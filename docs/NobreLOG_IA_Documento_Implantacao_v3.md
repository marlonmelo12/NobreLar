# DOCUMENTO DE IMPLANTAÇÃO

## NobreLOG IA — Montagem Automática de Carga por Eixo

**Projeto:** NobreLOG IA
**Evento:** Hackathon IA 2026 — UFC Campus Crateús
**Empresa:** Grupo Nobre Lar
**Backend:** Python
**Frontend:** React + TypeScript (TSX)
**Tipo de solução:** Sistema de otimização logística com interface web
**Versão:** 3.0 — Versão Canônica Consolidada (UTF-8, Order Splitting, Restrição 6m, Fallback Cubagem, GeoPy, OpenStreetMap e TSP)

---

## Histórico de revisão

| Versão | Mudanças principais |
|--------|---------------------|
| 1.0 | Documento original de implantação |
| 2.0 | Função objetivo formalizada com score multicritério; CP-SAT definido como solver; perfis de otimização configuráveis; relatório de decisão por pedido; edição manual auditada; validação declarativa de schema; RBAC no MVP; CI/CD; testes de carga; ADR para enriquecimento de dados |

---

# 1. Objetivo do documento

Este documento define a proposta técnica para implantação do sistema NobreLOG IA, considerando os requisitos apresentados no desafio da Nobre Lar e uma abordagem de arquitetura simples, sustentável e preferencialmente baseada em software open source.

O objetivo do sistema é automatizar a montagem de cargas dos caminhões, selecionando pedidos que maximizem a utilização da capacidade disponível sem ultrapassar os limites de peso e volume.

O desafio estabelece que o sistema deve receber os pedidos de um eixo e as características do veículo e produzir um plano de carga contendo os pedidos selecionados, valor total, peso, volume, percentual de ocupação e ordem de descarga.

A solução deve priorizar:

* simplicidade;
* confiabilidade;
* rastreabilidade;
* explicabilidade da decisão;
* facilidade de manutenção;
* baixo custo operacional;
* possibilidade de implantação posterior na operação real;
* ausência de complexidade de IA onde um algoritmo determinístico resolve o problema.

### 1.1 O que mudou na versão 2.0

A versão 1.0 definia corretamente o caminho feliz do sistema (dados limpos → otimização → plano válido), mas deixava em aberto, como "decisões a validar com o stakeholder", justamente os pontos de maior risco de implementação:

* qual é exatamente a função objetivo;
* o que acontece quando o solver não converge dentro do tempo aceitável;
* como o operador ajusta manualmente um plano sem quebrar as restrições;
* por que um pedido específico ficou de fora da carga.

A versão 2.0 fecha esses pontos. As perguntas aos stakeholders (seção 36) continuam existindo, mas cada uma agora tem um **valor padrão implementado e configurável**, de modo que o sistema funcione end-to-end mesmo antes da resposta definitiva da operação.

---

# 2. Contexto do problema

Segundo o desafio, o Grupo Nobre Lar opera a partir do centro de distribuição em Crateús, atendendo cinco eixos rodoviários com quatro caminhões. A montagem da carga atualmente é realizada manualmente e baseada principalmente no valor dos pedidos.

O coordenador pode gastar entre 40 e 60 minutos por dia nessa atividade.

O problema principal não é encontrar uma nova rota, mas determinar quais pedidos devem ser colocados em determinado caminhão respeitando simultaneamente:

* capacidade máxima em kg;
* capacidade máxima em m³.

O desafio determina ainda que a solução deve gerar um plano de carga utilizável pela expedição.

As metas do MVP são:

* reduzir o tempo de montagem para menos de 5 minutos;
* não gerar cargas acima da capacidade de peso;
* não gerar cargas acima da capacidade de volume;
* produzir um plano utilizável pela expedição;
* registrar as correções realizadas durante a limpeza dos dados.

## 2.1 Natureza formal do problema

Trata-se de um **problema da mochila multidimensional 0-1** (*multidimensional knapsack problem*, MKP):

* cada pedido é um item indivisível (`xᵢ ∈ {0,1}`);
* cada item consome duas dimensões de capacidade simultaneamente (kg e m³);
* o objetivo é maximizar um benefício agregado sem violar nenhuma dimensão.

O MKP é NP-difícil, o que justifica o uso de um solver especializado em vez de heurística própria — mas na escala deste problema (centenas de pedidos por eixo) é resolvido à otimalidade em segundos por solvers modernos. Essa caracterização é importante para a defesa técnica do projeto: ela mostra que a escolha do OR-Tools não é preferência de ferramenta, e sim consequência direta da classe do problema.

---

# 3. Escopo

## 3.1 Escopo obrigatório

O MVP deverá implementar:

1. ingestão dos arquivos fornecidos;
2. validação declarativa de schema dos arquivos de entrada;
3. limpeza e padronização dos dados;
4. filtragem de pedidos inválidos para o desafio;
5. cruzamento entre pedidos e cubagem;
6. conversão de unidades;
7. cálculo de peso e volume por pedido;
8. cálculo do score de prioridade por pedido;
9. seleção otimizada dos pedidos via CP-SAT;
10. validação independente das restrições físicas;
11. registro do motivo de inclusão/exclusão de cada pedido;
12. definição da ordem de descarga;
13. geração do plano de carga;
14. apresentação do plano em interface web;
15. edição manual controlada e auditada do plano;
16. geração de versão imprimível/assinável do plano;
17. registro das decisões e correções realizadas pelo sistema;
18. perfis de otimização configuráveis;
19. controle de acesso por papel (RBAC básico).

Os itens 2, 8, 11, 15, 18 e 19 são adições da versão 2.0.

---

# 4. Fora do escopo inicial

Não deverão fazer parte do MVP:

* rastreamento GPS em tempo real;
* aplicativo mobile para motoristas;
* integração com ERP;
* integração com sistemas fiscais;
* previsão de demanda;
* chatbot;
* LLM;
* visão computacional;
* previsão de trânsito;
* otimização dinâmica durante a viagem;
* sistema completo de TMS;
* cálculo real de frete;
* identificação de clientes;
* enriquecimento dos dados com fontes externas;
* alocação simultânea de múltiplos veículos entre múltiplos eixos (bônus — ver seção 18).

Essas funcionalidades podem ser consideradas posteriormente, caso exista necessidade operacional.

---

# 5. Premissas

A arquitetura proposta parte das seguintes premissas:

1. Os dados fornecidos pela Nobre Lar são a fonte oficial do MVP.
2. Os pedidos estão anonimizados.
3. Não deve haver tentativa de reidentificação.
4. Não devem ser adicionadas informações externas aos registros.
5. O veículo possui capacidade máxima conhecida em kg e m³.
6. Cada pedido possui ou pode receber uma cubagem a partir do código dos produtos.
7. Cada pedido pertence a uma cidade/eixo.
8. A seleção de pedidos é realizada para um eixo e veículo no fluxo principal.
9. A ordem das cidades pode ser previamente configurada.
10. O sistema precisa sempre impedir uma solução que ultrapasse peso ou volume.
11. Um pedido é indivisível: ou vai inteiro no veículo, ou não vai. *(Premissa a confirmar — pergunta 9 da seção 36; caso a operação permita fracionamento, o modelo muda de binário para inteiro e a seção 15 precisa ser revista.)*
12. Os pesos da função objetivo são parâmetros de negócio, não constantes técnicas.

A regra de não enriquecimento dos dados é especialmente importante: qualquer mecanismo externo de geocodificação deve ser tratado como uma decisão futura, não como dependência do MVP, e deve passar pelo processo de ADR descrito na seção 19.

---

# 6. Requisitos funcionais

## RF-001 — Importação dos dados

O sistema deverá permitir a importação dos arquivos de entrada utilizados no desafio.

Arquivos previstos:

* Pedidos.csv;
* Pedidos_Filtrados_Semana_1 a 4;
* Ranking_Top85_Materiais.csv;
* Dados_de_Entregas.csv.

O sistema deverá identificar erros básicos de estrutura antes de iniciar o processamento.

---

## RF-002 — Validação declarativa dos arquivos

**(Revisado na v2.0)**

A versão 1.0 listava *o que* validar, mas não *como*. A validação deverá ser **declarativa**, e não implementada como checagens dispersas no código de ingestão.

Recomendação: **Pandera** para os DataFrames de entrada e **Pydantic** para os registros já normalizados que trafegam pela API.

Exemplo de contrato:

```python
import pandera.pandas as pa
from pandera.typing import Series

class PedidoSchema(pa.DataFrameModel):
    numero_pedido:  Series[str]   = pa.Field(nullable=False, unique=False)
    codigo_produto: Series[str]   = pa.Field(nullable=False)
    quantidade:     Series[float] = pa.Field(gt=0)
    valor:          Series[float] = pa.Field(ge=0)
    cidade:         Series[str]   = pa.Field(nullable=False)
    status:         Series[str]   = pa.Field(isin=["FATURADO", "PENDENTE", "CANCELADO"])

    class Config:
        strict = "filter"      # descarta colunas não declaradas
        coerce = True          # tenta converter tipos antes de falhar
```

Vantagens sobre a validação ad hoc:

* a lista de linhas rejeitadas com o motivo (exigida por RF-016 e CA-009) é gerada automaticamente pelo próprio framework, sem código duplicado;
* o contrato de dados vira documentação executável;
* cada schema é testável isoladamente (ver seção 31).

O sistema deverá verificar:

* existência das colunas obrigatórias;
* tipos de dados;
* campos vazios;
* códigos de produto;
* valores numéricos;
* datas;
* duplicidades;
* registros inconsistentes.

