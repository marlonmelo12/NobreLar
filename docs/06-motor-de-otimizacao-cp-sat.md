# 06. Motor de Otimização (OR-Tools CP-SAT)

---

## 1. Formulação Matemática do Problema

O problema é formalmente classificado como um **Problema da Mochila Multidimensional 0-1** (*Multidimensional 0-1 Knapsack Problem - MKP*), estendido com restrições lineares de compatibilidade física.

### Conjuntos e Índices
- \(I = \{1, 2, \dots, N\}\): Conjunto de pedidos elegíveis pertencentes ao eixo selecionado.
- \(v\): O veículo alocado para a rota.

### Parâmetros
- \(W_i \in \mathbb{R}^+\): Peso total do pedido \(i\) em kg.
- \(V_i \in \mathbb{R}^+\): Volume total do pedido \(i\) em \(m^3\).
- \(S_i \in \mathbb{R}^+\): Score multicritério consolidado do pedido \(i\).
- \(L_i \in \{0, 1\}\): Flag booleana indicando se o pedido \(i\) contém tubos/barras de 6 metros (`has_long_items`).
- \(CAP_W \in \mathbb{R}^+\): Capacidade máxima de peso útil do veículo em kg.
- \(CAP_V \in \mathbb{R}^+\): Capacidade cúbica útil efetiva do veículo em \(m^3\).
- \(ALLOWS\_L_v \in \{0, 1\}\): Flag indicando se o veículo comporta peças de 6 metros (`allows_long_items`).

### Variáveis de Decisão
$$x_i \in \{0, 1\} \quad orall i \in I$$
Onde \(x_i = 1\) se o pedido for incluído no plano de carga e \(x_i = 0\) caso contrário.

---

## 2. Modelo de Programação por Restrições

$$\max \sum_{i \in I} S_i \cdot x_i$$

### Restrições Rígidas (Hard Constraints):
1. **Capacidade de Peso:**
   $$\sum_{i \in I} W_i \cdot x_i \le CAP_W$$
2. **Capacidade Volumétrica:**
   $$\sum_{i \in I} V_i \cdot x_i \le CAP_V$$
3. **Incompatibilidade Linear Dimensional (6 metros):**
   $$x_i \cdot L_i \le ALLOWS\_L_v \quad orall i \in I$$
4. **Pedidos Obrigatórios (SLA / Prioridade Manual):**
   $$x_i = 1 \quad orall i \in M \subset I$$

---

## 3. Função Objetivo: Score Multicritério com Suavização Logarítmica

Para evitar que pedidos milionários de baixo volume monopolizem a carga ou que cargas gigantes de baixo valor saturem o caminhão:

$$S_i = w_w \cdot \left(rac{W_i}{CAP_W}ight) + w_v \cdot \left(rac{V_i}{CAP_V}ight) + w_f \cdot \left(rac{\log(1 + 	ext{Valor}_i)}{\log(1 + 	ext{Valor}_{max})}ight) + w_q \cdot \left(rac{\log(1 + 	ext{Freq}_i)}{\log(1 + 	ext{Freq}_{max})}ight)$$

### Perfis de Otimização Padrão
- **Equilibrado (Default):** \(w_w = 0,25\), \(w_v = 0,25\), \(w_f = 0,35\), \(w_q = 0,15\).
- **Foco Financeiro:** \(w_w = 0,15\), \(w_v = 0,15\), \(w_f = 0,60\), \(w_q = 0,10\).
- **Foco em Ocupação Física:** \(w_w = 0,40\), \(w_v = 0,40\), \(w_f = 0,15\), \(w_q = 0,05\).

---

## 4. Implementação de Referência no Backend

```python
from ortools.sat.python import cp_model

def solve_load_plan(
    orders: list,
    capacity_kg: float,
    capacity_m3: float,
    allows_long_items: bool,
    time_limit_sec: float = 30.0
):
    model = cp_model.CpModel()

    # Escalonamento para inteiros (Aritmética exata do CP-SAT)
    scale_w = 1_000        # gramas
    scale_v = 1_000_000    # cm³
    scale_s = 10_000       # precisão de 4 casas decimais

    cap_w_int = round(capacity_kg * scale_w)
    cap_v_int = round(capacity_m3 * scale_v)

    n = len(orders)
    x = [model.NewBoolVar(f"x_{orders[i].id}") for i in range(n)]

    w_ints = [round(orders[i].weight_kg * scale_w) for i in range(n)]
    v_ints = [round(orders[i].volume_m3 * scale_v) for i in range(n)]
    s_ints = [round(orders[i].score * scale_s) for i in range(n)]

    # 1. Hard Constraints
    model.Add(sum(w_ints[i] * x[i] for i in range(n)) <= cap_w_int)
    model.Add(sum(v_ints[i] * x[i] for i in range(n)) <= cap_v_int)

    # 2. Linear Dimensional Constraint (6m)
    for i in range(n):
        if orders[i].has_long_items and not allows_long_items:
            model.Add(x[i] == 0)

    # 3. Mandatory Orders (SLA)
    for i in range(n):
        if orders[i].is_mandatory:
            model.Add(x[i] == 1)

    # 4. Maximize Aggregated Score
    model.Maximize(sum(s_ints[i] * x[i] for i in range(n)))

    # Resolver com CP-SAT
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_sec
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    return status, solver, x
```
