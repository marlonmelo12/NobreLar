# Architecture Decision Records (ADRs)

Este diretório contém os registros formais de decisões arquiteturais do projeto **NobreLOG IA**. Cada ADR documenta o contexto, a decisão adotada, as alternativas descartadas e as consequências técnicas decorrentes.

---

## 📋 Catálogo de ADRs

| ADR | Título | Status | Contexto Principal |
| :--- | :--- | :---: | :--- |
| [ADR-0001](./ADR-0001-otimizador-sem-ml-puro.md) | Não utilizar Machine Learning no núcleo de decisão | **ACEITO** | Problema combinatório com restrições rígidas; ML não garante viabilidade. |
| [ADR-0002](./ADR-0002-or-tools-cp-sat-em-vez-de-knapsack.md) | Adoção do Google OR-Tools CP-SAT | **ACEITO** | Suporte a restrições multidimensionais e flexibilidade para regras de negócio. |
| [ADR-0003](./ADR-0003-score-multicriterio-logaritmico.md) | Função objetivo com Score Logarítmico | **ACEITO** | Suavização da cauda longa de ticket médio e equilíbrio valor vs ocupação. |
| [ADR-0004](./ADR-0004-validacao-declarativa-pandera-pydantic.md) | Validação declarativa via Pandera e Pydantic | **ACEITO** | Eliminação de código de validação disperso e geração de log de limpeza. |
| [ADR-0005](./ADR-0005-monolito-modular-fastapi-react.md) | Adoção de Monólito Modular (FastAPI + React) | **ACEITO** | Simplicidade operacional, velocidade de entrega e desacoplamento interno. |
| [ADR-0006](./ADR-0006-sem-geocodificacao-externa-no-mvp.md) | Proibição de enriquecimento geográfico externo | **ACEITO** | Conformidade com o regulamento do desafio (LGPD e anonimização). |
| [ADR-0007](./ADR-0007-pre-processing-order-splitting.md) | Pré-processador de Fatiamento de Cargas (Order Splitting) | **ACEITO** | Cargas que excedem 4.800 kg (cimento) fatiadas em remessas vinculadas. |
| [ADR-0008](./ADR-0008-restricao-geometrica-tubos-6m.md) | Restrição linear dimensional para tubos de 6 metros | **ACEITO** | Incompatibilidade física de canos longos com veículos curtos fechados. |
| [ADR-0009](./ADR-0009-fallback-heuristico-cubagem-skus.md) | Fallback heurístico de cubagem por categoria | **ACEITO** | Preservação de 52% dos pedidos contendo produtos fora do Top 85. |
| [ADR-0010](./ADR-0010-sanidade-volumetrica-dos-veiculos.md) | Parametrização da cubagem útil operacional da frota | **ACEITO** | Correção do erro cadastral histórico de 2,45 m³ no Mercedes Accelo 815. |
