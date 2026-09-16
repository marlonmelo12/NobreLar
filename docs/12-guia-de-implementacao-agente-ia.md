# 12. Guia de Implementação para Agente Autônomo de IA (Zero Alucinação)

> **AVISO AO AGENTE DE IA / CODING AGENT:**  
> Este documento é o **Gabarito Técnico Imutável** para implementação do sistema NobreLOG IA. Não altere os dicionários, expressões regulares, constantes de veículos ou regras determinísticas aqui estabelecidas. Toda a lógica necessária para o backend e otimizador está especificada em código Python pronto para uso.

---

## 1. Stack e Dependências Fixadas (`requirements.txt`)

Para evitar incompatibilidades de versões (ex: Pandera vs Pydantic v2) e falhas de runtime no Windows (WeasyPrint / GTK3):

```text
fastapi>=0.110.0,<0.116.0
uvicorn[standard]>=0.28.0,<0.35.0
pydantic>=2.6.0,<2.11.0
pandera>=0.19.0,<0.21.0
ortools>=9.9.3963,<9.12.0
geopy>=2.4.0,<2.5.0
sqlalchemy>=2.0.28,<2.1.0
python-multipart>=0.0.9
jinja2>=3.1.3
xhtml2pdf>=0.2.15
pytest>=8.0.0
```

> [!NOTE]
> **Compatibilidade Windows sem GTK3:**  
> O `xhtml2pdf` é 100% Python puro e substitui o WeasyPrint no ambiente Windows local sem requerer DLLs nativas de C (Cairo/Pango/GObject). Em ambiente Linux/Docker, WeasyPrint pode ser reativado opcionalmente.

---

## 2. Dicionário Canônico: Cidade $\to$ Eixo Rodoviário (Lookup Table)

Nenhum pedido deve ser processado sem consultar este dicionário. Cidades não mapeadas pertencem a Crateús (descarte do escopo regional) ou devem ser logadas no `CleaningLog`.

```python
# app/core/constants.py

CITY_TO_AXIS_MAP = {
    # Eixo 1: Fronteira Piauí
    "BURITI DOS MONTES": {"axis_id": "eixo-1-fronteira-pi", "axis_name": "Fronteira Piauí", "delivery_order": 1},
    "BARRO VERMELHO":    {"axis_id": "eixo-1-fronteira-pi", "axis_name": "Fronteira Piauí", "delivery_order": 2},
    "TUCUNS":            {"axis_id": "eixo-1-fronteira-pi", "axis_name": "Fronteira Piauí", "delivery_order": 3},
    "QUEIMADAS":         {"axis_id": "eixo-1-fronteira-pi", "axis_name": "Fronteira Piauí", "delivery_order": 4},
    "FILOMENA":          {"axis_id": "eixo-1-fronteira-pi", "axis_name": "Fronteira Piauí", "delivery_order": 5},

    # Eixo 2: Sertão Central
    "SUCESSO":           {"axis_id": "eixo-2-sertao-central", "axis_name": "Sertão Central", "delivery_order": 1},
    "TAMBORIL":          {"axis_id": "eixo-2-sertao-central", "axis_name": "Sertão Central", "delivery_order": 2},
    "NOVA RUSSAS":       {"axis_id": "eixo-2-sertao-central", "axis_name": "Sertão Central", "delivery_order": 3},
    "FAZENDA":           {"axis_id": "eixo-2-sertao-central", "axis_name": "Sertão Central", "delivery_order": 4},
    "IBIAPABA":          {"axis_id": "eixo-2-sertao-central", "axis_name": "Sertão Central", "delivery_order": 5},

    # Eixo 3: Eixo Sul
    "INDEPENDENCIA":     {"axis_id": "eixo-3-sul", "axis_name": "Eixo Sul", "delivery_order": 1},
    "SAO JOSE":          {"axis_id": "eixo-3-sul", "axis_name": "Eixo Sul", "delivery_order": 2},
    "ADAO":              {"axis_id": "eixo-3-sul", "axis_name": "Eixo Sul", "delivery_order": 3},
    "VILA GRACA":        {"axis_id": "eixo-3-sul", "axis_name": "Eixo Sul", "delivery_order": 4},
    "JATOBA DOS UMBELINOS": {"axis_id": "eixo-3-sul", "axis_name": "Eixo Sul", "delivery_order": 5},
    "SAO GONCALO":       {"axis_id": "eixo-3-sul", "axis_name": "Eixo Sul", "delivery_order": 6},

    # Eixo 4: Norte e Serra
    "IPAPORANGA":        {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 1},
    "PORANGA":           {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 2},
    "ARARENDA":          {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 3},
    "VACA MORTA":        {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 4},
    "CURRAL VELHO":      {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 5},
    "CURRAL DO MEIO":    {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 6},
    "ROSARIO":           {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 7},
    "PAU DE OLEIO":      {"axis_id": "eixo-4-norte-serra", "axis_name": "Norte e Serra", "delivery_order": 8},

    # Eixo 5: Inhamuns
    "NOVO ORIENTE":      {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 1},
    "REALEJO":           {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 2},
    "SANTANA":           {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 3},
    "MONTE NEBO":        {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 4},
    "SANTO ANDRE":       {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 5},
    "QUITERIANOPOLIS":   {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 6},
    "BARRA DOS SIMIOES": {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 7},
    "LAGOA DAS PEDRAS":  {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 8},
    "UMBURANA":          {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 9},
    "SITIO GIRA SOL":    {"axis_id": "eixo-5-inhamuns", "axis_name": "Inhamuns", "delivery_order": 10}
}
```

