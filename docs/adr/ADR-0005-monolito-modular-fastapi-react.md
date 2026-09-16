# ADR-0005: Arquitetura em Monólito Modular (FastAPI + React)

## Status
**ACEITO**

## Contexto
Avaliou-se a divisão do sistema em microsserviços (ex: serviço de ingestão, serviço de otimização, serviço de romaneio). 

## Decisão
Adotou-se o padrão de **Monólito Modular**. O backend e o solver residem na mesma aplicação FastAPI, modularizada internamente por domínios.

## Consequências
- **Positivas:**
  - Zero sobrecarga de latência de rede entre serviços na chamada do solver.
  - Facilidade de deploy em contêiner único via Docker.
  - Baixa complexidade operacional para o evento do Hackathon e produção inicial.
