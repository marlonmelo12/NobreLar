"""Módulo de pré-processamento de pedidos: fatiamento de carga (Order Splitting) e validação territorial.

Implementa:
- RF-003-B e ADR-0007: Desmembramento de pedidos com peso superior à capacidade útil do caminhão (ex: cimento > 4.800 kg)
- Validação de restrição territorial de veículos (Bongo/HR restritos a Crateús e distritos; caminhão maior para outras cidades)
"""

from typing import List, Dict, Any, Tuple
import structlog
from app.core.constants import SPLIT_TARGET_RATIO, CITY_TO_AXIS_MAP

logger = structlog.get_logger()


def split_overweight_orders(orders: List[Dict[str, Any]], max_capacity_kg: float = 4800.0) -> List[Dict[str, Any]]:
    """Desmembra pedidos cuja massa excede a capacidade útil do caminhão em subpedidos vinculados.

    Exemplo:
        Pedido de 5.387 kg de cimento -> P1 (4.080 kg) + P2 (1.307 kg) com is_split=True.
    """
    processed_orders = []
    target_p1_kg = max_capacity_kg * SPLIT_TARGET_RATIO

    for ord_dict in orders:
        peso = ord_dict.get("total_weight_kg", 0.0)

        # Se o pedido já cabe no veículo, segue inalterado
        if peso <= max_capacity_kg:
            processed_orders.append(ord_dict)
            continue

        # Pedido excede capacidade -> Fatiamento (Order Splitting)
        logger.info(
            f"Aplicando Order Splitting no pedido {ord_dict['id']} ({peso:.2f} kg > {max_capacity_kg:.2f} kg)"
        )
        ratio = target_p1_kg / peso if peso > 0 else 0.5

        # Subpedido P1
        p1 = dict(ord_dict)
        p1["id"] = f"{ord_dict['id']}-P1"
        p1["is_split"] = True
        p1["parent_order_id"] = ord_dict["id"]
        p1["total_weight_kg"] = round(peso * ratio, 2)
        p1["total_volume_m3"] = round(ord_dict.get("total_volume_m3", 0.0) * ratio, 4)
        p1["total_value"] = round(ord_dict.get("total_value", ord_dict.get("value", 0.0)) * ratio, 2)

        # Subpedido P2
        p2 = dict(ord_dict)
        p2["id"] = f"{ord_dict['id']}-P2"
        p2["is_split"] = True
        p2["parent_order_id"] = ord_dict["id"]
        p2["total_weight_kg"] = round(peso - p1["total_weight_kg"], 2)
        p2["total_volume_m3"] = round(ord_dict.get("total_volume_m3", 0.0) - p1["total_volume_m3"], 4)
        val_orig = ord_dict.get("total_value", ord_dict.get("value", 0.0))
        p2["total_value"] = round(val_orig - p1["total_value"], 2)

        processed_orders.extend([p1, p2])

    return processed_orders


def validate_vehicle_territorial_compatibility(vehicle_dict: Dict[str, Any], cities_in_load: List[str]) -> Tuple[bool, str]:
    """Valida se o veículo possui autorização operacional para trafegar nas localidades da carga.

    Regra de negócio:
    - Veículos médios com restricted_to_crateus = True (Kia Bongo e Hyundai HR)
      só podem atender Crateús e seus distritos.
    - Para destinos em outras cidades autônomas (intermunicipal), exige-se caminhão grande (Mercedes-Benz Accelo 815).
    """
    is_restricted = vehicle_dict.get("restricted_to_crateus", False)
    if not is_restricted:
        return True, "Veículo intermunicipal autorizado para todas as localidades."

    for city in cities_in_load:
        c_upper = city.strip().upper()
        meta = CITY_TO_AXIS_MAP.get(c_upper)
        if meta and meta.get("is_external", False):
            return False, (
                f"Violação territorial: o veículo '{vehicle_dict.get('name')}' é restrito a "
                f"Crateús e seus distritos, não podendo ser alocado para a cidade externa '{city}'."
            )

    return True, "Localidades compatíveis com a atuação do veículo urbano/distrital."