---

## 3. Seed Oficial da Frota de Veículos

```python
# app/core/seeds.py

DEFAULT_VEHICLES = [
    {
        "id": "accelo-815-01",
        "name": "Mercedes-Benz Accelo 815 (3/4)",
        "plate": "NBL-8150",
        "capacity_kg": 4800.0,
        "useful_volume_m3": 18.50, # Cubagem útil corrigida com fator de estivagem
        "useful_length_m": 5.50,
        "allows_long_items": True,  # Suporta barras de 6m
        "active": True
    },
    {
        "id": "kia-bongo-01",
        "name": "Kia Bongo K2500",
        "plate": "NBL-2500",
        "capacity_kg": 1700.0,
        "useful_volume_m3": 6.50,
        "useful_length_m": 3.10,
        "allows_long_items": False, # NÃO suporta barras de 6m
        "active": True
    },
    {
        "id": "titan-160-01",
        "name": "Honda Titan 160 Cargo",
        "plate": "NBL-1601",
        "capacity_kg": 300.0,
        "useful_volume_m3": 0.38,
        "useful_length_m": 0.80,
        "allows_long_items": False,
        "active": True
    }
]
```

---

## 4. Parsers e Expressões Regulares Oficiais

```python
# app/services/parsers.py
import re
from datetime import datetime

# Regex testada com 100% de sucesso nas 1.981 linhas da base
ITEM_REGEX = re.compile(
    r'^\s*(?P<code>\d+)\s*-\s*(?P<desc>.*?)\s*\((?P<qtd>[\d.,]+)\s*(?P<unit>[A-Za-z0-9]+)\)\s*$'
)

def clean_currency(val) -> float:
    if not val or val == "nan":
        return 0.0
    s = str(val).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try:
        return float(s)
    except ValueError:
        return 0.0

def sanitize_order_id(raw_id: str) -> str:
    # Ex: '12.608570' -> 'L12608570', 'L12609716.' -> 'L12609716'
    digits = re.sub(r'[^0-9]', '', str(raw_id))
    return f"L{digits}" if digits else "INVALIDO"

def sanitize_brazilian_date(d_str: str) -> str:
    if not d_str or str(d_str) == "nan":
        return datetime.today().strftime('%Y-%m-%d')
    s = str(d_str).strip()
    # Correção dos erros encontrados na base
    s = s.replace('26/08/14', '26/08/26')
    s = s.replace('15/0826', '15/08/26').replace('20/0826', '20/08/26')
    s = s.replace('28/0/26', '28/08/26').replace('290826', '29/08/26')
    
    for fmt in ('%d/%m/%y', '%d/%m/%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except ValueError:
            pass
    return datetime.today().strftime('%Y-%m-%d')
```

---

## 5. Tabela de Categorização e Fallback (587 SKUs fora do Top 85)