Caso um **arquivo** não esteja de acordo com o formato esperado (coluna obrigatória ausente), o processamento deverá ser interrompido. Caso um **registro** individual esteja inválido, ele deverá ser descartado com motivo registrado, sem interromper o lote. Essa distinção está detalhada na seção 30.

---

## RF-003 — Limpeza dos pedidos

O sistema deverá excluir ou marcar para exclusão:

* retiradas no balcão;
* pedidos cancelados;
* entregas em Crateús.

Essas são regras explicitamente definidas no desafio.

Cada exclusão deve gerar um registro em `CleaningLog` (ver seção 11), com o pedido afetado, a regra aplicada e o valor do campo que disparou a regra.

### RF-003-B — Pré-Processamento de Fatiamento de Cargas (Order Splitting)

**(Novo na v3.0 — Resolução de Cargas Pesadas)**

A auditoria dos dados reais revelou compras de grande porte que ultrapassam 5.000 kg (ex: 100 sacos de cimento Poty no pedido `L12609291` pesando 5.387 kg), excedendo a capacidade do caminhão Accelo 815 (4.800 kg). Sob a premissa de indivisibilidade pura, o solver binário descartaria compulsoriamente os pedidos mais rentáveis da loja.

O sistema dispõe de um módulo pré-solver de fatiamento:
- Pedidos elegíveis com massa superior à capacidade útil do caminhão ($W_i > CAP_W$) são desmembrados em subpedidos vinculados:
  ```text
  Pedido Original: L12609291 (5.387,80 kg | R$ 6.328,17)
  --> Subpedido 1: L12609291-P1 (4.000,00 kg | R$ 4.700,00) [is_split = True]
  --> Subpedido 2: L12609291-P2 (1.387,80 kg | R$ 1.628,17) [is_split = True]
  ```
- Cada subpedido compete como variável binária ($x_{i,p} \in \{0, 1\}$), mantendo a formulação linear exata.

---

## RF-004 — Normalização

O sistema deverá converter:

* datas para um formato único (ISO 8601);
* peso para unidade numérica (kg);
* volume para unidade numérica (m³);
* quantidades para valores numéricos;
* unidades de venda para uma representação padronizada.

A unidade canônica interna do sistema é **kg** para peso e **m³** para volume. Qualquer conversão deve ocorrer na camada de ingestão, nunca na camada de otimização.

---

## RF-005 — Cubagem

O sistema deverá cruzar cada item do pedido com sua ficha técnica utilizando o código do produto.

Deverá calcular:

```text
peso_item   = quantidade × peso_unitário
volume_item = quantidade × volume_unitário
```

O pedido deverá receber:

```text
peso_total
volume_total
valor_total
```

### RF-005-A — Rastreabilidade da origem da cubagem

**(Novo na v2.0)**

Cada produto deve registrar a origem do seu dado de cubagem:

```text
source = "ficha_tecnica" | "ranking_top85" | "estimado" | "ausente"
```

E o plano de carga deve expor, como indicador de confiança:

```text
% do peso total do plano baseado em cubagem estimada
% do volume total do plano baseado em cubagem estimada
```

Isso é relevante porque o aprovador humano precisa saber o nível de confiança do romaneio **antes** de assinar. Um plano com 95% de ocupação calculado sobre 40% de dados estimados tem risco operacional muito diferente de um plano equivalente com cubagem integralmente conhecida.

### RF-005-B — Fallback Heurístico de Cubagem por Categoria

**(Novo na v3.0 — Resolução de Itens fora do Top 85)**

O catálogo `Ranking_Top85_Materiais.csv` cobre 85 produtos essenciais, mas existem 587 SKUs ativos faturados fora dessa lista (presentes em 51,9% dos pedidos). A exclusão de pedidos sem cubagem eliminaria metade das vendas. O sistema adota parâmetros médios de classe (conexões: 0,05 kg / 0,0003 m³; elétrica: 0,08 kg / 0,0005 m³; ferragens: 0,02 kg / 0,0001 m³; tintas: 0,30 kg / 0,0010 m³), marcando `source = "heuristica_categoria"`.

---

## RF-006 — Conversão de piso

Quando o produto estiver comercializado em m², o sistema deverá aplicar a regra de conversão definida pela ficha técnica para determinar a quantidade correspondente em caixas.

```text
caixas = ceil(quantidade_m2 / m2_por_caixa)
```

O arredondamento para cima é a hipótese conservadora do MVP: não se vende fração de caixa, e subestimar caixas subestima peso e volume — o erro mais perigoso para o sistema, porque produz um plano que parece viável e não é.

A fórmula exata e o critério de arredondamento deverão ser validados com o responsável pela operação antes da implementação definitiva (pergunta 15 da seção 36).

### RF-006-A — Restrição Linear Dimensional (Tubos e Barras de 6 Metros)

**(Novo na v3.0 — Resolução de Incompatibilidade Física)**

A base de dados possui expressivo volume de tubulações de esgoto (100mm) e água (25mm) comercializados em metros, mas expedidos em barras industriais de 6 metros, além de treliças de 6 metros. O sistema marca `has_long_items = True` para esses pedidos e inclui a restrição linear no solver CP-SAT:
$$x_i \cdot 	ext{has\_long\_items}_i \le 	ext{allows\_long\_items}_{	ext{veiculo}}$$
Impedindo que peças de 6 metros sejam alocadas em veículos sem carroceria aberta ou comprimento útil adequado.

---

## RF-007 — Seleção de pedidos

O sistema deverá selecionar automaticamente um subconjunto dos pedidos de determinado eixo.

A solução não poderá ultrapassar:

```text
peso_total   <= capacidade_peso_veiculo
volume_total <= capacidade_volume_veiculo
```

---

## RF-008 — Otimização da ocupação via CP-SAT

**(Revisado na v2.0)**

O sistema deverá buscar uma combinação de pedidos que maximize o benefício agregado da carga, utilizando o **CP-SAT solver** do Google OR-Tools (`ortools.sat.python.cp_model`).

### Por que CP-SAT e não o Knapsack solver

A versão 1.0 citava "OR-Tools" genericamente. A escolha específica importa:

| Critério | KnapsackSolver | CP-SAT |
|----------|----------------|--------|
| Multidimensional (peso + volume) | Suportado | Suportado nativamente |
| Restrições adicionais (SLA, incompatibilidade, agrupamento) | Não expressável | Restrições lineares triviais |
| Limite de tempo com melhor incumbente | Limitado | Nativo (`max_time_in_seconds`) |
| Fixar pedido obrigatório (`xᵢ = 1`) | Não | Trivial |
| Status explícito da solução | Limitado | `OPTIMAL` / `FEASIBLE` / `INFEASIBLE` |

As restrições da coluna 3 são exatamente as que as perguntas 8 a 12 da seção 36 sugerem que a operação vai pedir. Começar com CP-SAT evita reescrever o motor quando isso acontecer.

### Tratamento numérico

CP-SAT trabalha com **inteiros**. Pesos, volumes e scores devem ser escalados antes de entrar no modelo:

```text
peso_int   = round(peso_kg  × 1000)      # precisão de 1 g
volume_int = round(volume_m3 × 1_000_000) # precisão de 1 cm³
score_int  = round(score     × 10_000)    # 4 casas decimais
```

Esse detalhe é fonte comum de bug silencioso: truncar em vez de arredondar produz soluções que o solver considera válidas e a validação independente (RF-010) rejeita.

---

## RF-009 — Função objetivo

**(Reescrito na v2.0 — era o principal ponto em aberto da versão 1.0)**

A versão 1.0 propunha apenas `α × ocupação_peso + β × ocupação_volume` e deixava os pesos indefinidos. Essa formulação tem um defeito: ao tratar consumo de capacidade como benefício puro, ela premia pedidos pesados e volumosos de baixo valor, simplesmente porque ocupam mais caminhão.

A função objetivo de referência do MVP passa a ser um **score de prioridade multicritério normalizado**, combinando consumo de capacidade, valor financeiro e demanda comercial.

### 9.1 Componentes do score

Para cada pedido `i`:

```text
pᵢ = peso_i   / capacidade_peso          consumo relativo de peso
vᵢ = volume_i / capacidade_volume        consumo relativo de volume
fᵢ = log(1 + valor_i)      / log(1 + valor_max)        valor normalizado
qᵢ = log(1 + frequência_i) / log(1 + frequência_max)   demanda normalizada
```

O uso de consumo **relativo à capacidade do veículo** (em vez de peso e volume absolutos) é deliberado: faz o score depender do veículo selecionado, o que é correto — um pedido de 900 kg é restritivo em um caminhão de 3.500 kg e irrelevante em um de 20.000 kg.

A **normalização logarítmica** de valor e frequência evita que outliers dominem a seleção. Com normalização linear, um pedido de R$ 100.000 em uma base onde a mediana é R$ 3.000 achata todos os demais para perto de zero e o score deixa de discriminar.

### 9.2 Score agregado

```text
Sᵢ = w_p·pᵢ + w_v·vᵢ + w_f·fᵢ + w_q·qᵢ

sujeito a:
  w_p + w_v + w_f + w_q = 1
  0 ≤ Sᵢ ≤ 1
```

### 9.3 Modelo de otimização completo

```text
maximizar:   Σᵢ Sᵢ · xᵢ

sujeito a:   Σᵢ peso_i   · xᵢ ≤ capacidade_peso
             Σᵢ volume_i · xᵢ ≤ capacidade_volume
             xᵢ ∈ {0,1}
```

