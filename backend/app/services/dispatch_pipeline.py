"""Pipeline diário de expedição com particionamento por eixos e alocação multi-viagens.

Implementa a orquestração ponta a ponta de um dia de faturamento:
1. Ingestão desacoplada (JSON estruturado ou CSV tradicional).
2. Higienização e descarte auditado de balcão/cancelados em CleaningLog.
3. Cubagem técnica e extração detalhada de itens com detecção de 6m.
4. Detecção e priorização compulsória de pedidos urgentes (SLA).
5. Particionamento territorial em eixos rodoviários (Eixo 0 Urbano a Eixo 5 Inhamuns).
6. Alocação sequencial de frota com geração de viagens sucessivas (ondas) na carroceria aberta.
7. Roteirização TSP e sequenciamento físico na carroceria aberta com drill-down de itens.
"""

from pathlib import Path
import urllib.parse
from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
from sqlalchemy.orm import Session
import structlog

from app.core.config import settings
from app.core.constants import CITY_TO_AXIS_MAP
from app.core.seeds import DEFAULT_VEHICLES
from app.domain.models import Order, OrderItem, CleaningLog, Vehicle
from app.services.parsers import (
    sanitize_order_id,
    sanitize_brazilian_date,
    clean_currency,
    parse_order_items,
    parse_address_components
)
from app.services.cleaning import CleaningService
from app.services.cubagem_service import CubagemService
from app.core.geo_constants import DEPOT_COORDINATES, REGION_COORDINATES_CACHE
from app.services.distance_matrix import haversine_road_distance_km
from app.services.optimizer_cpsat import solve_load_allocation
from app.services.tsp_solver import solve_tsp
from app.services.pre_processor import split_overweight_orders
from app.services.validation import IndependentValidator

logger = structlog.get_logger()


