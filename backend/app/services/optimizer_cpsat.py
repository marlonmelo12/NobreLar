"""Motor de otimização combinatória com Google OR-Tools CP-SAT.

Implementa a resolução exata do problema da mochila multidimensional 0-1 (MKP),
com escalonamento para inteiros, restrições físicas invioláveis de peso e volume,
restrição linear dimensional para peças de 6m, restrição territorial de frota
e registro explicável de decisão para 100% dos pedidos.
"""

import time
import math
from typing import List, Dict, Any, Optional
import structlog
from ortools.sat.python import cp_model

from app.core.constants import (
    SCALE_WEIGHT,
    SCALE_VOLUME,
    SCALE_SCORE,
    CITY_TO_AXIS_MAP,
)
from app.services.scoring import calculate_order_scores

logger = structlog.get_logger()


def solve_load_allocation(
    orders: List[Dict[str, Any]],
    capacity_kg: float,
    capacity_m3: float,
    allows_long_items: bool,
    restricted_to_crateus: bool = False,
    w_weight: float = 0.25,
    w_volume: float = 0.25,
    w_value: float = 0.30,
    w_freq: float = 0.20,
    objective_mode: str = "score_agregado",
    time_limit_sec: float = 30.0,
    random_seed: int = 42,
    mandatory_order_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Resolve a alocação ótima de pedidos na carga via CP-SAT.

    Garante cumprimento dos limites físicos sem violação sob qualquer circunstância.
    """
    start_time = time.perf_counter()
    mandatory_set = set(mandatory_order_ids or [])

    n = len(orders)
    if n == 0:
        return {
            "status": "SEM_PEDIDOS",
            "selected_order_ids": [],
            "total_weight_kg": 0.0,
            "total_volume_m3": 0.0,
            "total_value": 0.0,
            "weight_occupancy_pct": 0.0,
            "volume_occupancy_pct": 0.0,
            "limiting_resource": "PESO",
            "optimality_gap": 0.0,
            "solve_duration_ms": 0,
            "algorithm_version": "cpsat-v3.0",
            "decisions": []
        }

    # 1. Cálculo prévio dos scores multicritério e eficiência
    scored_orders = calculate_order_scores(
        orders=orders,
        capacity_kg=capacity_kg,
        capacity_m3=capacity_m3,
        w_peso=w_weight,
        w_volume=w_volume,
        w_valor=w_value,
        w_quantidade=w_freq
    )

    # 2. Inicialização do Modelo CP-SAT
    model = cp_model.CpModel()

    cap_w_int = round(capacity_kg * SCALE_WEIGHT)
    cap_v_int = round(capacity_m3 * SCALE_VOLUME)

    x = [model.NewBoolVar(f"x_{scored_orders[i]['id']}") for i in range(n)]

    w_ints = []
    v_ints = []
    obj_ints = []

    # Mapeamento inicial de motivos de exclusão a priori
    pre_excluded_reasons: Dict[int, str] = {}

    for i, o in enumerate(scored_orders):
        peso = float(o.get("total_weight_kg", o.get("weight_kg", 0.0)))
        vol = float(o.get("total_volume_m3", o.get("volume_m3", 0.0)))

        w_int = round(peso * SCALE_WEIGHT)
        v_int = round(vol * SCALE_VOLUME)

        # Seleção do objetivo: score agregado ou eficiência
        if objective_mode == "eficiencia":
            target_score = o.get("efficiency", 0.0)
        else:
            target_score = o.get("score", 0.0)

        score_int = round(target_score * SCALE_SCORE)

        w_ints.append(w_int)
        v_ints.append(v_int)
        obj_ints.append(score_int)

        # Exclusão a priori: pedido isolado estoura o caminhão
        if peso > capacity_kg:
            pre_excluded_reasons[i] = "EXCEDE_PESO_INDIVIDUAL"
            model.Add(x[i] == 0)
        elif vol > capacity_m3:
            pre_excluded_reasons[i] = "EXCEDE_VOLUME_INDIVIDUAL"
            model.Add(x[i] == 0)

        # Restrição linear de 6 metros
        if o.get("has_long_items", False) and not allows_long_items:
            pre_excluded_reasons[i] = "VEICULO_INCOMPATIVEL_6M"
            model.Add(x[i] == 0)

        # Restrição territorial de caminhões médios (Kia Bongo e Hyundai HR)
        if restricted_to_crateus:
            city_name = str(o.get("city_name", "")).strip().upper()
            meta_city = CITY_TO_AXIS_MAP.get(city_name)
            if meta_city and meta_city.get("is_external", False):
                pre_excluded_reasons[i] = "VEICULO_RESTRITO_CIDADE"
                model.Add(x[i] == 0)

        # Pedidos Obrigatórios (SLA ou seleção prévia)
        if o.get("is_mandatory", False) or o["id"] in mandatory_set:
            if i not in pre_excluded_reasons:
                model.Add(x[i] == 1)

    # 3. Restrições Fundamentais da Mochila Multidimensional
    model.Add(sum(w_ints[i] * x[i] for i in range(n)) <= cap_w_int)
    model.Add(sum(v_ints[i] * x[i] for i in range(n)) <= cap_v_int)

    # 4. Função Objetivo: Maximizar Benefício Agregado
    model.Maximize(sum(obj_ints[i] * x[i] for i in range(n)))

    # 5. Execução do Solver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = random_seed

    res_status = solver.Solve(model)
    status_str = solver.StatusName(res_status)
    duration_ms = int((time.perf_counter() - start_time) * 1000)

    selected_ids = []
    tot_w = 0.0
    tot_v = 0.0
    tot_val = 0.0
    decisions = []

    if res_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i in range(n):
            o = scored_orders[i]
            is_selected = (solver.Value(x[i]) == 1)

            if is_selected:
                selected_ids.append(o["id"])
                tot_w += float(o.get("total_weight_kg", 0.0))
                tot_v += float(o.get("total_volume_m3", 0.0))
                tot_val += float(o.get("total_value", o.get("value", 0.0)))
                reason = "SELECIONADO"
            else:
                reason = pre_excluded_reasons.get(i, "NAO_SELECIONADO_SOLVER")

            decisions.append({
                "order_id": o["id"],
                "included": is_selected,
                "score": o.get("score", 0.0),
                "efficiency": o.get("efficiency", 0.0),
                "peso_pct": o.get("peso_pct", 0.0),
                "volume_pct": o.get("volume_pct", 0.0),
                "exclusion_reason": reason
            })
    else:
        # Infeasible ou Unknown
        for i in range(n):
            o = scored_orders[i]
            decisions.append({
                "order_id": o["id"],
                "included": False,
                "score": o.get("score", 0.0),
                "efficiency": o.get("efficiency", 0.0),
                "peso_pct": o.get("peso_pct", 0.0),
                "volume_pct": o.get("volume_pct", 0.0),
                "exclusion_reason": pre_excluded_reasons.get(i, "NAO_SELECIONADO_SOLVER")
            })

    # Assertivas de Invariantes Físicos no Solver
    assert tot_w <= capacity_kg + 0.001, f"ERRO CRÍTICO: Violação de peso no CP-SAT! {tot_w} > {capacity_kg}"
    assert tot_v <= capacity_m3 + 0.001, f"ERRO CRÍTICO: Violação de volume no CP-SAT! {tot_v} > {capacity_m3}"

    # Cálculo do gap de otimalidade
    opt_gap = None
    if res_status == cp_model.OPTIMAL:
        opt_gap = 0.0
    elif res_status == cp_model.FEASIBLE:
        try:
            obj_val = solver.ObjectiveValue()
            best_bound = solver.BestObjectiveBound()
            if obj_val != 0:
                opt_gap = round(abs(best_bound - obj_val) / abs(obj_val), 4)
        except Exception:
            opt_gap = None

    weight_occ = round((tot_w / capacity_kg) * 100, 2)
    volume_occ = round((tot_v / capacity_m3) * 100, 2)
    limiting = "PESO" if (tot_w / capacity_kg) >= (tot_v / capacity_m3) else "VOLUME"

    return {
        "status": status_str,
        "selected_order_ids": selected_ids,
        "total_weight_kg": round(tot_w, 2),
        "total_volume_m3": round(tot_v, 4),
        "total_value": round(tot_val, 2),
        "weight_occupancy_pct": weight_occ,
        "volume_occupancy_pct": volume_occ,
        "limiting_resource": limiting,
        "optimality_gap": opt_gap,
        "solve_duration_ms": duration_ms,
        "algorithm_version": "cpsat-v3.0",
        "decisions": decisions
    }
