"""Pipeline diário de expedição com particionamento por eixos e alocação multi-viagens.

Implementa a orquestração ponta a ponta de um dia de faturamento:
1. Ingestão e higienização (descarte auditado de balcão/cancelados em CleaningLog).
2. Detecção e priorização compulsória de pedidos urgentes (SLA).
3. Classificação territorial em eixos rodoviários (Eixo 0 Urbano a Eixo 5 Inhamuns).
4. Alocação sequencial de frota com geração automática de viagens posteriores
   (Viagem 1, Viagem 2, etc.) quando o volume/peso do eixo supera a capacidade do veículo.
5. Roteirização TSP e geração da sequência LIFO de doca para cada viagem.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional, Union
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
        """Executa o pipeline completo de faturamento diário com suporte a múltiplas viagens."""
        logger.info("Iniciando processamento do pipeline diário de faturamento...")

        # 1. Carregamento do DataFrame
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

        total_read = len(df)
        discarded_logs: List[Dict[str, Any]] = []
        valid_orders: List[Dict[str, Any]] = []

        # 2. Filtragem, Higienização e Tratamento dos Pedidos
        for _, row in df.iterrows():
            row_dict = {k.strip(): v for k, v in row.to_dict().items() if pd.notna(v)}

            # Avaliação de descarte com scope_regional=False para permitir Crateús urbano no Eixo 0
            is_eligible, logs = CleaningService.evaluate_order(row_dict, scope_regional=False)
            if not is_eligible:
                for log in logs:
                    if self.db:
                        self.db.add(log)
                    discarded_logs.append({
                        "pedido": log.record_reference,
                        "regra": log.rule_applied,
                        "motivo": log.reason
                    })
                continue

            raw_id = row_dict.get("Pedido", row_dict.get("ID", row_dict.get("PEDIDO", "")))
            clean_id = sanitize_order_id(raw_id)
            if clean_id == "INVALIDO":
                continue

            clean_date = sanitize_brazilian_date(row_dict.get("Data", row_dict.get("DATA", "")))
            clean_val = clean_currency(row_dict.get("Valor_Pedido", row_dict.get("VALOR DO PEDIDO", 0.0)))
            city_raw = str(row_dict.get("Cidade", row_dict.get("CIDADE", ""))).strip().upper()

            meta_axis = CITY_TO_AXIS_MAP.get(city_raw)
            if not meta_axis:
                discarded_logs.append({
                    "pedido": clean_id,
                    "regra": "cidade_nao_mapeada",
                    "motivo": f"Localidade '{city_raw}' não consta no mapeamento regional canônico."
                })
                continue

            axis_id = meta_axis["axis_id"]

            # Flag de urgência compulsória
            sit_entrega = str(row_dict.get("Situacao_CSV_Entrega", row_dict.get("Prioridade", ""))).strip().upper()
            is_urgent = (sit_entrega == "URGENTE") or str(row_dict.get("Urgente", "")).strip().lower() in ("true", "1", "sim")

            # Endereço
            raw_addr = row_dict.get("Endereco", row_dict.get("Endereço", row_dict.get("Logradouro", "")))
            parsed_addr = parse_address_components(raw_addr)

            # Itens e Cubagem
            itens_str = row_dict.get("Itens_Resumo", row_dict.get("ITENS", ""))
            parsed_items = parse_order_items(itens_str)
            cubing_res = self.cubagem.compute_order_cubing(parsed_items)

            # Pagamento na entrega
            pgt_entrega = str(row_dict.get("PGT ENTREGA?", row_dict.get("PAGAMENTO_ENTREGA", ""))).strip().upper()
            is_collect = "RECEBER" in pgt_entrega or "SIM" in pgt_entrega

            order_data = {
                "id": clean_id,
                "external_id": str(raw_id),
                "date": clean_date,
                "city_name": city_raw,
                "axis_id": axis_id,
                "total_value": clean_val,
                "value": clean_val,
                "total_weight_kg": cubing_res["total_weight_kg"],
                "total_volume_m3": cubing_res["total_volume_m3"],
                "weight_kg": cubing_res["total_weight_kg"],
                "volume_m3": cubing_res["total_volume_m3"],
                "has_long_items": cubing_res["has_long_items"],
                "is_mandatory": is_urgent,
                "address_line": parsed_addr["address_line"],
                "address_number": parsed_addr["address_number"],
                "neighborhood": parsed_addr["neighborhood"],
                "postal_code": parsed_addr["postal_code"],
                "payment_on_delivery": "A RECEBER" if is_collect else None,
                "sale_frequency": 1,
            }

            valid_orders.append(order_data)

        if self.db:
            self.db.commit()

        # 3. Desdobramento de pedidos que excedem a capacidade máxima do maior caminhão (4.800 kg)
        valid_orders = split_overweight_orders(valid_orders, max_capacity_kg=4800.0)

        # 4. Agrupamento de pedidos por Eixo Rodoviário
        orders_by_axis: Dict[str, List[Dict[str, Any]]] = {}
        for ord_item in valid_orders:
            ax = ord_item["axis_id"]
            orders_by_axis.setdefault(ax, []).append(ord_item)

        # 5. Obtenção da Frota Atual (2 Caminhões Grandes e 2 Caminhões Médios)
        available_vehicles = self._get_fleet_vehicles()
        large_trucks = [v for v in available_vehicles if not v["restricted_to_crateus"]]
        medium_trucks = [v for v in available_vehicles if v["restricted_to_crateus"]]

        all_trips: List[Dict[str, Any]] = []
        unallocated_orders: List[Dict[str, Any]] = []

        # 6. Alocação e Escalonamento de Viagens por Eixo (Multi-Trip)
        # Ordenamos os eixos: primeiro intermunicipais pesados, depois urbano
        for axis_id, axis_orders in sorted(orders_by_axis.items(), key=lambda x: (x[0] == "eixo-0-crateus-urbano", x[0])):
            pending_pool = list(axis_orders)
            trip_idx = 1

            while pending_pool:
                # Determina o veículo adequado para a viagem
                assigned_vehicle = self._select_vehicle_for_trip(
                    axis_id=axis_id,
                    pending_orders=pending_pool,
                    large_trucks=large_trucks,
                    medium_trucks=medium_trucks,
                    trip_number=trip_idx
                )

                # Separa IDs prioritários/urgentes na fila pendente
                urgent_ids = [o["id"] for o in pending_pool if o.get("is_mandatory")]

                # Se a soma dos pedidos urgentes exceder a capacidade do caminhão,
                # não passamos todos como mandatory de uma vez (para não tornar o CP-SAT inviável).
                # Em vez disso, passamos o subset que cabe por ordem de prioridade.
                mandatory_for_solver = self._select_feasible_mandatory(urgent_ids, pending_pool, assigned_vehicle)

                # Executa o solver CP-SAT para encontrar a melhor carga
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
                    # Nenhum pedido pôde ser alocado (ex: incompatibilidade dimensional ou física)
                    logger.warning(
                        f"Nenhum pedido alocado para o eixo {axis_id} na viagem {trip_idx}. "
                        f"Pedidos restantes: {len(pending_pool)}"
                    )
                    unallocated_orders.extend(pending_pool)
                    break

                # Recupera os pedidos selecionados
                allocated_orders = [o for o in pending_pool if o["id"] in selected_ids]

                # Roteirização TSP e Sequenciamento LIFO de Doca
                depot_lat, depot_lon = DEPOT_COORDINATES["lat"], DEPOT_COORDINATES["lon"]
                locations = [(depot_lat, depot_lon)]
                for o in allocated_orders:
                    coords = REGION_COORDINATES_CACHE.get(o["city_name"], (depot_lat, depot_lon))
                    locations.append(coords)

                tsp_res = solve_tsp(locations, depot_index=0, roundtrip=True)
                delivery_stops = tsp_res["delivery_order"]

                order_id_to_delivery_seq = {}
                for seq_idx, node_idx in enumerate(delivery_stops, start=1):
                    if 1 <= node_idx <= len(allocated_orders):
                        ord_id = allocated_orders[node_idx - 1]["id"]
                        order_id_to_delivery_seq[ord_id] = seq_idx

                total_allocated = len(allocated_orders)
                routed_items = []
                for o in allocated_orders:
                    deliv_seq = order_id_to_delivery_seq.get(o["id"], 1)
                    loading_seq = total_allocated - deliv_seq + 1
                    routed_items.append({
                        **o,
                        "delivery_order": deliv_seq,
                        "loading_order": loading_seq,
                    })

                # Ordena os itens pela sequência LIFO de doca (1º a carregar = fundo do baú)
                routed_items.sort(key=lambda x: x["loading_order"])

                # Validação independente de invariantes físicas e territoriais
                is_valid, validation_errors = IndependentValidator.validate_plan(
                    selected_orders=allocated_orders,
                    capacity_kg=assigned_vehicle["capacity_kg"],
                    capacity_m3=assigned_vehicle["useful_volume_m3"],
                    target_axis_id=axis_id,
                    allows_long_items=assigned_vehicle["allows_long_items"]
                )

                trip_title = f"Viagem {trip_idx}" if trip_idx > 1 else "Viagem 1 (Primeira Saída)"
                trip_record = {
                    "trip_id": f"{axis_id}-V{trip_idx}",
                    "trip_number": trip_idx,
                    "trip_title": trip_title,
                    "axis_id": axis_id,
                    "axis_name": CITY_TO_AXIS_MAP.get(allocated_orders[0]["city_name"], {}).get("axis_name", axis_id),
                    "vehicle_id": assigned_vehicle["id"],
                    "vehicle_name": assigned_vehicle["name"],
                    "vehicle_plate": assigned_vehicle["plate"],
                    "total_orders": len(allocated_orders),
                    "total_value": round(sum(o["total_value"] for o in allocated_orders), 2),
                    "total_weight_kg": round(sum(o["total_weight_kg"] for o in allocated_orders), 2),
                    "total_volume_m3": round(sum(o["total_volume_m3"] for o in allocated_orders), 3),
                    "weight_occupancy_pct": round((sum(o["total_weight_kg"] for o in allocated_orders) / assigned_vehicle["capacity_kg"]) * 100, 1),
                    "volume_occupancy_pct": round((sum(o["total_volume_m3"] for o in allocated_orders) / assigned_vehicle["useful_volume_m3"]) * 100, 1),
                    "limiting_resource": "VOLUME" if solve_res["volume_occupancy_pct"] >= solve_res["weight_occupancy_pct"] else "PESO",
                    "solver_status": solve_res["status"],
                    "solve_duration_ms": solve_res["solve_duration_ms"],
                    "estimated_tortuosity_distance_km": tsp_res.get("total_distance_km", 0.0),
                    "is_valid": is_valid,
                    "validation_errors": validation_errors,
                    "items": routed_items,
                    "decisions": solve_res.get("decisions", [])
                }

                all_trips.append(trip_record)

                # Remove pedidos alocados do pool pendente do eixo
                pending_pool = [o for o in pending_pool if o["id"] not in selected_ids]
                trip_idx += 1

        # 7. Resumo Consolidado do Dia de Faturamento
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
                        "operates_intermunicipal": v.operates_intermunicipal,
                    }
                    for v in db_v
                ]
        return DEFAULT_VEHICLES

    def _select_vehicle_for_trip(
        self,
        axis_id: str,
        pending_orders: List[Dict[str, Any]],
        large_trucks: List[Dict[str, Any]],
        medium_trucks: List[Dict[str, Any]],
        trip_number: int
    ) -> Dict[str, Any]:
        """Seleciona o caminhão mais adequado respeitando restrições territoriais e dimensionais."""
        has_6m = any(o.get("has_long_items", False) for o in pending_orders)

        # Se for o Eixo Urbano / Distrital de Crateús:
        if axis_id == "eixo-0-crateus-urbano":
            # Se não tiver peças de 6m e houver caminhão médio disponível, usa o médio (Bongo ou HR)
            if not has_6m and medium_trucks:
                # Alterna entre os dois caminhões médios conforme a viagem
                idx = (trip_number - 1) % len(medium_trucks)
                return medium_trucks[idx]
            # Se tiver peças de 6m ou carga muito pesada, usa o caminhão grande
            idx = (trip_number - 1) % len(large_trucks)
            return large_trucks[idx]

        # Eixos Intermunicipais (Eixos 1 a 5):
        # Exigem compulsoriamente os Caminhões Grandes (Mercedes Accelo 815)
        idx = (trip_number - 1) % len(large_trucks)
        return large_trucks[idx]

    def _select_feasible_mandatory(
        self,
        urgent_ids: List[str],
        orders: List[Dict[str, Any]],
        vehicle: Dict[str, Any]
    ) -> List[str]:
        """Garante que a lista de pedidos obrigatórios não exceda individualmente a capacidade do caminhão."""
        feasible_mandatory = []
        acc_w = 0.0
        acc_v = 0.0

        for oid in urgent_ids:
            ord_obj = next((o for o in orders if o["id"] == oid), None)
            if not ord_obj:
                continue
            w = ord_obj["total_weight_kg"]
            v = ord_obj["total_volume_m3"]
            if ord_obj.get("has_long_items") and not vehicle["allows_long_items"]:
                continue
            if (acc_w + w <= vehicle["capacity_kg"]) and (acc_v + v <= vehicle["useful_volume_m3"]):
                feasible_mandatory.append(oid)
                acc_w += w
                acc_v += v

        return feasible_mandatory
