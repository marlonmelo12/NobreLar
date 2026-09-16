# ADR-0004: Validação Declarativa via Pandera e Pydantic

## Status
**ACEITO**

## Contexto
A base de dados continha falhas de preenchimento (datas inválidas, pedidos nulos e tipos heterogêneos). Validações condicionais procedurais dispersas geram código frágil e difícil de testar.

## Decisão
Adotar **Pandera** para validação de DataFrames na camada de ingestão e **Pydantic** para validação na camada de transporte da API.

## Consequências
- **Positivas:**
  - Contratos de dados auto-documentados e executáveis.
  - Geração automática do log de inconsistências para o `CleaningLog`.
  - Rejeição atômica de linhas defeituosas sem interrupção do processamento do lote.