### 9.4 Separação entre score e restrição

Esta distinção é arquiteturalmente central e deve ser preservada em código:

| | Pergunta que responde | Onde vive |
|---|---|---|
| **Score** `Sᵢ` | "Quão prioritário é este pedido?" | Função objetivo |
| **Restrição** | "Este pedido cabe na carga?" | Constraints do solver |

Um score alto **não garante** seleção. A consequência prática é que o sistema **não deve** ordenar pedidos por score e inserir um a um até encher — essa heurística gulosa produz soluções subótimas. O solver avalia o conjunto globalmente.

### 9.5 Perfis padrão

| Perfil | w_peso | w_volume | w_valor | w_vendas | Quando usar |
|--------|--------|----------|---------|----------|-------------|
| Equilibrado *(padrão)* | 0,25 | 0,25 | 0,30 | 0,20 | Operação normal |
| Comercial | 0,15 | 0,15 | 0,50 | 0,20 | Fechamento de mês, meta de faturamento |
| Capacidade | 0,35 | 0,35 | 0,20 | 0,10 | Esvaziar estoque, maximizar ocupação física |

Esses valores são **pontos de partida testáveis**, não verdades do sistema. A calibração final depende das respostas da seção 36.1.

---

## RF-009-A — Score de eficiência (critério avançado)

**(Novo na v2.0)**

Como variante, o sistema deverá suportar um score que mede **benefício por unidade de capacidade consumida**:

```text
E_i = (w_f·fᵢ + w_q·qᵢ) / (w_p·pᵢ + w_v·vᵢ + ε)
```

onde `ε` é uma constante pequena que evita divisão por zero.

Interpretação: quanto valor comercial o pedido entrega por cada fração de caminhão que ele consome. Um pedido de alto valor e baixo volume tem eficiência alta; um pedido volumoso e barato tem eficiência baixa.

Uso previsto:

* modo de otimização alternativo, selecionável por perfil;
* critério de desempate entre soluções de score agregado equivalente;
* indicador analítico no relatório de decisão (seção RF-011-A), mesmo quando não usado como objetivo.

Este score **não** é o padrão do MVP porque ele ignora o objetivo declarado do desafio de maximizar ocupação física. Fica disponível como cenário comparativo.

---

## RF-009-B — Perfis de otimização configuráveis

**(Novo na v2.0)**

Os pesos não devem ser constantes no código-fonte. Devem ser uma entidade persistida, editável via API, versionada e referenciada pelo plano gerado.

```text
OptimizationProfile
--------
id
name                 ("equilibrado", "comercial", "capacidade")
w_peso
w_volume
w_valor
w_quantidade
objective_mode       ("score_agregado" | "eficiencia")
is_default
created_at
```

Validação obrigatória na criação: `w_peso + w_volume + w_valor + w_quantidade = 1` (tolerância de 1e-6).

Benefício direto para a apresentação do projeto: permite demonstrar ao vivo o mesmo eixo resolvido sob três estratégias diferentes, evidenciando que o sistema é uma ferramenta de decisão parametrizável e não uma caixa-preta com uma resposta única.

---

## RF-010 — Validação independente da solução

Antes de disponibilizar o plano, o backend deverá executar uma validação **independente do solver**:

```text
assert Σ peso_i   ≤ capacidade_peso
assert Σ volume_i ≤ capacidade_volume
assert todos os pedidos selecionados pertencem ao eixo requisitado
assert nenhum pedido selecionado está na lista de descartados pela limpeza
```

"Independente" significa: implementada em código próprio, sem consultar o solver, operando sobre o resultado final. Se o solver tiver bug ou o escalonamento numérico (RF-008) introduzir erro de arredondamento, esta camada é a que impede um plano inválido de chegar à expedição.

Uma solução inválida jamais poderá ser enviada para a expedição, nem persistida como plano aprovável.

---

## RF-011 — Cálculo dos indicadores

O sistema deverá apresentar:

* quantidade de pedidos;
* valor total;
* peso total;
* volume total;
* ocupação de peso;
* ocupação de volume;
* capacidade restante em kg;
* capacidade restante em m³;
* recurso limitante do plano (peso ou volume);
* percentual do plano baseado em cubagem estimada;
* status do solver e tempo de otimização.

---

## RF-011-A — Relatório de decisão do solver

**(Novo na v2.0)**

O sistema deverá registrar não apenas quais pedidos entraram, mas **por que os demais ficaram de fora**.

```text
LoadPlanDecision
--------
id
load_plan_id
order_id
included            (bool)
score               (Sᵢ calculado)
efficiency          (Eᵢ calculado)
peso_pct            (consumo relativo de peso)
volume_pct          (consumo relativo de volume)
exclusion_reason
```

Valores possíveis de `exclusion_reason`:

| Código | Significado |
|--------|-------------|
| `SELECIONADO` | Incluído na carga |
| `EXCEDE_PESO_INDIVIDUAL` | Pedido isolado ultrapassa a capacidade de peso do veículo |
| `EXCEDE_VOLUME_INDIVIDUAL` | Pedido isolado ultrapassa a capacidade volumétrica |
| `SEM_CUBAGEM` | Produto sem ficha técnica — pendente de validação |
| `NAO_SELECIONADO_SOLVER` | Elegível, mas não compôs a solução ótima |
| `REMOVIDO_LIMPEZA` | Descartado antes da otimização (cancelado, balcão, Crateús) |
| `REMOVIDO_MANUALMENTE` | Retirado pelo operador na edição do plano |

Justificativa: a meta do projeto é substituir 40–60 minutos de decisão humana. Um coordenador só troca sua decisão pela do sistema se conseguir auditar por que o pedido que ele esperava ver na carga não está lá. Sem isso, o sistema é rejeitado na operação mesmo estando matematicamente correto.

---

## RF-012 — Ordem de descarga

O sistema deverá organizar os pedidos de acordo com a ordem das cidades do eixo.

A ordem oficial das cidades deverá ser configurável, persistida no campo `City.delivery_order`.

O desafio informa que a ordem das cidades de cada eixo é uma decisão a ser proposta pelas equipes. Portanto, o MVP não deve assumir automaticamente que uma rota calculada externamente representa a ordem operacional correta.

Regra de carregamento: a ordem física de carregamento do caminhão é o **inverso** da ordem de descarga — a primeira cidade a ser atendida deve ser a última a ser carregada. O plano deve apresentar as duas listas.

---

## RF-013 — Plano de carga

O sistema deverá gerar um plano contendo, no mínimo:

* identificação do eixo;
* identificação do veículo;
* data e ID de execução;
* perfil de otimização utilizado e seus pesos;
* pedidos selecionados;
* cidade;
* valor;
* peso;
* volume;
* ocupação;
* ordem de descarga;
* ordem de carregamento;
* totais;
* indicador de confiança da cubagem;
* campo de assinatura do responsável.

---

## RF-013-A — Edição manual controlada

**(Novo na v2.0)**

É praticamente certo que a operação vai querer remover ou incluir um pedido manualmente antes de assinar. Sem esse recurso, o plano automático vira uma proposta do tipo "aceite tudo ou descarte tudo", o que é o padrão clássico de rejeição de sistemas de otimização pela operação.

```text
POST /api/load-plans/{id}/items/{order_id}/toggle
```

Comportamento obrigatório:

1. Recalcula totais de peso, volume e valor.
2. Reexecuta a validação independente (RF-010).
3. **Rejeita a alteração** se ela violar qualquer capacidade — retorna `409 Conflict` com o motivo. Nunca permite persistir um plano inválido.
4. Registra a tentativa em auditoria, inclusive quando rejeitada.
5. Marca o plano como `modificado_manualmente = true`, preservando o resultado original do solver para comparação.

```text
LoadPlanAudit
--------
id
load_plan_id
user_id
action              ("ADD_ORDER" | "REMOVE_ORDER" | "APPROVE" | "REJECT")
order_id
accepted            (bool)
rejection_reason
weight_before / weight_after
volume_before / volume_after
created_at
```

---

## RF-014 — Exportação

O plano deverá poder ser:

* visualizado na aplicação;
* impresso;
* exportado para PDF.

Opção recomendada para geração do PDF no backend: **WeasyPrint**, que gera PDFs a partir de HTML/CSS e possui licença BSD. Isso evita implementar manualmente um mecanismo de composição de documentos e permite reaproveitar o mesmo HTML/CSS da visualização web.

O PDF deve conter o ID de execução e o hash da configuração usada, de modo que qualquer romaneio impresso seja rastreável até a execução que o gerou.

---

## RF-015 — Histórico da execução

Cada plano deverá possuir informações mínimas de rastreabilidade:

```text
ID da execução
data/hora
eixo
veículo
perfil de otimização (id + snapshot dos pesos)
quantidade de pedidos analisados
quantidade selecionada
peso / volume / ocupação
status do solver
gap de otimalidade
duração da otimização
versão do algoritmo
```

O **snapshot dos pesos** é obrigatório, não apenas o `profile_id`. Se o perfil for editado depois, sem o snapshot torna-se impossível reproduzir uma execução passada — o que violaria RNF-003.

---

## RF-016 — Registro da limpeza

O sistema deverá registrar as principais correções realizadas.

```text
CleaningLog
--------
id
execution_id
record_reference    (pedido / linha do arquivo)
rule_applied
action              ("REMOVIDO" | "CORRIGIDO" | "MARCADO_REVISAO")
field
original_value
corrected_value
reason
```

Exemplo:

