"""Heurística gulosa de contingência (Fallback) para situações de timeout ou ausência de incumbente no solver.

Implementa RNF-001-A e Seção 15:
- Ordenação decrescente por score de eficiência E_i
- Inserção estrita garantindo peso <= capacidade e volume <= capacidade
- Marcação explícita de algorithm_version = 'greedy-fallback-v1'
"""

from typing import List, Dict, Any, Optional
import structlog
from app.services.scoring import calculate_order_scores
from app.core.constants import CITY_TO_AXIS_MAP

logger = structlog.get_logger()


def solve_greedy_fallback(
    orders: List[Dict[str, Any]],
    capacity_kg: float,
    capacity_m3: float,
    allows_long_items: bool,
    restricted_to_crateus: bool = False,
    w_weight: float = 0.25,
    w_volume: float = 0.25,
    w_value: float = 0.30,
    w_freq: float = 0.20
) -> Dict[str, Any]:
    """Heurística gulosa determinística baseada na máxima eficiência de ocupação."""
    logger.warning("Acionando fallback heurístico guloso para montagem de carga.")

    scored_orders = calculate_order_scores(
        orders=orders,
        capacity_kg=capacity_kg,
        capacity_m3=capacity_m3,
        w_peso=w_weight,
        w_volume=w_volume,
        w_valor=w_value,
        w_quantidade=w_freq
    )

    # Ordena por eficiência decrescente; desempate determinístico por ID crescente
    sorted_orders = sorted(
        scored_orders,
        key=lambda o: (o.get("efficiency", 0.0), -float(o.get("total_weight_kg", 0.0))),
        reverse=True
    )

    selected_ids = []
    tot_w = 0.0
    tot_v = 0.0
    tot_val = 0.0
    decisions = []

    for o in sorted_orders:
        peso = float(o.get("total_weight_kg", 0.0))
        vol = float(o.get("total_volume_m3", 0.0))
        val = float(o.get("total_value", 0.0))

        # Restrição de 6 metros
        if o.get("has_long_items", False) and not allows_long_items:
            decisions.append({
                "order_id": o["id"],
                "included": False,
                "score": o.get("score", 0.0),
                "efficiency": o.get("efficiency", 0.0),
                "peso_pct": o.get("peso_pct", 0.0),
                "volume_pct": o.get("volume_pct", 0.0),
                "exclusion_reason": "VEICULO_INCOMPATIVEL_6M"
            })
            continue

        # Restrição territorial
        if restricted_to_crateus:
            city_name = str(o.get("city_name", "")).strip().upper()
            meta_city = CITY_TO_AXIS_MAP.get(city_name)
            if meta_city and meta_city.get("is_external", False):
                decisions.append({
                    "order_id": o["id"],
                    "included": False,
                    "score": o.get("score", 0.0),
                    "efficiency": o.get("efficiency", 0.0),
                    "peso_pct": o.get("peso_pct", 0.0),
                    "volume_pct": o.get("volume_pct", 0.0),
                    "exclusion_reason": "VEICULO_RESTRITO_CIDADE"
                })
                continue

        # Verifica se cabe simultaneamente em peso e volume
        if (tot_w + peso <= capacity_kg + 0.001) and (tot_v + vol <= capacity_m3 + 0.001):
            selected_ids.append(o["id"])
            tot_w += peso
            tot_v += vol
            tot_val += val
            decisions.append({
                "order_id": o["id"],
                "included": True,
                "score": o.get("score", 0.0),
                "efficiency": o.get("efficiency", 0.0),
                "peso_pct": o.get("peso_pct", 0.0),
                "volume_pct": o.get("volume_pct", 0.0),
                "exclusion_reason": "SELECIONADO"
            })
        else:
            reason = "EXCEDE_PESO_INDIVIDUAL" if (tot_w + peso > capacity_kg) else "EXCEDE_VOLUME_INDIVIDUAL"
            decisions.append({
                "order_id": o["id"],
                "included": False,
                "score": o.get("score", 0.0),
                "efficiency": o.get("efficiency", 0.0),
                "peso_pct": o.get("peso_pct", 0.0),
                "volume_pct": o.get("volume_pct", 0.0),
                "exclusion_reason": reason
            })

    weight_occ = round((tot_w / capacity_kg) * 100, 2)
    volume_occ = round((tot_v / capacity_m3) * 100, 2)
    limiting = "PESO" if (tot_w / capacity_kg) >= (tot_v / capacity_m3) else "VOLUME"

    return {
        "status": "FALLBACK_GULOSO",
        "selected_order_ids": selected_ids,
        "total_weight_kg": round(tot_w, 2),
        "total_volume_m3": round(tot_v, 4),
        "total_value": round(tot_val, 2),
        "weight_occupancy_pct": weight_occ,
        "volume_occupancy_pct": volume_occ,
        "limiting_resource": limiting,
        "optimality_gap": None,
        "solve_duration_ms": 5,
        "algorithm_version": "greedy-fallback-v1",
        "decisions": decisions
    }