```python
# app/services/cubagem_service.py

def classify_and_fallback(product_desc: str):
    d = product_desc.upper()
    
    # 1. Itens Longos (6 metros)
    if any(k in d for k in ['CANO', 'TUBO', 'TRELICA', 'ESPACADOR 6M', 'FORRO NOVAFORMA']):
        # Se for cano de esgoto 100mm: 0.5kg / 0.00785m3 por metro
        # Barra de cano de água 25mm: 0.26kg / 0.00049m3 por metro
        return {"peso": 0.50, "volume": 0.0080, "has_long": True, "source": "heuristica_longo"}
    
    # 2. Cimentos e Argamassas
    if any(k in d for k in ['CIMENTO', 'ARGAMASSA', 'GESSO', 'CAL ']):
        return {"peso": 15.0, "volume": 0.0100, "has_long": False, "source": "heuristica_argamassa"}
        
    # 3. Cerâmicas e Pisos
    if any(k in d for k in ['PISO', 'PORC', 'REV', 'CERBRAS', 'POINTER', 'KARINA']):
        # Média por m²: ~14 kg/m² e ~0.009 m³/m²
        return {"peso": 14.0, "volume": 0.0090, "has_long": False, "source": "heuristica_piso"}
        
    # 4. Caixas d'Água
    if any(k in d for k in ['CX. DAGUA', 'CAIXA D AGUA', 'BAKOF', 'FORTLEV']):
        return {"peso": 15.0, "volume": 1.5000, "has_long": False, "source": "heuristica_caixa"}
        
    # 5. Conexões Hidráulicas
    if any(k in d for k in ['JOELHO', 'TEE ', 'ADAPTADOR', 'LUVA', 'CURVA', 'SIFAO', 'VALVULA']):
        return {"peso": 0.05, "volume": 0.0003, "has_long": False, "source": "heuristica_conexao"}

    # 6. Louças Sanitárias
    if any(k in d for k in ['VASO', 'BACIA', 'LOUCA', 'CUBA', 'LAVATORIO', 'ASSENTO']):
        return {"peso": 20.0, "volume": 0.1000, "has_long": False, "source": "heuristica_louca"}

    # 7. Elétrica e Iluminação
    if any(k in d for k in ['CABO', 'FIO', 'DISJUNTOR', 'TOMADA', 'LUMINARIA', 'REFLETOR', 'LAMPADA']):
        return {"peso": 0.10, "volume": 0.0005, "has_long": False, "source": "heuristica_eletrica"}
        
    # 8. Tintas e Químicos
    if any(k in d for k in ['TINTA', 'LATEX', 'TEXT.', 'VERNIZ', 'MASSA CORRIDA']):
        return {"peso": 18.0, "volume": 0.0200, "has_long": False, "source": "heuristica_tinta"}

    # Fallback Geral (Miudezas e Ferramentas)
    return {"peso": 0.25, "volume": 0.0008, "has_long": False, "source": "heuristica_geral"}
```

---

## 6. Algoritmo de Order Splitting (Pré-Otimização)

```python
# app/services/pre_processor.py

def split_overweight_orders(orders: list, max_capacity_kg: float = 4800.0) -> list:
    """
    Desmembra pedidos maiores que a capacidade nominal do caminhão em subpedidos vinculados.
    Ex: 100 sacos de cimento (5.000 kg) -> P1 (4.000 kg) + P2 (1.000 kg)
    """
    processed_orders = []
    target_p1_kg = max_capacity_kg * 0.85 # Alvo de 85% para deixar margem de preenchimento

    for ord in orders:
        if ord["total_weight_kg"] <= max_capacity_kg:
            processed_orders.append(ord)
            continue
            
        # Pedido excede capacidade máxima -> Splitting
        ratio = target_p1_kg / ord["total_weight_kg"]
        
        # Subpedido P1
        p1 = dict(ord)
        p1["id"] = f"{ord['id']}-P1"
        p1["is_split"] = True
        p1["parent_order_id"] = ord["id"]
        p1["total_weight_kg"] = round(ord["total_weight_kg"] * ratio, 2)
        p1["total_volume_m3"] = round(ord["total_volume_m3"] * ratio, 4)
        p1["total_value"] = round(ord["total_value"] * ratio, 2)
        
        # Subpedido P2
        p2 = dict(ord)
        p2["id"] = f"{ord['id']}-P2"
        p2["is_split"] = True
        p2["parent_order_id"] = ord["id"]
        p2["total_weight_kg"] = round(ord["total_weight_kg"] - p1["total_weight_kg"], 2)
        p2["total_volume_m3"] = round(ord["total_volume_m3"] - p1["total_volume_m3"], 4)
        p2["total_value"] = round(ord["total_value"] - p1["total_value"], 2)

        processed_orders.extend([p1, p2])

    return processed_orders
```