```text
Pedido 1234
Regra: pedido cancelado
Ação: removido
Campo: status
Valor original: CANCELADO
Motivo: regra de negócio do desafio — pedidos cancelados não compõem carga
```

Isso atende à exigência de que cada correção seja explicada por um critério (CA-009).

---

## RF-017 — Controle de acesso

**(Novo na v2.0)**

RBAC simples, três papéis:

| Papel | Permissões |
|-------|-----------|
| `operador` | Importar dados, gerar plano, visualizar |
| `aprovador` | Tudo do operador + editar plano manualmente + aprovar + assinar |
| `admin` | Tudo + gerenciar veículos, eixos, cidades e perfis de otimização |

Autenticação por JWT. Mesmo no MVP, isso é barato de implementar e responde diretamente às perguntas 32–34 da seção 36.6, além de dar sentido operacional à auditoria de RF-013-A — auditoria sem identificação de usuário não é auditoria.

---

# 7. Requisitos não funcionais

## RNF-001 — Desempenho

```text
tempo total de geração do plano < 5 minutos
```

Objetivo interno para operação normal: **inferior a 30 segundos** fim a fim.

### RNF-001-A — Time budget e degradação graciosa

**(Novo na v2.0)**

A versão 1.0 assumia implicitamente que o solver sempre converge. Isso precisa de tratamento explícito:

```python
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)
```

Comportamento por status:

| Status | Ação |
|--------|------|
| `OPTIMAL` | Usar solução; registrar `gap = 0` |
| `FEASIBLE` | Usar melhor incumbente; registrar gap; sinalizar no plano |
| `INFEASIBLE` | Nenhuma combinação válida — investigar dados (ver seção 30) |
| `UNKNOWN` / timeout sem incumbente | Acionar fallback heurístico |

Fallback heurístico (plano de contingência):

```text
ordenar pedidos por Eᵢ = Sᵢ / (consumo de capacidade) decrescente
para cada pedido:
    se couber em peso E volume: incluir
plano marcado como algorithm_version = "greedy-fallback-v1"
```

O fallback nunca produz solução ótima, mas produz uma solução **válida** — e uma solução válida em 2 segundos é infinitamente melhor que uma tela travada durante uma demonstração ao vivo ou um turno de expedição.

---

## RNF-002 — Segurança

O sistema deverá:

* não armazenar dados pessoais desnecessários;
* não tentar reidentificar registros;
* validar arquivos de entrada;
* restringir operações administrativas via RBAC (RF-017);
* utilizar HTTPS em produção;
* manter credenciais fora do código-fonte (variáveis de ambiente / secrets);
* limitar tamanho e tipo de arquivo aceito no upload;
* registrar tentativas de acesso não autorizado.

### RNF-002-A — Barreira de reidentificação

**(Novo na v2.0)**

Qualquer camada futura de geocodificação ou enriquecimento externo (Fase 3, seção 19) deve passar por **revisão explícita de risco de reidentificação** antes de ir para produção, e essa decisão deve ficar registrada como **ADR** (Architecture Decision Record) versionado no repositório.

Motivo: a premissa 4 protege os dados hoje, mas premissas em documentos estáticos são esquecidas. Um desenvolvedor futuro que plugue geocodificação de endereços de entrega pode, sem má-fé, tornar reidentificável um conjunto que o desafio entregou anonimizado. O ADR força a decisão a ser consciente e registrada.

Formato mínimo do ADR: contexto, decisão, alternativas consideradas, consequências, status, data, responsável. Armazenados em `docs/adr/NNNN-titulo.md`.

---

## RNF-003 — Rastreabilidade

Toda solução deverá ser reproduzível a partir de:

* dados de entrada (arquivos originais preservados);
* configuração do veículo;
* perfil de otimização (snapshot dos pesos);
* semente aleatória do solver, quando aplicável;
* versão do algoritmo;
* data da execução.

Critério prático: reexecutar a mesma entrada com a mesma configuração deve produzir o mesmo plano. Em caso de múltiplos ótimos equivalentes, o desempate deve ser determinístico (por `order_id` crescente), nunca arbitrário.

---

## RNF-004 — Consistência

Uma solução gerada pelo sistema deverá ser matematicamente válida. Não poderá existir `peso > capacidade` nem `volume > capacidade`, em nenhuma circunstância — nem após edição manual, nem em fallback heurístico, nem em caso de erro do solver.

O desafio estabelece explicitamente zero cargas acima dos limites físicos como requisito do MVP.

---

## RNF-005 — Manutenibilidade

O sistema deverá separar:

```text
ingestão → validação → limpeza → cubagem → scoring → otimização → validação → ordenação → plano
```

Regra arquitetural: a camada de otimização recebe apenas estruturas já normalizadas (`peso_kg`, `volume_m3`, `score`) e não conhece CSV, unidades de venda nem regras de negócio de limpeza. Isso permite trocar o solver sem tocar no pipeline de dados, e vice-versa.

---

## RNF-006 — Observabilidade

O backend deverá registrar erros, tempo de processamento, quantidade de registros processados e descartados, motivo dos descartes e tempo gasto na otimização.

### RNF-006-A — Health check e métricas de qualidade

**(Novo na v2.0)**

```text
GET /api/health     → status do serviço e da conexão com o banco
GET /api/ready      → readiness probe (migrations aplicadas, solver disponível)
```

Além das métricas de execução, registrar métricas de **qualidade da solução**:

```text
optimality_gap          (distância entre solução e limite superior do solver)
ocupacao_combinada      (média ponderada de peso e volume)
recurso_limitante       ("peso" | "volume")
capacidade_ociosa_kg
capacidade_ociosa_m3
```

Isso dá um número objetivo de "quão boa" é a solução, não apenas "quão rápida" — indicador que fortalece bastante a defesa do projeto perante a banca.

---

## RNF-007 — Portabilidade

A aplicação deverá ser executável através de containers Docker, com `docker compose up` suficiente para subir o ambiente completo.

---

## RNF-008 — Open Source

Sempre que existir uma solução open source adequada, ela deverá ser preferida a uma implementação própria.

---

## RNF-009 — Qualidade de código e integração contínua

**(Novo na v2.0)**

Pipeline mínimo em GitHub Actions:

```yaml
jobs:
  quality:
    - ruff check .          # lint
    - ruff format --check . # formatação
    - mypy app/             # verificação de tipos
    - pytest --cov=app      # testes + cobertura
  build:
    - docker build          # valida que a imagem compila
```

Meta de cobertura para os módulos críticos (`cubing`, `scoring`, `optimizer`, `validation`): **mínimo 80%**. Para os demais, sem meta formal.

Justificativa: o documento declara como objetivo a "possibilidade de implantação posterior na operação real". CI é barato e é exatamente o que separa um MVP que roda na máquina do autor de um sistema que outra pessoa consegue manter.

---

# 8. Arquitetura proposta

```text
                         ┌──────────────────────┐
                         │      React + TS      │
                         │       Frontend       │
                         └──────────┬───────────┘
                                    │ HTTP/JSON + JWT
                                    ▼
                         ┌──────────────────────┐
                         │       FastAPI        │
                         │       Backend        │
                         └──────────┬───────────┘
                                    │
      ┌──────────┬──────────┬───────┴───────┬──────────┬──────────┐
      ▼          ▼          ▼               ▼          ▼          ▼
   Ingestão   Limpeza   Cubagem         Scoring   Optimizer   Plan Gen
      │          │          │               │          │          │
   Pandera    Pandas    Pandas          NumPy     OR-Tools   HTML+PDF
      │          │          │               │       CP-SAT   WeasyPrint
      └──────────┴──────────┴───────┬───────┴──────────┴──────────┘
                                    ▼
                            Validação independente
                                    │
                                    ▼
                               PostgreSQL
```

Pontos de atenção arquitetural:

* **Scoring é um módulo separado do Optimizer.** O score é uma regra de negócio; a otimização é uma técnica. Misturá-los torna impossível testar um sem o outro e dificulta trocar o solver.
* **Validação independente fica fora do Optimizer**, propositalmente, para não herdar eventuais bugs dele.

---

# 9. Backend

## 9.1 Tecnologia

```text
Python 3.11+
FastAPI            API e validação por type hints
Pydantic v2        contratos de dados
Pandas ou Polars   manipulação tabular
Pandera            validação declarativa de schema
OR-Tools (CP-SAT)  otimização combinatória
SQLAlchemy 2.x     ORM
Alembic            migrations
PostgreSQL 15+     persistência
WeasyPrint         geração de PDF
python-jose        JWT
Pytest             testes
Ruff + mypy        lint e tipos
structlog          logging estruturado
```

FastAPI é particularmente adequado porque utiliza type hints do Python para validação e geração automática de documentação OpenAPI, que serve diretamente como contrato para o frontend TypeScript.

---

# 10. Organização do backend

```text
backend/
│
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py
│   │   │   ├── uploads.py
│   │   │   ├── loads.py
│   │   │   ├── vehicles.py
│   │   │   ├── profiles.py          ← perfis de otimização (v2.0)
│   │   │   └── reports.py
│   │   └── dependencies.py
│   │
│   ├── domain/
│   │   ├── models/
│   │   │   ├── order.py
│   │   │   ├── product.py
│   │   │   ├── vehicle.py
│   │   │   ├── load_plan.py
│   │   │   └── optimization_profile.py   ← v2.0
│   │   │
│   │   ├── schemas/                      ← contratos Pandera (v2.0)
│   │   │   ├── pedidos_schema.py
│   │   │   └── materiais_schema.py
│   │   │
│   │   └── services/
│   │       ├── cleaning.py
│   │       ├── cubing.py
│   │       ├── scoring.py                ← v2.0 (isolado do solver)
│   │       ├── optimizer.py
│   │       ├── fallback.py               ← heurística gulosa (v2.0)
│   │       ├── validation.py             ← validação independente (v2.0)
│   │       ├── routing.py
│   │       └── load_plan.py
│   │
│   ├── infrastructure/
│   │   ├── database/
│   │   ├── repositories/
│   │   └── security/                     ← JWT / RBAC (v2.0)
│   │
│   └── main.py
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── load/                             ← testes de carga (v2.0)
├── docs/adr/                             ← decisões arquiteturais (v2.0)
├── requirements.txt
└── Dockerfile
```

