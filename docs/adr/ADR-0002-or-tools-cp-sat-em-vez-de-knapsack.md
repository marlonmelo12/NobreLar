# ADR-0002: Adoção do Google OR-Tools CP-SAT em vez do KnapsackSolver Puro

## Status
**ACEITO**

## Contexto
O pacote Google OR-Tools possui um módulo especializado em problemas da mochila (`knapsack_solver`). Entretanto, a operação de materiais de construção exige regras de negócio adicionais, como restrições dimensionais de 6 metros, pedidos obrigatórios (SLA) e agrupamento de pedidos do mesmo cliente.

## Decisão
Adotamos o **CP-SAT Solver** (`ortools.sat.python.cp_model`) como motor oficial de otimização.

## Consequências
- **Positivas:**
  - Suporta nativamente restrições lineares customizadas além do peso e volume clássicos.
  - Suporte trivial para fixar pedidos obrigatórios (\(x_i = 1\)) ou proibir pedidos incompatíveis (\(x_i + x_j \le 1\)).
  - Timeout nativo com devolução da melhor solução viável (*incumbent*).
  - Status explícito de otimalidade (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).
- **Negativas:**
  - Exige escalonamento de variáveis de ponto flutuante para inteiros (gramas e \(cm^3\)).
