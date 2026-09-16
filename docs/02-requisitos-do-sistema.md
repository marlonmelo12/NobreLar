# 02. Requisitos do Sistema (Funcionais e Não-Funcionais)

---

## 1. Requisitos Funcionais (RF)

### [RF-001] Ingestão de Arquivos
O sistema deve importar arquivos nos formatos CSV com separadores `;` e `,` contendo pedidos faturados (`Pedidos_Filtrados_Semana_X.csv`), dados de faturamento/logística (`DADOS DE ENTREGAS - Vendas_Faturamento_Entregas.csv`) e catálogo de produtos (`Ranking_Top85_Materiais.csv`).

### [RF-002] Validação Declarativa e Sanitização de Entrada
O sistema deve utilizar schemas declarativos (**Pandera** para DataFrames e **Pydantic** para APIs) validando colunas obrigatórias, formatos numéricos e datas.
- Deve aplicar pipeline de regex para sanear identificadores numéricos corrompidos (`12.608570` \(\to\) `12608570`, `12609716.` \(\to\) `12609716`).
- Deve corrigir anos e meses corrompidos (`26/08/14` \(\to\) `26/08/26`, `15/0826` \(\to\) `15/08/26`).
- Registros que violem o contrato devem ser descartados individualmente com log, sem abortar a carga do lote.

### [RF-003] Limpeza e Filtragem de Elegibilidade
O sistema deve excluir da fila de roteirização externa:
1. Pedidos com `Situacao_CSV_Entrega == 'RETIRADA'`.
2. Pedidos com `Logistica == 'CANCELADO'`.
3. Pedidos com `Cidade == 'CRATEUS'` (escopo do desafio regional).
Cada descarte deve gerar uma entrada rastreável em `CleaningLog`.

### [RF-004] Pré-Processamento de Fatiamento de Cargas (*Order Splitting*)
Caso um pedido individual elegível para o eixo selecionado possua peso superior à capacidade nominal do veículo (\(Peso_i > Cap_{peso}\)), o sistema deve desmembrá-lo antes da matriz de otimização em sub-pedidos vinculados:
- Pedido original `L12609291` (\(5.387	ext{ kg}\)) gera `L12609291-P1` (\(4.000	ext{ kg}\)) e `L12609291-P2` (\(1.387	ext{ kg}\)).
- Cada sub-pedido recebe status `is_split = True`, garantindo que cargas maciças de cimento possam ser carregadas sem violar restrições binárias.

### [RF-005] Cálculo de Cubagem e Peso
O sistema deve cruzar cada item do pedido com sua ficha técnica calculando:
$$	ext{peso\_item} = 	ext{quantidade} 	imes 	ext{peso\_unitário}$$
$$	ext{volume\_item} = 	ext{quantidade} 	imes 	ext{volume\_unitário}$$
O pedido final recebe a soma agregada: `total_weight_kg`, `total_volume_m3` e `total_value`.

### [RF-006] Rastreabilidade da Origem da Cubagem e Fallback Heurístico
Cada item deve marcar o metadado `cubagem_source`:
- `ficha_tecnica` ou `ranking_top85`: Dados auditados da indústria.
- `heuristica_categoria`: Para os 587 SKUs fora do Top 85, estimar peso e volume através da densidade média da classe (hidráulica leve, elétrica, ferragens, tintas), evitando descarte indevido do pedido.
- O plano de carga deve exibir o indicador de confiança: `% de cubagem estimada` no peso e volume totais.

### [RF-007] Conversão de Pisos e Porcelanatos
Produtos faturados em metros quadrados (`MT`) devem ser convertidos para caixas físicas inteiras:
$$	ext{caixas} = \left\lceil rac{	ext{quantidade\_m2}}{	ext{m2\_por\_caixa}} ightceil$$
O peso e volume totais do piso são calculados sobre a quantidade inteira de caixas.

### [RF-008] Restrição Linear Dimensional (Tubos e Barras de 6 Metros)
O sistema deve sinalizar a flag `has_long_items = True` para pedidos contendo canos de esgoto/água ou treliças (\(L \ge 6	ext{m}\)).
- O solver CP-SAT deve impedir a alocação de pedidos com `has_long_items` em veículos onde `allows_long_items == False` (baús curtos fechados).

### [RF-009] Otimização da Carga via OR-Tools CP-SAT
Para o par `(Eixo, Veículo)` selecionado, o motor deve resolver o problema de alocação de capacidade (MKP Multidimensional 0-1) maximizando a função objetivo multicritério:
$$\max \sum_{i \in 	ext{Pedidos}} S_i \cdot x_i$$
Sujeito a:
$$\sum_{i} 	ext{peso}_i \cdot x_i \le 	ext{capacidade\_peso}$$
$$\sum_{i} 	ext{volume}_i \cdot x_i \le 	ext{capacidade\_volume}$$
$$x_i \cdot 	ext{has\_long\_items}_i \le 	ext{allows\_long\_items}_{	ext{veiculo}} \quad orall i$$
$$x_i \in \{0, 1\}$$

### [RF-010] Score Multicritério Normalizado
O score de priorização \(S_i\) de cada pedido deve combinar consumo de capacidade e relevância comercial através de normalização logarítmica:
$$S_i = w_w \cdot rac{	ext{peso}_i}{	ext{cap\_peso}} + w_v \cdot rac{	ext{vol}_i}{	ext{cap\_vol}} + w_f \cdot rac{\log(1 + 	ext{valor}_i)}{\log(1 + 	ext{valor}_{max})} + w_q \cdot rac{\log(1 + 	ext{freq}_i)}{\log(1 + 	ext{freq}_{max})}$$
Com pesos configuráveis por perfil de otimização (Padrão: 0,25 / 0,25 / 0,35 / 0,15).

