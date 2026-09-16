# 11. Estratégia de Testes e Garantia da Qualidade (QA)

---

## 1. Pirâmide de Testes

```
        /        / E2E \       (Cenários completos: CSV -> Otimização -> PDF)
      /-------     / Integr. \     (Endpoints FastAPI + Banco SQLite em memória)
    /-----------   /   Unitários \   (Cálculo de cubagem, Conversão de piso, Invariantes)
  /---------------```

---

## 2. Testes de Invariantes Físicas do Solver

O teste mais crítico do sistema é a **verificação de invariantes**: garantir que nenhuma combinação de parâmetros gere violação física.

```python
import pytest
from app.services.optimizer_cpsat import solve_load_plan

def test_invariants_never_exceed_capacity():
    # Simula 50 pedidos aleatórios pesados e volumosos
    orders = generate_mock_orders(count=50)
    cap_kg = 4800.0
    cap_m3 = 18.5

    status, solver, x = solve_load_plan(orders, cap_kg, cap_m3, allows_long_items=True)

    selected = [orders[i] for i in range(len(orders)) if solver.Value(x[i]) == 1]
    
    total_w = sum(o.weight_kg for o in selected)
    total_v = sum(o.volume_m3 for o in selected)

    # Invariantes absolutas
    assert total_w <= cap_kg, f"Sobrecarga de peso violada: {total_w} > {cap_kg}"
    assert total_v <= cap_m3, f"Sobrecarga de volume violada: {total_v} > {cap_m3}"

def test_long_items_rejected_in_short_vehicle():
    orders = [
        create_order(id=1, weight=100, volume=0.5, has_long_items=True),
        create_order(id=2, weight=100, volume=0.5, has_long_items=False),
    ]
    # Veículo que NÃO aceita 6m
    status, solver, x = solve_load_plan(orders, 1700, 2.5, allows_long_items=False)

    assert solver.Value(x[0]) == 0, "Pedido com 6m alocado indevidamente em veículo curto!"
    assert solver.Value(x[1]) == 1, "Pedido comum deveria ter sido aceito."
```

---

## 3. Benchmarks de Desempenho e Time Budget

- **Métrica de Aceite (RNF-001):** O tempo de processamento do solver deve ser \(\le 5	ext{ segundos}\) para instâncias com até 100 pedidos por eixo (resolução típica em \(pprox 0,4	ext{ s}\)).
- O solver possui hard timeout de `30.0 segundos`. Se estourar o tempo, ele retorna a melhor solução viável (*incumbent*) encontrada até o momento.
