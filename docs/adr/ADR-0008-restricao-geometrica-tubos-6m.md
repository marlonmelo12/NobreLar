# ADR-0008: Restrição Linear Dimensional para Tubos e Barras de 6 Metros

## Status
**ACEITO**

## Contexto
Tubos de PVC e treliças metálicas possuem barras rígidas de 6 metros. Modelos de otimização baseados puramente em peso e volume escalares poderiam alocar essas peças em caminhonetes curtas fechadas (HR/Bongo), gerando inviabilidade física no pátio.

## Decisão
Adicionar metadados dimensionais (`has_long_items` e `allows_long_items`) e uma restrição linear estrita no CP-SAT: \(x_i \cdot 	ext{has\_long\_items}_i \le 	ext{allows\_long\_items}_v\).