A divisão é propositalmente simples. Não é necessário adotar microsserviços para este projeto.

---

# 11. Banco de dados

```text
User                          Vehicle
--------                      --------
id                            id
username                      name
password_hash                 capacity_kg
role                          capacity_m3
created_at                    active


Axis                          City
--------                      --------
id                            id
name                          name
active                        axis_id
                              delivery_order


Order                         OrderItem
--------                      --------
id                            id
external_id                   order_id
axis_id                       product_code
city_id                       quantity
value                         unit
status                        computed_weight_kg
delivery_status               computed_volume_m3
date
total_weight_kg
total_volume_m3
sale_frequency


Product                       OptimizationProfile        ← v2.0
--------                      --------
code                          id
description                   name
unit                          w_peso
weight_kg                     w_volume
volume_m3                     w_valor
m2_per_box                    w_quantidade
estimated                     objective_mode
source                        is_default


LoadPlan                      LoadPlanItem
--------                      --------
id                            id
execution_id                  load_plan_id
axis_id                       order_id
vehicle_id                    delivery_order
profile_id                    loading_order
profile_snapshot (JSON)       score
created_at                    
created_by                    
total_value                   LoadPlanDecision          ← v2.0
total_weight                  --------
total_volume                  id
weight_occupancy              load_plan_id
volume_occupancy              order_id
limiting_resource             included
estimated_cubing_pct          score / efficiency
solver_status                 peso_pct / volume_pct
optimality_gap                exclusion_reason
solve_duration_ms
algorithm_version             LoadPlanAudit             ← v2.0
manually_modified             --------
approved_by                   id
approved_at                   load_plan_id
                              user_id
CleaningLog                   action
--------                      order_id
id                            accepted
execution_id                  rejection_reason
record_reference              weight_before/after
rule_applied                  volume_before/after
action                        created_at
field
original_value
corrected_value
reason
```

Índices recomendados: `Order(axis_id, status, date)`, `OrderItem(order_id)`, `OrderItem(product_code)`, `LoadPlanDecision(load_plan_id)`.

---

# 12. Motor de otimização

## 12.1 Modelo formal

Variável de decisão binária por pedido:

```text
xᵢ ∈ {0,1}      xᵢ = 1 → pedido selecionado
                xᵢ = 0 → pedido não selecionado
```

Restrições:

```text
Σᵢ (peso_i   × xᵢ) ≤ capacidade_peso
Σᵢ (volume_i × xᵢ) ≤ capacidade_volume
```

Função objetivo:

```text
maximizar Σᵢ (Sᵢ × xᵢ)
```

## 12.2 Implementação de referência

```python
from ortools.sat.python import cp_model

def solve_load(orders, capacity_kg, capacity_m3, time_limit=30.0):
    model = cp_model.CpModel()

    # escalonamento para inteiros
    W = [round(o.weight_kg * 1000) for o in orders]
    V = [round(o.volume_m3 * 1_000_000) for o in orders]
    S = [round(o.score * 10_000) for o in orders]

    CAP_W = round(capacity_kg * 1000)
    CAP_V = round(capacity_m3 * 1_000_000)

    x = [model.NewBoolVar(f"x_{o.id}") for o in orders]

    model.Add(sum(W[i] * x[i] for i in range(len(orders))) <= CAP_W)
    model.Add(sum(V[i] * x[i] for i in range(len(orders))) <= CAP_V)

    # pedidos obrigatórios (SLA), quando existirem
    for i, o in enumerate(orders):
        if o.mandatory:
            model.Add(x[i] == 1)

    model.Maximize(sum(S[i] * x[i] for i in range(len(orders))))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)

    return status, solver, x
```

## 12.3 Extensões já suportadas pelo modelo

Por usar CP-SAT, as seguintes regras — prováveis nas respostas da seção 36 — entram como restrições adicionais sem reescrita do motor:

| Regra de negócio | Restrição |
|------------------|-----------|
| Pedido com SLA é obrigatório | `x_i = 1` |
| Pedidos do mesmo cliente viajam juntos | `x_i = x_j` |
| Produtos incompatíveis não viajam juntos | `x_i + x_j ≤ 1` |
| Ocupação mínima aceitável | `Σ peso_i·x_i ≥ 0.7 × cap_peso` |
| Limite de pedidos por carga | `Σ x_i ≤ N` |
| Pedido excluído manualmente | `x_i = 0` |

Esta é a principal justificativa técnica para CP-SAT em vez do Knapsack solver puro.

---

# 13. Peso versus volume

O desafio possui um bônus específico para identificar se determinado eixo é limitado predominantemente por peso ou volume.

```text
ocupacao_peso   = peso_total   / capacidade_peso
ocupacao_volume = volume_total / capacidade_volume

gap_peso   = 1 - ocupacao_peso
gap_volume = 1 - ocupacao_volume

recurso_limitante = "peso" se ocupacao_peso > ocupacao_volume senão "volume"
```

## 13.1 Análise de perfil do eixo

**(Expandido na v2.0)**

Além do plano individual, o sistema deverá calcular a **densidade média** dos pedidos por eixo:

```text
densidade_eixo = Σ peso_i / Σ volume_i          (kg/m³)
densidade_veiculo = capacidade_peso / capacidade_volume
```

Interpretação direta:

* `densidade_eixo > densidade_veiculo` → o eixo é **limitado por peso**: o caminhão atinge o limite de kg com espaço sobrando;
* `densidade_eixo < densidade_veiculo` → o eixo é **limitado por volume**: o caminhão enche fisicamente antes de atingir o peso máximo.

Valor operacional: se um eixo é sistematicamente limitado por volume, comprar caminhões com maior capacidade de carga em kg não resolve nada — a decisão correta é aumentar o baú. Esse é um insight de negócio concreto extraível dos dados, e um diferencial forte para a apresentação.

---

# 14. Ordenação de Descarga, Geocodificação (GeoPy / OSM) e Caixeiro Viajante (TSP)

**(Reformulado na v3.0 — Geocodificação Open Source e Otimização de Rota Integradas)**

O sistema integra a resolução do **Problema do Caixeiro Viajante (TSP - Traveling Salesperson Problem)** para encontrar a ordem ótima de entrega entre as cidades atendidas pela carga selecionada, minimizando a distância total percorrida e o tempo de tráfego a partir do Centro de Distribuição em Crateús.

## 14.1 Arquitetura de Geocodificação Open Source (GeoPy + OpenStreetMap)

Para operar sem custo de licenças comerciais de mapas e com total aderência ao open source:
1. **Biblioteca GeoPy:** Interface oficial com o geocodificador **Nominatim (OpenStreetMap)**.
2. **Políticas de Acesso Responsável:** Configurado com `RateLimiter(min_delay_seconds=1.1)` e `User-Agent` institucional, respeitando os termos de uso do OpenStreetMap.
3. **Cache Local no Banco de Dados:** Coordenadas obtidas são armazenadas nas colunas `latitude` e `longitude` da tabela `cities`.
4. **Fallback Offline Garantido:** Tabela estática com as coordenadas oficiais das 24 localidades da macrorregião de Crateús e Piauí (Buriti dos Montes, Ipaporanga, Poranga, Nova Russas, Sucesso, Tamboril, Independência, Novo Oriente, Realejo, etc.) e do CD Matriz (`-5.1784, -40.6775`).

## 14.2 Cálculo da Matriz de Distâncias Viárias

A matriz de distâncias $K 	imes K$ entre o CD (nó 0) e as cidades de entrega é gerada:
- **Modo Online:** Consulta à API pública do **OSRM (Open Source Routing Machine)** retornando as distâncias exatas pelas rodovias BR-226, CE-187 e CE-265.
- **Modo Offline:** Fórmula de **Haversine** com Fator de Tortuosidade Rodoviária do Sertão de Crateús:
  $$d_{	ext{rodovia}} = d_{	ext{haversine}} 	imes 1,28$$

## 14.3 Otimizador TSP com OR-Tools Routing API

Utiliza o módulo de roteirização do Google OR-Tools (`pywrapcp.RoutingModel`):

```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

def solve_tsp_route(distance_matrix: list[list[int]], depot_index: int = 0) -> dict:
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx, to_idx):
        return distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = 5

    solution = routing.SolveWithParameters(search_params)
    # Extrai rota otimizada e distância total
    ...
```

## 14.4 Sequenciamento LIFO na Doca (Last In, First Out)

A partir da sequência ótima gerada pelo Caixeiro Viajante:
- **Ordem de Descarga:** CD (Crateús) $\to$ Parada 1 $\to$ Parada 2 $\to$ Parada 3 $\to$ Retorno CD.
- **Ordem de Carregamento na Doca (Inversa):** Parada 3 (fundo do baú) $\to$ Parada 2 (meio) $\to$ Parada 1 (porta do caminhão).

---

# 15. Frontend