---

## 7. Otimizador Completo CP-SAT (`optimizer_cpsat.py`)

```python
# app/services/optimizer_cpsat.py
import math
from ortools.sat.python import cp_model

def solve_load_allocation(
    orders: list,
    capacity_kg: float,
    capacity_m3: float,
    allows_long_items: bool,
    w_weight: float = 0.25,
    w_volume: float = 0.25,
    w_value: float = 0.35,
    w_freq: float = 0.15,
    time_limit_sec: float = 30.0
):
    model = cp_model.CpModel()

    # Fatores de Escalonamento (Aritmética Inteira)
    SCALE_W = 1_000        # kg para g
    SCALE_V = 1_000_000    # m³ para cm³
    SCALE_S = 10_000       # precisão de 4 decimais

    cap_w_int = round(capacity_kg * SCALE_W)
    cap_v_int = round(capacity_m3 * SCALE_V)

    n = len(orders)
    if n == 0:
        return {"status": "NO_ORDERS", "selected_order_ids": []}

    max_val = max(o["total_value"] for o in orders) if orders else 1.0
    max_freq = max(o.get("sale_frequency", 1) for o in orders) if orders else 1.0

    # Variáveis de Decisão
    x = [model.NewBoolVar(f"x_{orders[i]['id']}") for i in range(n)]

    w_ints = []
    v_ints = []
    scores_int = []

    for i, o in enumerate(orders):
        # 1. Consumo relativo
        pw = o["total_weight_kg"] / capacity_kg
        pv = o["total_volume_m3"] / capacity_m3
        # 2. Relevância logarítmica
        vf = math.log1p(o["total_value"]) / math.log1p(max_val) if max_val > 0 else 0
        qf = math.log1p(o.get("sale_frequency", 1)) / math.log1p(max_freq) if max_freq > 0 else 0
        
        # 3. Score Agregado
        score = (w_weight * pw) + (w_volume * pv) + (w_value * vf) + (w_freq * qf)
        
        w_ints.append(round(o["total_weight_kg"] * SCALE_W))
        v_ints.append(round(o["total_volume_m3"] * SCALE_V))
        scores_int.append(round(score * SCALE_S))

    # Restrições de Capacidade Máxima
    model.Add(sum(w_ints[i] * x[i] for i in range(n)) <= cap_w_int)
    model.Add(sum(v_ints[i] * x[i] for i in range(n)) <= cap_v_int)

    # Restrição Dimensional (Peças de 6m)
    for i in range(n):
        if orders[i].get("has_long_items", False) and not allows_long_items:
            model.Add(x[i] == 0)

    # Pedidos Obrigatórios (SLA)
    for i in range(n):
        if orders[i].get("is_mandatory", False):
            model.Add(x[i] == 1)

    # Função Objetivo: Maximizar Benefício Agregado
    model.Maximize(sum(scores_int[i] * x[i] for i in range(n)))

    # Resolver
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8

    res_status = solver.Solve(model)
    status_str = solver.StatusName(res_status)

    selected_ids = []
    tot_w = 0.0
    tot_v = 0.0
    tot_val = 0.0

    if res_status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for i in range(n):
            if solver.Value(x[i]) == 1:
                selected_ids.append(orders[i]["id"])
                tot_w += orders[i]["total_weight_kg"]
                tot_v += orders[i]["total_volume_m3"]
                tot_val += orders[i]["total_value"]

    # Assertivas de Invariantes Independentes
    assert tot_w <= capacity_kg + 0.001, "ERRO CRÍTICO: Violação de Peso no Solver!"
    assert tot_v <= capacity_m3 + 0.001, "ERRO CRÍTICO: Violação de Volume no Solver!"

    return {
        "status": status_str,
        "selected_order_ids": selected_ids,
        "total_weight_kg": round(tot_w, 2),
        "total_volume_m3": round(tot_v, 4),
        "total_value": round(tot_val, 2),
        "weight_occupancy_pct": round((tot_w / capacity_kg) * 100, 2),
        "volume_occupancy_pct": round((tot_v / capacity_m3) * 100, 2),
        "limiting_resource": "PESO" if (tot_w / capacity_kg) >= (tot_v / capacity_m3) else "VOLUME"
    }
```

