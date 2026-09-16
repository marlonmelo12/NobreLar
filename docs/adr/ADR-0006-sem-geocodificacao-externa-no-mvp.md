# ADR-0006: Proibição de Enriquecimento Geográfico Externo no MVP

## Status
**ACEITO**

## Contexto
O desafio exige o respeito à anonimização e conformidade com a LGPD, vetando a reidentificação ou cruzamento com bases de dados externas.

## Decisão
No MVP, a ordem das cidades nos eixos é uma configuração pré-cadastrada no sistema (`City.delivery_order`), sem requisições a serviços externos de mapas ou geocodificação.