```text
React 18
TypeScript
Vite
React Router
TanStack Query
Tailwind CSS
Zod                 (validação dos contratos da API)
openapi-typescript  (geração de tipos a partir do OpenAPI do FastAPI)
```

`openapi-typescript` é uma adição da v2.0: gera automaticamente os tipos TypeScript a partir do schema OpenAPI que o FastAPI já expõe, eliminando a duplicação manual de contratos entre backend e frontend e prevenindo a classe de bug mais comum em projetos de hackathon — o frontend esperar um campo que o backend renomeou.

A interface deverá ser operacional, não um dashboard excessivamente complexo.

---

# 16. Telas do MVP

## Tela 1 — Dashboard

Número de pedidos, pedidos válidos, pedidos descartados, eixos, veículos, última execução, tempo de processamento.

## Tela 2 — Preparação

```text
Selecionar eixo
Selecionar veículo
Selecionar lote
Selecionar perfil de otimização     ← v2.0
```

Exibe: pedidos disponíveis, peso disponível, volume disponível, valor disponível, e uma prévia da densidade do eixo (seção 13.1).

## Tela 3 — Otimização

```text
GERAR PLANO DE CARGA

Validando dados...
Calculando cubagem...
Calculando scores...
Executando otimização...
Validando restrições...
Gerando plano...
```

## Tela 4 — Resultado

```text
EIXO 3 — VEÍCULO: Caminhão 02
Perfil: Equilibrado (0,25 / 0,25 / 0,30 / 0,20)

Pedidos: 27
Valor: R$ 185.420,50

Peso:    18.400 / 20.000 kg    92,0%
Volume:  48,2 / 50,0 m³        96,4%

Recurso limitante: VOLUME
Cubagem estimada: 12% do volume total
Solver: OPTIMAL — 1,42s — gap 0%
```

Ordem de descarga, com possibilidade de remover pedido (RF-013-A) e feedback imediato do impacto em peso/volume.

## Tela 5 — Pedidos não selecionados

**(Nova na v2.0)**

Lista dos pedidos elegíveis que ficaram de fora, com score, consumo de capacidade e motivo da exclusão (RF-011-A). Permite ao aprovador incluir manualmente um pedido — sujeito à revalidação de capacidade.

Esta tela é o que transforma o sistema de "caixa-preta" em "ferramenta de apoio à decisão", e é provavelmente o maior ganho de adoção por custo de implementação de todo o projeto.

## Tela 6 — Auditoria

Histórico de execuções, log de limpeza e trilha de alterações manuais.

---

# 17. Geração do romaneio

O frontend deverá permitir visualizar, imprimir e exportar em PDF.

O PDF deverá utilizar a mesma representação HTML/CSS da visualização web, gerada por WeasyPrint, e conter:

* cabeçalho com eixo, veículo, data e ID de execução;
* tabela de pedidos por cidade na ordem de descarga;
* totais e percentuais de ocupação;
* indicador de cubagem estimada;
* campos de assinatura (conferente e motorista);
* rodapé com hash da configuração para rastreabilidade.

---

# 18. Estratégia para o bônus multieixo

O MVP resolve `1 eixo + 1 veículo`. Somente depois deverá ser implementado `5 eixos + 4 caminhões`.

## 18.1 Escalabilidade e decomposição

**(Novo na v2.0)**

No MVP, o modelo tem `N` variáveis binárias (N = pedidos elegíveis do eixo). Com centenas de pedidos, CP-SAT resolve à otimalidade em segundos.

No cenário multieixo, o modelo passa a ter `N × M` variáveis (`x_{i,v}` = pedido `i` no veículo `v`), mais restrições de atribuição única:

```text
Σ_v x_{i,v} ≤ 1                          cada pedido em no máximo um veículo
Σ_i peso_i · x_{i,v} ≤ cap_peso_v        por veículo
Σ_i volume_i · x_{i,v} ≤ cap_volume_v    por veículo
```

Se o crescimento do espaço de busca inviabilizar a resolução monolítica dentro do time budget, a estratégia recomendada é **decomposição em duas fases**:

```text
Fase A — atribuir veículos a eixos (problema pequeno: 4 × 5)
Fase B — resolver o MKP de cada par (eixo, veículo) independentemente
Fase C — rebalancear: mover pedidos entre veículos com capacidade ociosa
```

Isso não garante o ótimo global, mas é tratável, explicável e suficiente para o objetivo operacional.

---

# 19. MLOps e ML

## 19.1 Não utilizar ML no MVP

> Não utilizar machine learning para resolver o problema principal.

O desafio possui regras determinísticas claras. Um modelo de ML não é necessário para a tarefa, e a solução com OR-Tools é determinística, explicável, auditável, reproduzível, mais simples de validar e mais fácil de apresentar à operação.

Formalizar essa decisão como **ADR-0001** no repositório, para que ela seja uma escolha documentada e não uma omissão.

## 19.2 Onde ML poderá ser utilizado futuramente

| Problema | Por que justifica ML |
|----------|---------------------|
| Previsão de demanda por eixo | Componente temporal e estocástico real |
| Estimativa de tempo de entrega | Depende de fatores não modeláveis deterministicamente |
| Previsão de ocupação futura | Suporta planejamento de frota |
| Estimativa de cubagem faltante | Regressão sobre produtos similares (resolve RF-005-A) |

O último caso é o mais interessante a curto prazo: prever peso/volume de produtos sem ficha técnica a partir de produtos da mesma categoria reduz diretamente o percentual de cubagem estimada — mas o modelo deve alimentar o campo `estimated = true`, e a decisão final continua sendo do otimizador determinístico.

## 19.3 MLOps mínimo, se e quando houver ML

```text
Git → training script → MLflow (tracking + registry) → modelo versionado → FastAPI
```

Para o início: MLflow local + SQLite é suficiente. Não é necessário Kubernetes, Kubeflow, Airflow, feature store, serving dedicado, GPU ou pipelines distribuídos.

---

# 20. LLM

Não há justificativa técnica para utilizar LLM no MVP. O sistema não precisa conversar, interpretar linguagem natural, gerar decisões, resumir documentos ou responder perguntas abertas.

Adicionar um LLM ao problema de otimização aumentaria custo, complexidade, superfície de falhas e dificuldade de auditoria.

Caso futuramente exista necessidade de interface conversacional:

```text
Usuário → LLM → API estruturada → Motor de otimização
```

O LLM atuaria apenas como camada de tradução de intenção ("monte a carga do eixo 3 priorizando valor") para parâmetros da API (`axis_id=3, profile=comercial`). **O LLM não deverá determinar diretamente quais pedidos cabem no caminhão.**

Registrar como **ADR-0002**.

---

# 21. API proposta

```text
POST   /api/auth/login

POST   /api/uploads
GET    /api/axes
GET    /api/vehicles
GET    /api/orders                        filtros: axis, status, city, date

GET    /api/optimization-profiles                        ← v2.0
POST   /api/optimization-profiles                        ← v2.0

POST   /api/load-plans/optimize
GET    /api/load-plans/{id}
GET    /api/load-plans/{id}/decisions                    ← v2.0
POST   /api/load-plans/{id}/items/{order_id}/toggle      ← v2.0
POST   /api/load-plans/{id}/approve                      ← v2.0
GET    /api/load-plans/{id}/pdf
GET    /api/load-plans/{id}/audit                        ← v2.0

GET    /api/executions/{id}/cleaning-log                 ← v2.0
GET    /api/analytics/axis-profile                       ← v2.0 (peso × volume)

GET    /api/health
GET    /api/ready
```

## POST `/api/load-plans/optimize`

Entrada:

```json
{
  "axis_id": 1,
  "vehicle_id": 2,
  "profile_id": 1,
  "time_limit_seconds": 30,
  "mandatory_order_ids": [1023, 1044]
}
```

Resposta:

```json
{
  "load_plan_id": 123,
  "execution_id": "2026-001",
  "total_orders": 27,
  "total_value": 185420.50,
  "total_weight_kg": 18400,
  "total_volume_m3": 48.2,
  "weight_occupancy": 0.920,
  "volume_occupancy": 0.964,
  "limiting_resource": "volume",
  "estimated_cubing_pct": 0.12,
  "solver_status": "OPTIMAL",
  "optimality_gap": 0.0,
  "solve_duration_ms": 1420,
  "algorithm_version": "cpsat-v2.0",
  "profile_snapshot": {
    "w_peso": 0.25, "w_volume": 0.25,
    "w_valor": 0.30, "w_quantidade": 0.20
  },
  "valid": true
}
```

---

# 22. Fluxo completo de processamento

```text
        ARQUIVOS
           │
           ▼
  Validação de schema (Pandera)  ──► arquivo inválido: BLOQUEIA
           │
           ▼
       Limpeza  ──────────────────► CleaningLog
           │
           ▼
      Padronização
           │
           ▼
        Cubagem  ─────────────────► sem ficha: PENDENTE
           │
           ▼
   Cálculo de scores (Sᵢ, Eᵢ)
           │
           ▼
   Pedidos por eixo + veículo + perfil
           │
           ▼
    CP-SAT Solver (time budget)
           │
     ┌─────┴─────┐
     ▼           ▼
 OPTIMAL/     timeout
 FEASIBLE        │
     │           ▼
     │      Fallback guloso
     └─────┬─────┘
           ▼
  Validação independente  ────────► inválido: ABORTA
           │
           ▼
  Registro de decisões (incluídos e excluídos)
           │
           ▼
  Ordem de descarga / carregamento
           │
           ▼
     Plano de carga
           │
     ┌─────┼─────┐
     ▼     ▼     ▼
 Frontend Edição PDF
           │
           ▼
      Aprovação + assinatura
```