### [RF-011] Validação Independente Pós-Solver
O backend deve validar a solução do solver através de assertivas determinísticas independentes antes de persistir ou exibir o plano:
$$	ext{assert } \sum 	ext{peso}_{	ext{selecionados}} \le 	ext{capacidade\_peso}$$
$$	ext{assert } \sum 	ext{volume}_{	ext{selecionados}} \le 	ext{capacidade\_volume}$$
$$	ext{assert } orall i \ (	ext{has\_long\_items}_i \implies 	ext{allows\_long\_items})$$

### [RF-012] Diagnóstico de Recurso Limitante (Bônus Peso vs Volume)
O sistema deve reportar a ocupação percentual e identificar se o eixo/veículo atingiu saturação primária de **Peso** ou **Volume**:
- `densidade_eixo = sum(peso) / sum(volume)`
- Se `ocupacao_peso > ocupacao_volume`: Limitado por Peso.
- Se `ocupacao_volume >= ocupacao_peso`: Limitado por Volume.

### [RF-013] Ordenação de Descarga por Rota
Os pedidos da carga selecionada devem ser sequenciados conforme a ordem preestabelecida de paradas das cidades no eixo (`City.delivery_order`):
- Posição 1 na descarga = Última cidade visitada (carregada primeiro no fundo do caminhão).
- Ordem de Carregamento (*LIFO - Last In, First Out*).

### [RF-014] Explicabilidade de Decisão (Pedidos Não Selecionados)
O sistema deve apresentar um relatório explícito justificando o motivo da não seleção de cada pedido remanescente:
- `EXCEDE_CAPACIDADE_PESO_RESTANTE`
- `EXCEDE_CAPACIDADE_VOLUME_RESTANTE`
- `INCOMPATIBILIDADE_DIMENSIONAL_6M`
- `BAIXO_SCORE_RELATIVO`

### [RF-015] Edição Manual Controlada com Validação em Tempo Real
O encarregado de logística pode forçar a inclusão (\(x_i = 1\)) ou exclusão (\(x_i = 0\)) de pedidos pela interface web.
- O sistema recalcula instantaneamente os percentuais de ocupação e bloqueia a finalização se houver violação de capacidade sem autorização de sobrecarga.

### [RF-016] Geração do Romaneio e Gestão de Recebíveis
O sistema deve gerar o Romaneio de Carga em tela e para exportação PDF (via WeasyPrint), contendo:
- Metadados do veículo, motorista, data e eixo.
- Tabela ordenada de pedidos e itens por cidade.
- **Tarja de Destaque Financeiro:** Identificação de pedidos com cobrança no destino (`PGT ENTREGA == A RECEBER`) com valor exato a ser cobrado pelo motorista.
- Campos formais de assinatura do conferente e motorista.

### [RF-017] Registro Histórico e Snapshots
Toda execução do otimizador deve ser salva com snapshot imutável dos parâmetros de entrada, pedidos selecionados, métricas de ocupação e hash da configuração.

### [RF-018] Controle de Acesso Baseado em Perfis (RBAC)
O sistema deve disponibilizar perfis de acesso:
- `operador`: Visualiza rotas, gera planos e emite romaneios.
- `coordenador`: Edita planos, força pedidos manuais e altera perfis de score.
- `admin`: Configura capacidades de veículos, sequenciamento de cidades e usuários.

---

## 2. Requisitos Não-Funcionais (RNF)

| Identificador | Categoria | Descrição |
| :--- | :--- | :--- |
| **RNF-001** | **Desempenho** | O solver CP-SAT deve retornar a solução ótima ou viável dentro de um *time budget* máximo de 30 segundos (`max_time_in_seconds = 30.0`). |
| **RNF-002** | **Precisão Numérica** | Toda a aritmética do solver deve operar com inteiros escalados (gramas e \(cm^3\)), evitando erros de ponto flutuante. |
| **RNF-003** | **Segurança & LGPD** | O sistema não deve tentar reidentificar dados anonimizados de clientes nem cruzar telefones/CPFs com bases externas (Barreira de Reidentificação). |
| **RNF-004** | **Observabilidade** | Logs estruturados em formato JSON para cada etapa (ingestão, descarte, resolução e emissão). |
| **RNF-005** | **Portabilidade** | Aplicação empacotada em contêineres Docker com orquestração via Docker Compose. |
| **RNF-006** | **Disponibilidade** | Endpoint de health check `/health` monitorando integridade da API, banco e dependência do OR-Tools. |
| **RNF-007** | **Auditabilidade** | Todo plano gerado deve possuir hash SHA-256 dos parâmetros e pedidos selecionados. |
| **RNF-008** | **Manutenibilidade** | Cobertura de testes unitários superior a 80% nos serviços de cálculo, cubagem e solver. |
| **RNF-009** | **Tecnologia Livre** | Arquitetura 100% baseada em frameworks Open Source sem dependência de licenças comerciais pagas de solvers (ex: Gurobi, CPLEX). |
| **RNF-010** | **Compatibilidade Web** | Frontend responsivo compatível com Chrome, Edge e Firefox modernos. |
