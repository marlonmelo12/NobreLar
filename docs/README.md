# NobreLOG IA — Documentação Oficial do Sistema

Bem-vindo ao repositório de documentação técnica e de arquitetura do **NobreLOG IA**, sistema inteligente de alocação, cubagem e otimização de cargas por eixo rodoviário desenvolvido para a **Nobre Lar Home Center** (Matriz Crateús - CE).

---

## 🧭 Mapa de Navegação da Documentação

| Arquivo | Título | Conteúdo Principal |
| :--- | :--- | :--- |
| [01-visao-geral-e-escopo.md](./01-visao-geral-e-escopo.md) | **Visão Geral e Escopo** | Contexto operacional, dor de negócio, escala, escopo do MVP e pós-MVP. |
| [02-requisitos-do-sistema.md](./02-requisitos-do-sistema.md) | **Requisitos do Sistema** | Requisitos Funcionais (RF-001 a RF-018) e Não-Funcionais (RNF-001 a RNF-010). |
| [03-regras-de-negocio.md](./03-regras-de-negocio.md) | **Regras de Negócio** | Regras determinísticas (RN-001 a RN-012), fatiamento, conversões e travas. |
| [04-arquitetura-e-stack.md](./04-arquitetura-e-stack.md) | **Arquitetura e Stack Tecnológica** | Modelo C4, monólito modular, backend FastAPI, frontend React + TSX. |
| [05-engenharia-de-dados-e-limpeza.md](./05-engenharia-de-dados-e-limpeza.md) | **Engenharia de Dados e Cubagem** | Pipelines Pandera, sanitização regex, conversão de pisos, cubagem Top 85 e fallback. |
| [06-motor-de-otimizacao-cp-sat.md](./06-motor-de-otimizacao-cp-sat.md) | **Motor de Otimização (CP-SAT)** | Formulação matemática, MKP multidimensional 0-1, score logarítmico e constraints. |
| [07-modelo-de-dados.md](./07-modelo-de-dados.md) | **Modelo de Dados e Schemas** | Diagrama Entidade-Relacionamento (ERD), schemas SQL e modelos Pydantic. |
| [08-rotas-geografia-e-veiculos.md](./08-rotas-geografia-e-veiculos.md) | **Rotas, Geografia e Veículos** | Os 5 eixos rodoviários, ordenação de descarga, dimensionamento da frota e estivagem. |
| [09-api-e-integracao.md](./09-api-e-integracao.md) | **API REST e Integrações** | Endpoints OpenAPI, contratos de payload e fluxo de execução. |
| [10-plano-de-carga-e-romaneio.md](./10-plano-de-carga-e-romaneio.md) | **Plano de Carga e Romaneio** | Layout do romaneio expedido, exportação PDF WeasyPrint e gestão de recebíveis. |
| [11-estrategia-de-testes-e-qa.md](./11-estrategia-de-testes-e-qa.md) | **Estratégia de Testes e QA** | Testes de invariantes, unitários, benchmarks de otimização e auditoria. |
| [12-guia-de-implementacao-agente-ia.md](./12-guia-de-implementacao-agente-ia.md) | **Guia do Agente de IA (Zero Alucinação)** | Blueprints determinísticos, regexes compiladas, seed data, lookups fechados e golden tests. |
| [adr/README.md](./adr/README.md) | **Architecture Decision Records** | Catálogo formal de ADR-0001 a ADR-0010 justificando escolhas estruturais. |

---

## 🎯 Destaques de Engenharia da Versão 3.0

Esta documentação foi refinada com base na auditoria empírica de 715 registros de vendas e 688 pedidos faturados reais da empresa:
1. **Order Splitting Automático (RN-007 / ADR-0007):** Resolve o travamento de pedidos de cimento de 5.000 kg através de remessas parciais vinculadas (`-P1`, `-P2`).
2. **Restrição Linear de 6 Metros (RN-008 / ADR-0008):** Impede alocação de tubulações longas de esgoto/água em veículos de caçamba curta.
3. **Fallback Heurístico de Cubagem (RN-004 / ADR-0009):** Salva 52% dos pedidos contendo produtos fora do Top 85 com densidades categorizadas.
4. **Sanidade Volumétrica dos Veículos (RN-009 / ADR-0010):** Parametrização das dimensões reais dos caminhões (superando a distorção de 2,45 m³ do cadastro).
5. **Rastreabilidade de Recebíveis no Romaneio (RN-011):** Gestão de entregas com pagamento na entrega (`A RECEBER`).
