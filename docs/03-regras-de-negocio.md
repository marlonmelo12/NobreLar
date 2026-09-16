# 03. Regras de Negócio e Restrições Operacionais

---

## RN-001 — Filtro Obrigatório de Canal de Retirada
- **Regra:** Nenhum pedido marcado como `RETIRADA` no ERP deve ser incluído na fila de montagem de cargas de caminhão.
- **Justificativa:** 26,7% dos pedidos da Nobre Lar são retirados diretamente no balcão pelo cliente. Alocá-los geraria fretes fantasmas e caminhões transportando mercadoria já entregue.
- **Ação do Sistema:** Registrar em `CleaningLog` com status `REMOVIDO_BALCAO` e disponibilizar para visualização na tela de "Retiradas na Loja".

---

## RN-002 — Segregação do Polo Municipal (Crateús)
- **Regra:** Pedidos com endereço de entrega em Crateús não devem competir por vagas nos caminhões dos 5 Eixos Intermunicipais no MVP.
- **Justificativa:** O regulamento do desafio operacional foca no escoamento rodoviário regional. As entregas municipais possuem dinâmica própria de veículo leve (motos/utilitários) com saídas múltiplas diárias.

---

## RN-003 — Conversão Obrigatória de Pisos Cerâmicos (Arredondamento Conservador)
- **Regra:** Se a unidade de venda for `MT` (metros quadrados), a quantidade deve ser convertida em caixas físicas inteiras utilizando o teto:
  $$	ext{caixas} = \left\lceil rac{	ext{Qtd}_{m^2}}{	ext{m2\_por\_caixa}} ightceil$$
- **Justificativa:** A indústria não fraciona caixas de cerâmica. O cliente compra 25,30 m², mas a expedição envia 11 caixas de 2,30 m² (25,30 m²). Calcular o peso fracionado subestimaria a carga no caminhão.

---

## RN-004 — Heurística de Cubagem para Produtos fora do Top 85
- **Regra:** Produtos sem ficha técnica cadastrada não devem causar a exclusão imediata do pedido. Em vez disso, aplicam-se parâmetros médios da categoria:
  - *Conexões e Hidráulica Leve:* 0,05 kg / 0,0003 m³ por unidade.
  - *Elétrica e Lâmpadas:* 0,08 kg / 0,0005 m³ por unidade.
  - *Ferragens e Parafusos:* 0,02 kg / 0,0001 m³ por unidade.
  - *Tintas e Acessórios Médios:* 1,20 kg / 0,0015 m³ por unidade.
- **Justificativa:** 51,9% dos pedidos faturados contêm pelo menos um item fora do Top 85. A exclusão rígida paralisaria metade da operação da empresa.

---

## RN-005 — Indivisibilidade Padrão do Pedido
- **Regra:** Por padrão, todos os itens de um pedido devem ser transportados no mesmo caminhão (\(x_i \in \{0, 1\}\)).
- **Exceção Controlada:** Aplica-se a RN-007 quando o pedido for fisicamente maior que a capacidade do caminhão.

---

## RN-006 — Incompatibilidade Linear de Tubulações (Regra dos 6 Metros)
- **Regra:** Pedidos contendo barras rígidas de PVC (esgoto ou água) ou treliças metálicas de 6 metros só podem ser alocados em veículos cadastrados com `allows_long_items = True`.
- **Justificativa:** Um tubo de 6 metros não entra em caminhonete HR fechada ou baú de 3 metros, mesmo que possua apenas 3 kg e 0,04 m³. A restrição física sobrepõe-se à restrição escalar.

---

## RN-007 — Fatiamento Obrigatório de Super-Cargas (*Order Splitting*)
- **Regra:** Caso a massa de um único pedido ultrapasse o limite de carga útil do caminhão (\(Peso > Cap_{peso}\)), o sistema deve fatiá-lo em remessas automáticas vinculadas:
  - Exemplo: Pedido de 100 sacos de cimento (\(5.000	ext{ kg}\)) em veículo de \(4.800	ext{ kg}\):
    - Subpedido 1: 80 sacos (\(4.000	ext{ kg}\)) com ID `L12608477-P1`.
    - Subpedido 2: 20 sacos (\(1.000	ext{ kg}\)) com ID `L12608477-P2`.
- **Justificativa:** Sem o fatiamento, o modelo matemático binário é forçado a rejeitar o pedido (\(x_i = 0\)), deixando as vendas mais lucrativas da empresa travadas no depósito.

---

## RN-008 — Sanidade Volumétrica dos Veículos (Fator de Estivagem Útil)
- **Regra:** A cubagem útil de veículos de carga fechada deve considerar as dimensões reais da carroceria (\(C 	imes L 	imes A\)) multiplicadas por um **Fator de Estivagem Operacional de 0,85** (desconto de 15% para espaços vazios entre paletes e cantos):
  $$Cap_{vol\_util} = (C 	imes L 	imes A) 	imes 0,85$$
- **Justificativa:** Elimina o erro cadastral da planilha original (onde um caminhão 3/4 Accelo aparecia com irrisórios \(2,45	ext{ m}^3\), lotando com apenas 1 caixa d'água).

---

## RN-009 — Limitação de Caixas D'Água por Veículo
- **Regra:** Veículos utilitários leves (HR/Bongo) não podem receber mais de 1 Caixa D'Água de 1.000L (`12185`) ou 2 de 500L (`12184`). Caminhões médios (Accelo) limitam-se a 4 unidades de 1.000L no topo da carga.
- **Justificativa:** Caixas d'água possuem densidade ultrabaixa (\(8,2	ext{ kg/m}^3\)) e grande diâmetro físico. Empilhá-las sob sacaria de cimento destrói o produto.

---

## RN-010 — Sequenciamento LIFO na Ordem de Carregamento
- **Regra:** A ordem física de carregamento na doca deve ser o inverso da ordem de descarga nas cidades:
  $$	ext{Ordem Carregamento} = 	ext{Ordem Inversa da Ordem de Paradas}$$
- **Justificativa:** O primeiro pedido a ser descarregado na primeira cidade deve ser colocado por último na porta da carroceria (*Last In, First Out*).

---

## RN-011 — Gestão de Recebíveis no Destino (`A RECEBER`)
- **Regra:** Pedidos que possuam o campo `PGT ENTREGA? == 'A RECEBER'` devem ser destacados no romaneio com tarja vermelha e valor total a ser recebido pelo motorista em espécie ou PIX.
- **Justificativa:** Garantir custódia e conferência financeira na saída e no retorno do motorista à base.

---

## RN-012 — Trava de Sobrecarga na Edição Manual
- **Regra:** Se o operador adicionar pedidos manualmente ultrapassando a capacidade do caminhão em mais de 5%, o sistema deve bloquear a emissão do romaneio e exigir autenticação de senha do Coordenador de Logística com termo de responsabilidade.
