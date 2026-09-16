# ADR-0009: Fallback Heurístico de Cubagem por Categoria

## Status
**ACEITO**

## Contexto
O arquivo `Ranking_Top85_Materiais.csv` cobre 85 produtos essenciais, mas 587 produtos ativos não possuem ficha técnica cadastrada. A regra inicial de excluir produtos sem cubagem causaria a rejeição de 51,9% dos pedidos faturados.

## Decisão
Implementar um sistema de fallback de cubagem baseado em parâmetros médios por categoria (hidráulica leve, elétrica, ferragens, tintas), exibindo o indicador `% de cubagem estimada` no romaneio.