---

# 23. Tratamento de erros

| Situação | Exemplo | Resultado |
|----------|---------|-----------|
| Erro de estrutura do arquivo | Coluna `codigo_produto` ausente | Processamento **bloqueado** |
| Registro inválido | `peso = "abc"` | Registro descartado, motivo registrado |
| Produto sem cubagem | Produto 123 não encontrado | Pedido marcado `SEM_CUBAGEM`, excluído da otimização, listado ao operador |
| Pedido maior que o veículo | `peso_pedido > capacidade` | Excluído com motivo `EXCEDE_PESO_INDIVIDUAL`, informado explicitamente |
| Solver INFEASIBLE | Pedidos obrigatórios não cabem juntos | Erro explicando qual restrição é inviável |
| Solver timeout | Instância grande demais | Fallback guloso, plano marcado como heurístico |
| Edição manual inválida | Adicionar pedido que estoura volume | `409 Conflict`, alteração rejeitada e auditada |

Princípio geral: **nunca assumir peso ou volume ausente**. Um pedido sem cubagem confiável fica fora da carga e visível ao operador, em vez de entrar com valor estimado silencioso.

---

# 24. Estratégia de testes

## 24.1 Testes unitários

Conversão de unidades, cálculo de peso, cálculo de volume, conversão m²→caixas, filtros de limpeza, cálculo de ocupação, cálculo do score, normalização logarítmica, validação de capacidade.

Casos de borda obrigatórios do score:

```text
valor_max = valor_min       → evitar divisão por zero na normalização
frequência = 0              → log(1+0) = 0, válido
pedido com peso 0           → não deve gerar score indefinido
soma dos pesos ≠ 1          → perfil deve ser rejeitado na criação
```

## 24.2 Testes do otimizador

```text
Caso 1 — capacidade = 100 kg; pedidos = 30, 40, 50
         verificar que 30+40+50=120 é rejeitado
         verificar que o solver encontra 40+50=90 ou 30+50=80 conforme score

Caso 2 — duas dimensões: cap_peso = 100, cap_volume = 100
         pedido pesado-e-pouco-volumoso vs leve-e-volumoso

Caso 3 — pedido individual maior que o veículo → excluído com motivo correto

Caso 4 — todos os pedidos cabem → todos selecionados

Caso 5 — pedido obrigatório (x_i = 1) respeitado

Caso 6 — pedidos obrigatórios conflitantes → INFEASIBLE tratado
```

## 24.3 Teste de invariantes

**Obrigatório e independente do solver.** Toda solução, em qualquer caminho de código (solver ótimo, fallback ou pós-edição manual), deve satisfazer:

```text
peso   ≤ capacidade_peso
volume ≤ capacidade_volume
nenhum pedido duplicado
nenhum pedido de outro eixo
nenhum pedido descartado na limpeza
```

Recomenda-se **property-based testing** (Hypothesis) gerando conjuntos aleatórios de pedidos e capacidades, verificando que os invariantes valem sempre. Isso cobre casos que testes escritos à mão não alcançam.

## 24.4 Teste de carga

**(Novo na v2.0)**

Gerar instâncias sintéticas com volume realista de pedidos por eixo (por exemplo 100, 500, 1.000 e 2.000 pedidos elegíveis) e medir:

```text
tempo até primeira solução viável
tempo até prova de otimalidade
gap ao atingir o time budget
uso de memória
```

Sem isso, a meta de RNF-001 está validada apenas contra o exemplo didático de três pedidos — o que não prova nada sobre a operação real.

---

# 25. Implantação

## 25.1 Ambiente local

```text
docker compose up
├── frontend   (Vite dev / Nginx em prod)
├── backend    (FastAPI + Uvicorn)
└── postgres
```

Suficiente para o MVP. Não é necessário Kubernetes.

## 25.2 Ambiente de produção inicial

```text
Reverse Proxy (Nginx/Caddy + TLS)
      ▼
Frontend (build estático)
      ▼
FastAPI (Uvicorn, N workers)
      ▼
PostgreSQL
```

O processamento pode permanecer síncrono, desde que a meta de <5 minutos seja atendida — o que o time budget de 30s do solver garante por construção. Caso futuramente fique pesado, adicionar fila de tarefas. **Não é recomendável adicionar Celery/RabbitMQ no MVP sem evidência de necessidade.**

## 25.3 Backup

PostgreSQL com backup periódico, retenção definida, restauração testada e armazenamento separado do servidor principal. Os arquivos de entrada originais também devem ser preservados, pois sem eles nenhuma execução é reproduzível (RNF-003).

---

# 26. Observabilidade

```text
execution_id, start_time, end_time, duration
axis, vehicle, profile_id
orders_input, orders_removed, orders_ineligible, orders_selected
total_weight, total_volume, weight_occupancy, volume_occupancy
limiting_resource, estimated_cubing_pct
solver_status, optimality_gap, solve_duration_ms
algorithm_version, user_id
```

Exemplo de log estruturado:

```text
Execution: 2026-001
Axis: 3 | Vehicle: Truck-02 | Profile: equilibrado

Input:       482 orders
Removed:      73 (cancelados: 41, balcão: 22, Crateús: 10)
Ineligible:   18 (sem cubagem: 15, excede veículo: 3)
Eligible:    391
Selected:     31

Weight: 91,8%  |  Volume: 95,1%  |  Limitante: volume
Cubagem estimada: 12%
Solver: OPTIMAL | gap 0% | 1,42s
```

---

# 27. Decisões arquiteturais (ADRs)

**(Novo na v2.0)**

Decisões estruturais devem ser registradas em `docs/adr/`, não apenas descritas em prosa. Formato mínimo: contexto, decisão, alternativas consideradas, consequências, status, data, responsável.

| ADR | Decisão | Status |
|-----|---------|--------|
| 0001 | Não utilizar ML no núcleo de decisão | Aceita |
| 0002 | Não utilizar LLM no MVP | Aceita |
| 0003 | CP-SAT como solver, em vez de KnapsackSolver | Aceita |
| 0004 | Score multicritério com normalização logarítmica | Aceita |
| 0005 | Monólito modular, não microsserviços | Aceita |
| 0006 | Geocodificação Open Source GeoPy/OSM e TSP via OR-Tools | Aceita |
| 0007 | Pedido indivisível (variável binária) | Pendente de confirmação do stakeholder |

O ADR-0006 é o que ativa a barreira de RNF-002-A: qualquer reversão futura dessa decisão exige um novo ADR com análise de reidentificação.

---

# 28. Decisões técnicas recomendadas

| Problema | Solução recomendada |
|----------|---------------------|
| API | FastAPI |
| Frontend | React + TypeScript |
| Tipos compartilhados | openapi-typescript |
| Banco | PostgreSQL |
| Migrations | Alembic |
| Processamento | Python 3.11+ |
| Manipulação de dados | Pandas/Polars |
| Validação de schema | Pandera + Pydantic |
| Otimização | OR-Tools **CP-SAT** |
| Fallback | Heurística gulosa por eficiência |
| PDF | WeasyPrint |
| Autenticação | JWT + RBAC (3 papéis) |
| Containerização | Docker Compose |
| Testes | Pytest + Hypothesis |
| CI | GitHub Actions (ruff, mypy, pytest, build) |
| Logging | structlog |
| ML no MVP | Não utilizar |
| LLM | Não utilizar |
| MLOps | Apenas quando houver ML |
| Tracking ML futuro | MLflow |
| Geocodificação MVP | Não utilizar |
| Roteamento futuro | OSRM + OR-Tools Routing, se autorizado |
| Arquitetura | Monólito modular |
| Microsserviços | Não necessários inicialmente |
| Kubernetes | Não necessário inicialmente |
| Celery/RabbitMQ | Não necessário inicialmente |

---

# 29. Justificativa das principais escolhas

**OR-Tools / CP-SAT.** O problema é um MKP 0-1, NP-difícil, com duas dimensões de capacidade. CP-SAT resolve nativamente o caso multidimensional, aceita restrições adicionais de negócio sem reescrita do modelo, permite time budget com melhor incumbente e retorna status explícito da solução. Não há razão para implementar branch-and-bound próprio.

**Score multicritério com log.** Ocupação pura premia pedidos pesados e baratos; valor puro ignora a restrição física que é o cerne do desafio. A combinação ponderada equilibra os dois, e a normalização logarítmica impede que outliers de faturamento dominem a seleção.

**FastAPI.** Validação por type hints e OpenAPI automático, que serve como contrato tipado direto para o frontend.

**PostgreSQL.** Suficiente para pedidos, produtos, veículos, eixos, planos, execuções e auditoria. Não há necessidade de banco distribuído.

**WeasyPrint.** Gera o romaneio a partir do mesmo HTML/CSS da visualização web, evitando manter dois mecanismos de composição de documento.

**Monólito modular.** O sistema tem um único fluxo de processamento, um único time e um único banco. Microsserviços aqui só adicionariam latência de rede e complexidade de deploy sem nenhum ganho de escalabilidade real.

---

# 30. Estratégia de evolução

## Fase 1 — MVP (hackathon)

```text
CSV → Validação → Limpeza → Cubagem → Scoring → CP-SAT → Validação → Plano → PDF
```

Inclui: perfis de otimização, relatório de decisão, edição manual auditada, RBAC básico.

## Fase 2 — Operação

Integração com a origem dos pedidos, histórico consolidado, fluxo formal de aprovação, assinatura digital, dashboards de acompanhamento, alertas de baixa ocupação.