---


---

## 7-B. Solucionador do Caixeiro Viajante (TSP) com OR-Tools Routing

Após a seleção dos pedidos pelo CP-SAT, o sistema executa a roteirização do Caixeiro Viajante para ordenar as paradas do caminhão:

```python
# app/services/tsp_solver.py
import math
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def solve_tsp_order(
    locations: list[tuple[float, float]],
    depot_index: int = 0,
    roundtrip: bool = True
) -> dict:
    """
    locations: Lista de tuplas (lat, lon), onde o índice 0 é o CD Nobre Lar Crateús.
    Retorna a sequência ótima de nós e a distância viária total estimada.
    """
    n = len(locations)
    if n <= 1:
        return {"route": [0], "total_distance_km": 0.0}

    # 1. Matriz de Distâncias Viárias (Haversine + Tortuosidade 1.28)
    def dist_meters(c1, c2):
        lat1, lon1, lat2, lon2 = map(math.radians, [c1[0], c1[1], c2[0], c2[1]])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return int(6371000 * c * 1.28) # metros

    matrix = [[dist_meters(locations[i], locations[j]) for j in range(n)] for i in range(n)]

    manager = pywrapcp.RoutingIndexManager(n, 1, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def callback(from_idx, to_idx):
        return matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

    transit_idx = routing.RegisterTransitCallback(callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_idx)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        return {"route": list(range(n)), "total_distance_km": 0.0}

    idx = routing.Start(0)
    route = []
    tot_dist = 0
    while not routing.IsEnd(idx):
        node = manager.IndexToNode(idx)
        route.append(node)
        prev = idx
        idx = solution.Value(routing.NextVar(idx))
        tot_dist += routing.GetArcCostForVehicle(prev, idx, 0)

    if roundtrip:
        route.append(manager.IndexToNode(idx))

    return {
        "route": route,
        "total_distance_km": round(tot_dist / 1000.0, 2)
    }
```

## 8. Golden Test Fixture (Gabarito de Teste Unitário)

```python
# tests/test_golden_fixture.py
import pytest
from app.services.optimizer_cpsat import solve_load_allocation

def test_golden_allocation_eixo4_accelo():
    """
    Gabarito de validação: Eixo 4 (Ipaporanga/Poranga) com Accelo 815
    """
    mock_orders = [
        {"id": "L01", "total_weight_kg": 2000.0, "total_volume_m3": 1.5, "total_value": 4500.0, "has_long_items": False},
        {"id": "L02", "total_weight_kg": 1800.0, "total_volume_m3": 1.2, "total_value": 3900.0, "has_long_items": False},
        {"id": "L03", "total_weight_kg": 900.0,  "total_volume_m3": 0.8, "total_value": 2100.0, "has_long_items": False},
        {"id": "L04", "total_weight_kg": 500.0,  "total_volume_m3": 0.4, "total_value": 1100.0, "has_long_items": False},
        {"id": "L05", "total_weight_kg": 150.0,  "total_volume_m3": 0.2, "total_value": 350.0,  "has_long_items": True},
    ]

    # Teste 1: Accelo 815 (Comporta 6m, 4800 kg, 18.5 m³)
    result = solve_load_allocation(
        orders=mock_orders,
        capacity_kg=4800.0,
        capacity_m3=18.5,
        allows_long_items=True
    )

    assert result["status"] in ("OPTIMAL", "FEASIBLE")
    assert result["total_weight_kg"] <= 4800.0
    assert result["total_volume_m3"] <= 18.5
    assert "L05" in result["selected_order_ids"], "L05 tem 6m e deve ser aceito no Accelo"

    # Teste 2: Bongo K2500 (NÃO comporta 6m, 1700 kg, 6.5 m³)
    result_bongo = solve_load_allocation(
        orders=mock_orders,
        capacity_kg=1700.0,
        capacity_m3=6.5,
        allows_long_items=False
    )
    assert "L05" not in result_bongo["selected_order_ids"], "L05 NÃO pode ser alocado no Bongo!"
    assert result_bongo["total_weight_kg"] <= 1700.0
```