class DailyDispatchPipeline:
    """Orquestrador do processamento de faturamento diário e expedição multi-viagens."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db
        self.cubagem = CubagemService()

    def process_daily_billing(
        self,
        csv_file_path_or_df: Union[str, Path, pd.DataFrame],
        profile_name: str = "Equilibrado",
        time_limit_seconds: float = 20.0
    ) -> Dict[str, Any]:
        """Executa o pipeline completo de faturamento diário a partir de CSV ou DataFrame."""
        if isinstance(csv_file_path_or_df, (str, Path)):
            p = Path(csv_file_path_or_df)
            if not p.exists():
                raise FileNotFoundError(f"Arquivo de faturamento diário não encontrado: {p}")
            try:
                df = pd.read_csv(p, sep=";", encoding="utf-8", dtype=str)
                if len(df.columns) <= 1:
                    df = pd.read_csv(p, sep=",", encoding="utf-8", dtype=str)
            except Exception:
                df = pd.read_csv(p, sep=";", encoding="latin1", dtype=str)
                if len(df.columns) <= 1:
                    df = pd.read_csv(p, sep=",", encoding="latin1", dtype=str)
        else:
            df = csv_file_path_or_df

        raw_orders: List[Dict[str, Any]] = []
        for _, row in df.iterrows():
            row_dict = {k.strip(): v for k, v in row.to_dict().items() if pd.notna(v)}
            raw_orders.append(row_dict)

        return self.process_orders_collection(raw_orders, profile_name, time_limit_seconds)

    def process_orders_json(
        self,
        orders: List[Dict[str, Any]],
        profile_name: str = "Equilibrado",
        time_limit_seconds: float = 20.0
    ) -> Dict[str, Any]:
        """Processa pedidos recebidos diretamente via JSON desacoplado e retorna ambas as visões com drill-down."""
        raw_result = self.process_orders_collection(orders, profile_name, time_limit_seconds)

        # Formata especificamente para os contratos desacoplados de saída
        cargas = self.format_truck_load_response(raw_result["trips"])
        roteiros = self.format_delivery_route_response(raw_result["trips"])
        pedidos_nao_alocados = self.format_unallocated_orders_response(raw_result.get("unallocated_orders", []))

        return {
            "status": raw_result["status"],
            "resumo": raw_result["summary"],
            "cargas_caminhao": cargas,
            "roteiros_entrega": roteiros,
            "descartes_limpeza": raw_result["discarded_cleaning_logs"],
            "pedidos_nao_alocados": pedidos_nao_alocados
        }

    def process_orders_collection(
        self,
        raw_orders: List[Dict[str, Any]],
        profile_name: str = "Equilibrado",
        time_limit_seconds: float = 20.0
    ) -> Dict[str, Any]:
        """Processa uma coleção de pedidos brutos com descarte, cubagem, multi-viagens e roteirização."""
        total_read = len(raw_orders)
        discarded_logs: List[Dict[str, Any]] = []
        valid_orders: List[Dict[str, Any]] = []

        for row_dict in raw_orders:
            eligible, order_data, disc_log = self._normalize_single_order(row_dict)
            if not eligible:
                if disc_log:
                    discarded_logs.append(disc_log)
                continue
            if order_data:
                valid_orders.append(order_data)

        if self.db:
            self.db.commit()

        # Desdobramento de pedidos que excedem a capacidade máxima do caminhão grande (4.800 kg)
        valid_orders = split_overweight_orders(valid_orders, max_capacity_kg=4800.0)

        # Agrupamento de pedidos por Eixo Rodoviário
        orders_by_axis: Dict[str, List[Dict[str, Any]]] = {}
        for ord_item in valid_orders:
            ax = ord_item["axis_id"]
            orders_by_axis.setdefault(ax, []).append(ord_item)

        fleet_vehicles = self._get_fleet_vehicles()
        all_trips: List[Dict[str, Any]] = []
        unallocated_orders: List[Dict[str, Any]] = []
        trip_idx = 1

        for axis_id, axis_orders in orders_by_axis.items():
            pending_pool = list(axis_orders)

            while pending_pool:
                assigned_vehicle = self._select_vehicle_for_trip(
                    axis_id=axis_id,
                    trip_idx=trip_idx,
                    fleet=fleet_vehicles,
                    pending_orders=pending_pool
                )

                if not assigned_vehicle:
                    logger.warning(f"Sem veículo compatível para o eixo {axis_id} na viagem {trip_idx}")
                    for o in pending_pool:
                        o["motivo_nao_alocacao"] = f"Sem veículo compatível disponível na frota para o eixo {axis_id}."
                    unallocated_orders.extend(pending_pool)
                    break

                urgent_ids = [o["id"] for o in pending_pool if o.get("is_mandatory")]
                mandatory_for_solver = self._select_feasible_mandatory(urgent_ids, pending_pool, assigned_vehicle)

                solve_res = solve_load_allocation(
                    orders=pending_pool,
                    capacity_kg=assigned_vehicle["capacity_kg"],
                    capacity_m3=assigned_vehicle["useful_volume_m3"],
                    allows_long_items=assigned_vehicle["allows_long_items"],
                    restricted_to_crateus=assigned_vehicle["restricted_to_crateus"],
                    mandatory_order_ids=mandatory_for_solver,
                    time_limit_sec=time_limit_seconds
                )

                selected_ids = solve_res["selected_order_ids"]
                if not selected_ids:
                    logger.warning(
                        f"Nenhum pedido alocado para o eixo {axis_id} na viagem {trip_idx}. "
                        f"Pedidos restantes: {len(pending_pool)}"
                    )
                    for o in pending_pool:
                        o["motivo_nao_alocacao"] = f"Capacidade volumétrica ou de peso do veículo {assigned_vehicle['name']} excedida."
                    unallocated_orders.extend(pending_pool)
                    break

                allocated_orders = [o for o in pending_pool if o["id"] in selected_ids]

                # Roteirização TSP
                depot_lat, depot_lon = DEPOT_COORDINATES["lat"], DEPOT_COORDINATES["lon"]
                locations = [(depot_lat, depot_lon)]
                for o in allocated_orders:
                    coords = (o.get("latitude", depot_lat), o.get("longitude", depot_lon))
                    locations.append(coords)

                tsp_res = solve_tsp(locations, depot_index=0, roundtrip=True)
                delivery_stops = tsp_res["delivery_order"]

                # Cálculo ponto a ponto da rota (trechos e acumulado)
                curr_loc = (depot_lat, depot_lon)
                accumulated_km = 0.0
                order_points_meta = {}

                for seq_idx, node_idx in enumerate(delivery_stops, start=1):
                    if 1 <= node_idx <= len(allocated_orders):
                        ord_obj = allocated_orders[node_idx - 1]
                        order_loc = locations[node_idx]
                        leg_km = haversine_road_distance_km(curr_loc, order_loc)
                        accumulated_km += leg_km
                        curr_loc = order_loc
                        order_addr = ord_obj.get("formatted_address") or ord_obj.get("address_line") or f"{ord_obj['city_name']}, CE"
                        order_points_meta[ord_obj["id"]] = {
                            "ponto_numero": seq_idx,
                            "delivery_order": seq_idx,
                            "distancia_trecho_km": leg_km,
                            "distancia_acumulada_km": round(accumulated_km, 2),
                            "latitude": order_loc[0],
                            "longitude": order_loc[1],
                            "coordenadas": {"lat": order_loc[0], "lon": order_loc[1]},
                            "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(str(order_addr))}"
                        }

                return_leg_km = haversine_road_distance_km(curr_loc, (depot_lat, depot_lon))
                total_route_km = round(accumulated_km + return_leg_km, 2)
                if total_route_km == 0.0 and tsp_res.get("total_distance_km", 0.0) > 0.0:
                    total_route_km = tsp_res.get("total_distance_km", 0.0)

                depot_addr_enc = urllib.parse.quote(DEPOT_COORDINATES["address"])
                ponto_origem = {
                    "ponto_numero": 0,
                    "tipo_ponto": "ORIGEM",
                    "nome": DEPOT_COORDINATES["name"],
                    "cidade": DEPOT_COORDINATES["city"],
                    "endereco": DEPOT_COORDINATES["address"],
                    "latitude": depot_lat,
                    "longitude": depot_lon,
                    "coordenadas": {"lat": depot_lat, "lon": depot_lon},
                    "distancia_trecho_km": 0.0,
                    "distancia_acumulada_km": 0.0,
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={depot_addr_enc}",
                    "acao": "Carregamento e conferência na doca de expedição"
                }

                ponto_retorno = {
                    "ponto_numero": len(delivery_stops) + 1,
                    "tipo_ponto": "RETORNO",
                    "nome": DEPOT_COORDINATES["name"],
                    "cidade": DEPOT_COORDINATES["city"],
                    "endereco": DEPOT_COORDINATES["address"],
                    "latitude": depot_lat,
                    "longitude": depot_lon,
                    "coordenadas": {"lat": depot_lat, "lon": depot_lon},
                    "distancia_trecho_km": return_leg_km,
                    "distancia_acumulada_km": total_route_km,
                    "google_maps_url": f"https://www.google.com/maps/search/?api=1&query={depot_addr_enc}",
                    "acao": "Retorno ao CD Matriz Crateús"
                }

                total_allocated = len(allocated_orders)
                routed_items = []
                for o in allocated_orders:
                    meta = order_points_meta.get(o["id"], {})
                    deliv_seq = meta.get("delivery_order", 1)
                    loading_seq = total_allocated - deliv_seq + 1

                    routed_items.append({
                        **o,
                        "delivery_order": deliv_seq,
                        "loading_order": loading_seq,
                        "ponto_numero": deliv_seq,
                        "latitude": meta.get("latitude", o.get("latitude", depot_lat)),
                        "longitude": meta.get("longitude", o.get("longitude", depot_lon)),
                        "coordenadas": meta.get("coordenadas", o.get("coordenadas", {"lat": depot_lat, "lon": depot_lon})),
                        "distancia_trecho_km": meta.get("distancia_trecho_km", 0.0),
                        "distancia_acumulada_km": meta.get("distancia_acumulada_km", 0.0),
                        "google_maps_url": meta.get("google_maps_url"),
                        "posicao_carroceria": None,
                        "posicao_na_carroceria": None,
                    })

                # Ordena pela sequência física de carregamento
                routed_items.sort(key=lambda x: x["loading_order"])

                # Validação independente de integridade física e territorial
                is_valid, validation_errors = IndependentValidator.validate_plan(
                    selected_orders=allocated_orders,
                    capacity_kg=assigned_vehicle["capacity_kg"],
                    capacity_m3=assigned_vehicle["useful_volume_m3"],
                    target_axis_id=axis_id,
                    allows_long_items=assigned_vehicle["allows_long_items"]
                )

                trip_title = f"Viagem {trip_idx}"
                trip_record = {
                    "trip_id": f"{axis_id}-V{trip_idx}",
                    "trip_number": trip_idx,
                    "trip_title": trip_title,
                    "axis_id": axis_id,
                    "axis_name": CITY_TO_AXIS_MAP.get(allocated_orders[0]["city_name"], {}).get("axis_name", axis_id),
                    "vehicle_id": assigned_vehicle["id"],
                    "vehicle_name": assigned_vehicle["name"],
                    "vehicle_plate": assigned_vehicle["plate"],
                    "vehicle_capacity_kg": assigned_vehicle["capacity_kg"],
                    "vehicle_useful_volume_m3": assigned_vehicle["useful_volume_m3"],
                    "vehicle_allows_long_items": assigned_vehicle["allows_long_items"],
                    "vehicle_type": "Caminhão",
                    "total_orders": len(allocated_orders),
                    "total_value": round(sum(o["total_value"] for o in allocated_orders), 2),
                    "total_weight_kg": round(sum(o["total_weight_kg"] for o in allocated_orders), 2),
                    "total_volume_m3": round(sum(o["total_volume_m3"] for o in allocated_orders), 3),
                    "weight_occupancy_pct": round((sum(o["total_weight_kg"] for o in allocated_orders) / assigned_vehicle["capacity_kg"]) * 100, 1),
                    "volume_occupancy_pct": round((sum(o["total_volume_m3"] for o in allocated_orders) / assigned_vehicle["useful_volume_m3"]) * 100, 1),
                    "limiting_resource": "VOLUME" if solve_res["volume_occupancy_pct"] >= solve_res["weight_occupancy_pct"] else "PESO",
                    "solver_status": solve_res["status"],
                    "solve_duration_ms": solve_res["solve_duration_ms"],
                    "estimated_tortuosity_distance_km": total_route_km,
                    "ponto_origem": ponto_origem,
                    "ponto_retorno": ponto_retorno,
                    "is_valid": is_valid,
                    "validation_errors": validation_errors,
                    "items": routed_items,
                    "decisions": solve_res.get("decisions", [])
                }

                all_trips.append(trip_record)
                pending_pool = [o for o in pending_pool if o["id"] not in selected_ids]
                trip_idx += 1

        total_invoiced_value = sum(t["total_value"] for t in all_trips)
        total_allocated_weight = sum(t["total_weight_kg"] for t in all_trips)
        total_allocated_volume = sum(t["total_volume_m3"] for t in all_trips)
        total_allocated_orders = sum(t["total_orders"] for t in all_trips)

        return {
            "status": "SUCESSO",
            "summary": {
                "total_records_read": total_read,
                "total_discarded_cleaning": len(discarded_logs),
                "total_valid_deliveries": len(valid_orders),
                "total_allocated_orders": total_allocated_orders,
                "total_unallocated_orders": len(unallocated_orders),
                "total_trips_generated": len(all_trips),
                "total_invoiced_value": round(total_invoiced_value, 2),
                "total_allocated_weight_kg": round(total_allocated_weight, 2),
                "total_allocated_volume_m3": round(total_allocated_volume, 3),
            },
            "discarded_cleaning_logs": discarded_logs,
            "trips": all_trips,
            "unallocated_orders": unallocated_orders
        }

    def _normalize_single_order(
        self,
        row_dict: Dict[str, Any]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
        """Higieniza, extrai cubagem e normaliza um único pedido."""
        raw_id = row_dict.get("id") or row_dict.get("pedido") or row_dict.get("numero_pedido") or row_dict.get("Pedido") or row_dict.get("ID") or "SEM_ID"
        clean_id = sanitize_order_id(raw_id)
        if clean_id == "INVALIDO":
            return False, None, None

        # 1. Situação operacional do pedido (Enum canônico do CSV: NORMAL, URGENTE, RETIRADA, CARRO HORARIO, PROGRAMADO, TOPIQUE, CANCELADO)
        sit_cadastral = str(row_dict.get("Situacao", "")).strip().upper()
        logistica = str(row_dict.get("logistica") or row_dict.get("Logistica") or "").strip().upper()
        raw_sit = str(
            row_dict.get("situacao")
            or row_dict.get("SITUACAO")
            or (sit_cadastral if sit_cadastral in ("CANCELADO", "RETIRADA", "URGENTE") else None)
            or row_dict.get("Situacao_CSV_Entrega")
            or sit_cadastral
            or "NORMAL"
        ).strip().upper()

        if raw_sit == "CANCELADO" or sit_cadastral == "CANCELADO" or logistica == "CANCELADO":
            return False, None, {
                "pedido": str(raw_id),
                "regra": "pedido_cancelado",
                "motivo": "Pedido cancelado expurgado do planejamento logístico."
            }

        if raw_sit == "RETIRADA":
            return False, None, {
                "pedido": str(raw_id),
                "regra": "retirada_balcao",
                "motivo": "Pedido com retirada direta no balcão da loja não compõe carga de transporte rodoviário."
            }

        city_raw = str(row_dict.get("cidade") or row_dict.get("city") or row_dict.get("Cidade") or "").strip().upper()
        meta_axis = CITY_TO_AXIS_MAP.get(city_raw)
        if not meta_axis:
            return False, None, {
                "pedido": str(raw_id),
                "regra": "cidade_nao_mapeada",
                "motivo": f"Localidade '{city_raw}' não consta no mapeamento regional canônico de Crateús."
            }

        axis_id = meta_axis["axis_id"]
        clean_date = sanitize_brazilian_date(str(row_dict.get("data") or row_dict.get("data_emissao") or row_dict.get("Data") or ""))
        clean_val = clean_currency(row_dict.get("valor") or row_dict.get("total_pedido") or row_dict.get("Valor_Pedido") or 0.0)

        # Flag de urgência
        urgente_field = row_dict.get("urgente", row_dict.get("is_urgent"))
        is_urgent = False
        if isinstance(urgente_field, bool):
            is_urgent = urgente_field
        elif urgente_field:
            is_urgent = str(urgente_field).strip().lower() in ("true", "1", "sim", "urgente")
        if not is_urgent and raw_sit == "URGENTE":
            is_urgent = True

        # Endereço
        raw_addr = row_dict.get("endereco") or row_dict.get("address") or row_dict.get("Endereco") or ""
        parsed_addr = parse_address_components(raw_addr)

        # Pagamento na entrega
        pgt = str(row_dict.get("pagamento_entrega") or row_dict.get("pagamento_na_entrega") or row_dict.get("PGT ENTREGA?") or "").strip().upper()
        is_collect = "RECEBER" in pgt or "SIM" in pgt

        # Cliente e Vendedor
        customer = row_dict.get("cliente") or row_dict.get("Cliente")
        seller = row_dict.get("vendedor") or row_dict.get("Vendedor")

        # Coordenadas geográficas (caso venham explícitas no JSON ou fallback do cache regional)
        lat_input = row_dict.get("latitude") if row_dict.get("latitude") is not None else row_dict.get("lat")
        lon_input = row_dict.get("longitude") if row_dict.get("longitude") is not None else (row_dict.get("lon") or row_dict.get("lng"))
        custom_coords = None
        if lat_input is not None and lon_input is not None:
            try:
                custom_coords = (float(lat_input), float(lon_input))
            except (ValueError, TypeError):
                custom_coords = None

        fallback_coords = REGION_COORDINATES_CACHE.get(city_raw, (DEPOT_COORDINATES["lat"], DEPOT_COORDINATES["lon"]))
        final_coords = custom_coords or fallback_coords

        # 2. Processamento dos Itens e Cubagem Técnica
        raw_items = row_dict.get("itens") or row_dict.get("items") or row_dict.get("Itens_Resumo") or ""
        items_computed: List[Dict[str, Any]] = []

        if isinstance(raw_items, list):
            for it in raw_items:
                if isinstance(it, dict):
                    code = str(it.get("codigo") or it.get("product_code") or "00000").strip()
                    desc = str(it.get("descricao") or it.get("product_desc") or "").strip()
                    if not desc and it.get("produto"):
                        p_str = str(it.get("produto"))
                        parts = p_str.split(" - ", 1)
                        if len(parts) == 2:
                            code, desc = parts[0].strip(), parts[1].strip()
                        else:
                            desc = p_str
                    qtd = float(it.get("quantidade", it.get("quantity", 1.0)))
                    unit = str(it.get("unidade", it.get("unit", "UN"))).strip().upper()
                    price = float(it.get("preco_unitario", it.get("unit_price", 0.0)))
                    c_res = self.cubagem.compute_item_cubing(code, desc, qtd, unit)
                    final_qtd = c_res.get("effective_quantity", qtd)
                    final_unit = c_res.get("effective_unit", unit)
                    items_computed.append({
                        "codigo": code,
                        "descricao": desc or f"PRODUTO {code}",
                        "quantidade": final_qtd,
                        "unidade": final_unit,
                        "preco_unitario": price,
                        "peso_unitario_kg": c_res["unit_weight_kg"],
                        "peso_total_kg": c_res["computed_weight_kg"],
                        "volume_total_m3": c_res["computed_volume_m3"],
                        "e_item_6m": False,
                        "cubagem_estimada": c_res["is_estimated"]
                    })
        elif isinstance(raw_items, str) and raw_items.strip():
            parsed = parse_order_items(raw_items)
            for p in parsed:
                c_res = self.cubagem.compute_item_cubing(p["product_code"], p["product_desc"], p["quantity"], p["unit"])
                final_qtd = c_res.get("effective_quantity", p["quantity"])
                final_unit = c_res.get("effective_unit", p["unit"])
                items_computed.append({
                    "codigo": p["product_code"],
                    "descricao": p["product_desc"],
                    "quantidade": final_qtd,
                    "unidade": final_unit,
                    "preco_unitario": 0.0,
                    "peso_unitario_kg": c_res["unit_weight_kg"],
                    "peso_total_kg": c_res["computed_weight_kg"],
                    "volume_total_m3": c_res["computed_volume_m3"],
                    "e_item_6m": False,
                    "cubagem_estimada": c_res["is_estimated"]
                })

        total_w = sum(it["peso_total_kg"] for it in items_computed)
        total_v = sum(it["volume_total_m3"] for it in items_computed)
        has_long = False

        order_data = {
            "id": clean_id,
            "external_id": str(raw_id),
            "date": clean_date,
            "customer": str(customer) if customer else None,
            "seller": str(seller) if seller else None,
            "city_name": city_raw,
            "axis_id": axis_id,
            "situacao": raw_sit,
            "total_value": clean_val,
            "value": clean_val,
            "total_weight_kg": round(total_w, 2),
            "total_volume_m3": round(total_v, 4),
            "weight_kg": round(total_w, 2),
            "volume_m3": round(total_v, 4),
            "has_long_items": has_long,
            "is_mandatory": is_urgent,
            "address_line": parsed_addr.get("address_line", raw_addr),
            "address_number": parsed_addr.get("address_number"),
            "neighborhood": parsed_addr.get("neighborhood"),
            "postal_code": parsed_addr.get("postal_code"),
            "formatted_address": raw_addr,
            "payment_on_delivery": "A RECEBER" if is_collect else None,
            "sale_frequency": 1,
            "latitude": final_coords[0],
            "longitude": final_coords[1],
            "coordenadas": {"lat": final_coords[0], "lon": final_coords[1]},
            "items": items_computed,  # DRILL-DOWN PRESERVADO!
        }

        return True, order_data, None

    def format_truck_load_response(self, trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formata viagens para a visão de Carregamento na Carroceria Aberta com drill-down."""
        formatted: List[Dict[str, Any]] = []
        for t in trips:
            alerta = None

            pedidos_carroceria = []
            for it in t.get("items", []):
                pedidos_carroceria.append({
                    "pedido": it["id"],
                    "external_id": it.get("external_id", it["id"]),
                    "ordem_carregamento": it.get("loading_order", 1),
                    "posicao_carroceria": None,
                    "ordem_entrega_prevista": it.get("delivery_order", 1),
                    "cliente": it.get("customer"),
                    "cidade": it.get("city_name"),
                    "endereco": it.get("address_line") or it.get("formatted_address"),
                    "situacao": it.get("situacao", "NORMAL"),
                    "peso_total_kg": it.get("total_weight_kg", it.get("weight_kg", 0.0)),
                    "volume_total_m3": it.get("total_volume_m3", it.get("volume_m3", 0.0)),
                    "valor_total": it.get("total_value", it.get("value", 0.0)),
                    "urgente": it.get("is_mandatory", False),
                    "possui_itens_6m": False,
                    "pagamento_na_entrega": it.get("payment_on_delivery"),
                    "itens": it.get("items", [])  # DRILL-DOWN ANINHADO
                })

            formatted.append({
                "viagem_id": t["trip_id"],
                "viagem_numero": t["trip_number"],
                "titulo": t["trip_title"],
                "eixo_id": t["axis_id"],
                "eixo_nome": t["axis_name"],
                "veiculo": {
                    "id": t["vehicle_id"],
                    "nome": t["vehicle_name"],
                    "placa": t["vehicle_plate"],
                    "tipo_carroceria": "Caminhão",
                    "capacidade_kg": t.get("vehicle_capacity_kg", 4800.0),
                    "volume_util_m3": t.get("vehicle_useful_volume_m3", 18.5),
                    "permite_barras_6m": t.get("vehicle_allows_long_items", True),
                },
                "total_pedidos": t["total_orders"],
                "peso_total_kg": t["total_weight_kg"],
                "volume_total_m3": t["total_volume_m3"],
                "faturamento_total": t["total_value"],
                "ocupacao_peso_pct": t["weight_occupancy_pct"],
                "ocupacao_volume_pct": t["volume_occupancy_pct"],
                "recurso_limitante": t["limiting_resource"],
                "alerta_carroceria": alerta,
                "pedidos_carroceria": pedidos_carroceria
            })
        return formatted

    def format_delivery_route_response(self, trips: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formata viagens para a visão de Ordem de Entrega (Roteiro TSP) com drill-down."""
        formatted: List[Dict[str, Any]] = []
        for t in trips:
            # Ordena por delivery_order crescente (1ª parada, 2ª parada...)
            items_by_deliv = sorted(t.get("items", []), key=lambda x: x.get("delivery_order", 1))

            paradas = []
            total_receber = 0.0
            for it in items_by_deliv:
                val = it.get("total_value", it.get("value", 0.0))
                is_collect = it.get("payment_on_delivery") == "A RECEBER"
                if is_collect:
                    total_receber += val

                paradas.append({
                    "ponto_numero": it.get("ponto_numero", it.get("delivery_order", 1)),
                    "parada": it.get("delivery_order", 1),
                    "tipo_ponto": "ENTREGA",
                    "pedido": it["id"],
                    "external_id": it.get("external_id", it["id"]),
                    "cliente": it.get("customer"),
                    "cidade": it.get("city_name"),
                    "endereco_completo": it.get("formatted_address") or it.get("address_line") or it.get("city_name"),
                    "latitude": it.get("latitude", 0.0),
                    "longitude": it.get("longitude", 0.0),
                    "coordenadas": it.get("coordenadas", {"lat": it.get("latitude", 0.0), "lon": it.get("longitude", 0.0)}),
                    "distancia_trecho_km": it.get("distancia_trecho_km", 0.0),
                    "distancia_acumulada_km": it.get("distancia_acumulada_km", 0.0),
                    "google_maps_url": it.get("google_maps_url") or f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(str(it.get('formatted_address') or it.get('address_line') or it.get('city_name') or 'Crateús - CE'))}",
                    "posicao_na_carroceria": None,
                    "situacao": it.get("situacao", "NORMAL"),
                    "valor_pedido": val,
                    "status_pagamento": "A RECEBER" if is_collect else "QUITADO",
                    "valor_a_receber": val if is_collect else 0.0,
                    "alerta_cobranca": f"ATENÇÃO: RECEBER R$ {val:.2f} NA ENTREGA (PAGAMENTO PENDENTE)" if is_collect else None,
                    "peso_total_kg": it.get("total_weight_kg", it.get("weight_kg", 0.0)),
                    "volume_total_m3": it.get("total_volume_m3", it.get("volume_m3", 0.0)),
                    "possui_itens_6m": False,
                    "itens": it.get("items", [])  # DRILL-DOWN ANINHADO
                })

            p_origem = t.get("ponto_origem")
            p_retorno = t.get("ponto_retorno")
            pontos_completos = ([p_origem] if p_origem else []) + paradas + ([p_retorno] if p_retorno else [])
            
            itinerario_str = "CD Crateús"
            if paradas:
                itinerario_str += " ➔ " + " ➔ ".join(f"Ponto {p['parada']}: {p.get('cliente') or 'Cliente'} ({p['cidade']})" for p in paradas)
            itinerario_str += " ➔ Retorno CD Crateús"

            formatted.append({
                "viagem_id": t["trip_id"],
                "viagem_numero": t["trip_number"],
                "titulo": t["trip_title"],
                "eixo_id": t["axis_id"],
                "eixo_nome": t["axis_name"],
                "veiculo": {
                    "id": t["vehicle_id"],
                    "nome": t["vehicle_name"],
                    "placa": t["vehicle_plate"],
                    "tipo": "Caminhão",
                },
                "total_paradas": t["total_orders"],
                "faturamento_total": t["total_value"],
                "total_a_receber_rota": round(total_receber, 2),
                "distancia_estimada_km": t.get("estimated_tortuosity_distance_km", 0.0),
                "ponto_origem": p_origem,
                "ponto_retorno": p_retorno,
                "pontos_rota": pontos_completos,
                "itinerario_resumido": itinerario_str,
                "paradas": paradas
            })
        return formatted

    def format_unallocated_orders_response(self, unallocated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Formata pedidos não alocados com motivo operacional e drill-down de itens."""
        formatted: List[Dict[str, Any]] = []
        for it in unallocated:
            formatted.append({
                "pedido": str(it.get("id")),
                "external_id": str(it.get("external_id", it.get("id"))),
                "cliente": it.get("customer"),
                "cidade": it.get("city_name") or "NÃO INFORMADA",
                "eixo_id": it.get("axis_id"),
                "endereco": it.get("formatted_address") or it.get("address_line") or it.get("city_name"),
                "situacao": it.get("situacao", "NORMAL"),
                "peso_total_kg": round(float(it.get("total_weight_kg", it.get("weight_kg", 0.0))), 2),
                "volume_total_m3": round(float(it.get("total_volume_m3", it.get("volume_m3", 0.0))), 4),
                "valor_total": round(float(it.get("total_value", it.get("value", 0.0))), 2),
                "urgente": bool(it.get("is_mandatory", False)),
                "motivo": str(it.get("motivo_nao_alocacao", "Capacidade ou disponibilidade de frota excedida")),
                "itens": it.get("items", [])
            })
        return formatted

    def _get_fleet_vehicles(self) -> List[Dict[str, Any]]:
        """Recupera a frota oficial cadastrada no banco ou a semente oficial."""
        if self.db:
            db_v = self.db.query(Vehicle).filter(Vehicle.active == True).all()
            if db_v:
                return [
                    {
                        "id": v.id,
                        "name": v.name,
                        "plate": v.plate,
                        "capacity_kg": v.capacity_kg,
                        "useful_volume_m3": v.useful_volume_m3,
                        "useful_length_m": v.useful_length_m,
                        "allows_long_items": v.allows_long_items,
                        "restricted_to_crateus": v.restricted_to_crateus,
                    }
                    for v in db_v
                ]

        return [
            {
                "id": v["id"],
                "name": v["name"],
                "plate": v["plate"],
                "capacity_kg": v["capacity_kg"],
                "useful_volume_m3": v["useful_volume_m3"],
                "useful_length_m": v["useful_length_m"],
                "allows_long_items": v["allows_long_items"],
                "restricted_to_crateus": v.get("restricted_to_crateus", False),
            }
            for v in DEFAULT_VEHICLES
            if v.get("active", True)
        ]

    def _select_vehicle_for_trip(
        self,
        axis_id: str,
        trip_idx: int,
        fleet: List[Dict[str, Any]],
        pending_orders: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Seleciona o caminhão mais adequado para a viagem considerando território."""
        is_crateus_urban = (axis_id == "eixo-0-crateus-urbano")

        if is_crateus_urban:
            medium_trucks = [v for v in fleet if v.get("restricted_to_crateus", False)]
            if medium_trucks:
                return medium_trucks[(trip_idx - 1) % len(medium_trucks)]

        large_trucks = [v for v in fleet if not v.get("restricted_to_crateus", False)]
        if large_trucks:
            return large_trucks[(trip_idx - 1) % len(large_trucks)]

        return fleet[0] if fleet else None

    def _select_feasible_mandatory(
        self,
        urgent_ids: List[str],
        orders: List[Dict[str, Any]],
        vehicle: Dict[str, Any]
    ) -> List[str]:
        """Seleciona subconjunto viável de pedidos obrigatórios que cabem fisicamente no veículo."""
        if not urgent_ids:
            return []

        orders_map = {o["id"]: o for o in orders}
        accum_w = 0.0
        accum_v = 0.0
        feasible_ids = []

        urgent_sorted = sorted(
            urgent_ids,
            key=lambda oid: orders_map.get(oid, {}).get("total_value", 0.0),
            reverse=True
        )

        for oid in urgent_sorted:
            ord_obj = orders_map.get(oid)
            if not ord_obj:
                continue

            w = ord_obj.get("total_weight_kg", 0.0)
            v = ord_obj.get("total_volume_m3", 0.0)

            if accum_w + w <= vehicle["capacity_kg"] and accum_v + v <= vehicle["useful_volume_m3"]:
                accum_w += w
                accum_v += v
                feasible_ids.append(oid)

        return feasible_ids
