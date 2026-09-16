"""Módulo de cálculo do score multicritério e score de eficiência.

Implementa as regras canônicas de negócio definidas nos requisitos RF-009,
RF-009-A e ADR-0003:
- Normalização relativa de capacidade (peso e volume divididos pelas capacidades do caminhão)
- Normalização logarítmica de valor financeiro e frequência de vendas para evitar distorção por outliers
- Score multicritério agregado: S_i = w_p*p_i + w_v*v_i + w_f*f_i + w_q*q_i
- Score de eficiência por unidade de capacidade consumida: E_i
"""

import math
from typing import List, Dict, Any


def calculate_order_scores(
    orders: List[Dict[str, Any]],
    capacity_kg: float,
    capacity_m3: float,
    w_peso: float = 0.25,
    w_volume: float = 0.25,
    w_valor: float = 0.30,
    w_quantidade: float = 0.20,
    epsilon: float = 1e-6
) -> List[Dict[str, Any]]:
    """Calcula o score de prioridade multicritério (S_i) e eficiência (E_i) para cada pedido.

    Trata casos de borda como valor_max = 0, frequência = 0 e pesos nulos.
    """
    if capacity_kg <= 0 or capacity_m3 <= 0:
        raise ValueError("As capacidades do veículo devem ser estritamente positivas.")

    # Validação da soma dos pesos (tolerância de 1e-5)
    soma_pesos = w_peso + w_volume + w_valor + w_quantidade
    if abs(soma_pesos - 1.0) > 1e-5:
        raise ValueError(f"A soma dos pesos do perfil de otimização deve ser 1.0 (obtido: {soma_pesos:.6f}).")

    if not orders:
        return []

    # Extração de máximos para normalização logarítmica
    max_val = max((float(o.get("total_value", o.get("value", 0.0))) for o in orders), default=1.0)
    max_freq = max((int(o.get("sale_frequency", 1)) for o in orders), default=1)

    log_max_val = math.log1p(max_val) if max_val > 0 else 1.0
    log_max_freq = math.log1p(max_freq) if max_freq > 0 else 1.0

    scored_orders = []

    for ord_dict in orders:
        item = dict(ord_dict)
        peso = float(item.get("total_weight_kg", item.get("weight_kg", 0.0)))
        vol = float(item.get("total_volume_m3", item.get("volume_m3", 0.0)))
        val = float(item.get("total_value", item.get("value", 0.0)))
        freq = int(item.get("sale_frequency", 1))

        # 1. Consumos relativos de capacidade
        p_i = peso / capacity_kg
        v_i = vol / capacity_m3

        # 2. Relevância comercial com amortecimento logarítmico
        f_i = math.log1p(val) / log_max_val if log_max_val > 0 else 0.0
        q_i = math.log1p(freq) / log_max_freq if log_max_freq > 0 else 0.0

        # 3. Score Agregado de Prioridade (0 <= S_i <= 1)
        s_i = (w_peso * p_i) + (w_volume * v_i) + (w_valor * f_i) + (w_quantidade * q_i)

        # 4. Score de Eficiência (Benefício por capacidade consumida)
        denominador = (w_peso * p_i) + (w_volume * v_i) + epsilon
        numerador = (w_valor * f_i) + (w_quantidade * q_i)
        e_i = numerador / denominador

        item["peso_pct"] = round(p_i * 100, 2)
        item["volume_pct"] = round(v_i * 100, 2)
        item["score"] = round(s_i, 6)
        item["efficiency"] = round(e_i, 6)

        scored_orders.append(item)

    return scored_orders