## Fase 3 — Otimização avançada

Multieixo com alocação dos quatro veículos, análise sistemática de peso × volume por eixo, otimização de rota, geolocalização (mediante ADR e autorização).

## Fase 4 — Inteligência preditiva

Apenas com dados suficientes: previsão de demanda, estimativa de cubagem faltante, previsão de ocupação, custo por km e margem por eixo. Stack: scikit-learn + MLflow + FastAPI. **O otimizador determinístico continua tomando a decisão final.**

---

# 31. Critérios de aceite do MVP

| ID | Critério |
|----|----------|
| CA-001 | O sistema carrega os dados fornecidos |
| CA-002 | Pedidos cancelados, balcão e Crateús são tratados conforme as regras do desafio |
| CA-003 | A cubagem é calculada corretamente |
| CA-004 | Nenhuma solução ultrapassa a capacidade de peso |
| CA-005 | Nenhuma solução ultrapassa a capacidade de volume |
| CA-006 | O plano é gerado em menos de 5 minutos |
| CA-007 | O plano apresenta pedidos, valor, peso, volume, ocupação e ordem de descarga |
| CA-008 | O plano pode ser impresso/exportado em PDF |
| CA-009 | As correções da limpeza podem ser explicadas |
| CA-010 | O plano pode ser utilizado pela expedição sem retrabalho significativo |
| **CA-011** | **Todo pedido excluído tem motivo registrado e consultável** *(v2.0)* |
| **CA-012** | **O plano pode ser editado manualmente sem jamais violar capacidade** *(v2.0)* |
| **CA-013** | **Trocar o perfil de otimização produz planos diferentes sem alterar código** *(v2.0)* |
| **CA-014** | **A mesma entrada com a mesma configuração reproduz o mesmo plano** *(v2.0)* |
| **CA-015** | **O sistema retorna plano válido mesmo quando o solver não converge** *(v2.0)* |
| **CA-016** | **O sistema identifica se o eixo é limitado por peso ou por volume** *(v2.0 — bônus do desafio)* |

---

# 32. Perguntas para os stakeholders

Mantidas da v1.0, agora com **valor padrão implementado** — o sistema funciona antes da resposta, e a resposta apenas recalibra a configuração.

## 32.1 Objetivo da otimização

| # | Pergunta | Padrão adotado |
|---|----------|----------------|
| 1 | O que significa "melhor carga"? | Perfil equilibrado |
| 2–4 | Maximizar peso, volume ou valor? | Combinação ponderada |
| 5 | Peso e volume têm a mesma importância? | Sim (0,25 / 0,25) |
| 6 | Existe produto prioritário? | Não implementado; suportado via `x_i = 1` |

## 32.2 Pedidos

| # | Pergunta | Padrão adotado |
|---|----------|----------------|
| 7 | Todos os pedidos têm a mesma prioridade? | Não — score por valor e frequência |
| 8 | Existe SLA? | Não implementado; suportado |
| 9 | Pedido pode ser dividido entre caminhões? | **Não** (premissa 11) |
| 10 | Pedido deve ser transportado integralmente? | Sim |
| 11–12 | Pedidos obrigatórios / que podem esperar? | Via `mandatory_order_ids` |

## 32.3 Cubagem

| # | Pergunta | Padrão adotado |
|---|----------|----------------|
| 13–14 | Como é calculado o volume? Qual a unidade oficial? | m³ como unidade canônica |
| 15 | Conversão m² → caixas? | `ceil()`, a validar |
| 16 | Peso bruto ou líquido? | A confirmar — **impacta diretamente CA-004** |
| 17 | Produtos sem cubagem? | Excluídos e sinalizados |
| 18 | Ranking_Top85 pode ser usado diretamente? | Sim, marcado como `estimated` |
| 19–20 | Margem de segurança? | Não aplicada; configurável por veículo |

## 32.4 Veículos

21. Capacidade legal ou operacional? 22. Existe margem de segurança? 23. Os quatro caminhões são diferentes? 24. Restrição de produtos por veículo? 25. Veículos prioritários por eixo?

*Padrão: capacidade cadastrada tratada como limite absoluto, sem margem. A pergunta 21 é crítica — se a capacidade informada for legal e não operacional, o sistema pode gerar planos fisicamente inviáveis mesmo estando matematicamente corretos.*

## 32.5 Eixos

26. A ordem atual das cidades é conhecida? 27. É fixa? 28. Pode variar conforme os pedidos? 29. Restrições de acesso? 30. A ordem deve considerar distância ou a sequência operacional atual?

*Padrão: ordem fixa configurável por `City.delivery_order`.*

## 32.6 Operação

31. Quem executa? 32. Quem gera carga? 33. Quem altera? 34. Quem aprova? 35. O plano pode ser alterado manualmente? 36. A alteração precisa ser registrada? 37. Assinatura digital ou física?

*Padrão: RBAC de três papéis; alteração manual permitida ao `aprovador`, sempre auditada; assinatura física no romaneio impresso.*

## 32.7 Dados

38. Fonte oficial? 39. Frequência de atualização? 40. Integração futura com ERP? 41. Sistema que gera os pedidos? 42. Sistema com dados de produtos? 43. Identificador único permanente?

*A pergunta 43 é crítica para a Fase 2: sem chave estável, a integração com ERP exige camada de reconciliação.*

## 32.8 Geolocalização

44. Autoriza dados externos do OpenStreetMap? 45. Ordem manual ou calculada? 46. Existe rota operacional oficial? 47. Distância rodoviária real importa? 48. Restrições de estrada não mapeadas?

*Padrão: não utilizar dados externos (ADR-0006).*

## 32.9 Futuro

49. Interesse em previsão de demanda? 50. Histórico suficiente? 51. Custo por km? 52. Margem por eixo? 53. Distribuição automática dos quatro veículos entre os cinco eixos?

---

# 33. Decisão arquitetural final

```text
                 NobreLOG IA
                     │
          ┌──────────┴──────────┐
          │                     │
      React/TS             FastAPI/Python
                                │
        ┌──────────┬────────────┼────────────┬──────────┐
        │          │            │            │          │
     Dados     Scoring     OR-Tools     Validação      PDF
        │          │        CP-SAT      independente    │
   PostgreSQL   NumPy      Optimizer         │      WeasyPrint
                                             │
                                        Auditoria
```

A solução deve ser implementada como **monólito modular**, e não como microsserviços.

O coração do sistema deve ser um **motor de otimização determinístico**, e não um modelo de IA.

```text
Dados confiáveis
      ↓
Limpeza rastreável
      ↓
Cubagem determinística com origem registrada
      ↓
Score de prioridade parametrizável
      ↓
Otimização matemática com garantia de viabilidade
      ↓
Validação independente
      ↓
Decisão explicável
      ↓
Edição controlada e auditada
      ↓
Romaneio assinável
```

Essa abordagem atende diretamente ao problema descrito pela Nobre Lar, mantém a solução explicável para a equipe de logística e evita adicionar componentes cuja complexidade não é necessária para o MVP.

---

# 34. Resumo das mudanças da v2.0

| # | Mudança | Requisito | Motivo |
|---|---------|-----------|--------|
| 1 | Função objetivo formalizada com score multicritério | RF-009 | Era o maior ponto em aberto da v1.0 |
| 2 | Score de eficiência como critério alternativo | RF-009-A | Evita premiar pedidos pesados e baratos |
| 3 | CP-SAT explicitado + time budget + fallback | RF-008, RNF-001-A | Suporta restrições futuras; nunca trava |
| 4 | Perfis de otimização configuráveis | RF-009-B | Pesos são regra de negócio, não constante |
| 5 | Relatório de decisão por pedido | RF-011-A | Adoção pela operação depende de explicabilidade |
| 6 | Edição manual auditada | RF-013-A | Evita o padrão "aceite tudo ou descarte tudo" |
| 7 | Validação declarativa de schema | RF-002 | Gera o log de limpeza sem código duplicado |
| 8 | Rastreabilidade da origem da cubagem | RF-005-A | Aprovador precisa saber a confiança do plano |
| 9 | RBAC básico | RF-017 | Auditoria sem usuário identificado não é auditoria |
| 10 | Health check + métricas de qualidade | RNF-006-A | Mede quão boa é a solução, não só quão rápida |
| 11 | ADRs, incluindo barreira de reidentificação | RNF-002-A, §27 | Premissas em prosa são esquecidas |
| 12 | Pipeline de CI | RNF-009 | Requisito da meta de "implantação real" |
| 13 | Testes de carga e property-based | §24 | v1.0 validava desempenho com 3 pedidos |
| 14 | Snapshot do perfil no plano | RF-015 | Sem ele, execuções passadas não reproduzem |
| 15 | Análise de densidade por eixo | §13.1 | Ataca diretamente o bônus do desafio |
| 16 | Estratégia de decomposição multieixo | §18.1 | v1.0 não discutia escalabilidade do solver |

---

# 35. Fontes técnicas consultadas

* Google OR-Tools — CP-SAT, knapsack multidimensional, packing e routing.
* FastAPI — validação por type hints e OpenAPI.
* Pandera — validação declarativa de schemas de DataFrame.
* Hypothesis — property-based testing.
* OSRM — roteamento e matrizes de distância, para eventual evolução.
* GeoPy — interface Python para serviços de geocodificação.
* Nominatim/OpenStreetMap — política de utilização e restrições do serviço público.
* WeasyPrint — geração de PDF a partir de HTML/CSS.
* MLflow — tracking e registry para eventual etapa futura de ML.
