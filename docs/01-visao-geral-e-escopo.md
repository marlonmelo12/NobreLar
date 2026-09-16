# 01. Visão Geral e Escopo do Sistema

## 1. Contexto do Problema

O **Grupo Nobre Lar** opera no segmento de materiais de construção e acabamento (Home Center) a partir de seu centro de distribuição e loja matriz em **Crateús (Ceará)**. 

A operação logística atende não apenas o município-sede, mas também uma vasta área regional compreendendo cidades vizinhas, vilas, distritos e assentamentos rurais nos Sertões de Crateús e divisa com o Piauí, estruturados comercialmente em **5 Eixos Rodoviários Intermunicipais**.

### A Dor Operacional
Atualmente, o processo de montagem e roteirização das cargas é **estritamente manual**, executado pelo coordenador de logística com auxílio de planilhas eletrônicas e conferência visual de notas fiscais:
- O processo consome entre **40 e 60 minutos diários** por eixo rodoviário.
- A tomada de decisão é altamente enviesada pelo **valor financeiro** do pedido, ignorando frequentemente a densidade (\(kg/m^3\)) dos materiais.
- Ocorre sobrecarga em caminhões que transportam sacarias pesadas (cimento/argamassa) ou ociosidade severa de peso quando transportam caixas d'água e tubos plásticos.
- Pedidos com itens longos (tubos de 6 metros) são frequentemente alocados para veículos incompatíveis, gerando atrasos na doca de carregamento.

---

## 2. Escala Operacional e Números da Base Real (Agosto/2026)

- **Faturamento Faturado Analisado:** R$ 759.236,79 (688 pedidos de linha).
- **Carga Física Movimentada:** 252,4 toneladas e 215,5 m³ de volume cúbico líquido.
- **Divisão Geográfica:**
  - **Crateús (Sede):** 579 pedidos (84,2% do total) — Ticket Médio: R$ 873,06.
  - **Interior (5 Eixos):** 109 pedidos (15,8% do total) — Ticket Médio: R$ 2.335,87 (Picos de R$ 6.603 em Realejo e R$ 4.451 em Poranga).
- **Frota Alocável:** Caminhões Mercedes-Benz Accelo 815 (4.800 kg), Utilitários Kia Bongo / Hyundai HR (1.700 kg) e Motos de Carga (300 kg).

---

## 3. Escopo do MVP (Hackathon IA 2026)

### 3.1 O que ESTÁ no Escopo Obrigatório
1. **Ingestão e Validação de Dados:** Importação declarativa de pedidos faturados, clientes, itens e catálogo de cubagem (Top 85).
2. **Sanitização Automatizada:** Remoção obrigatória de retiradas no balcão (`RETIRADA`), pedidos cancelados e entregas municipais em Crateús.
3. **Conversão Industrial de Pisos:** Transformação de m² de pisos/porcelanatos para caixas físicas inteiras (`ceil(m2 / m2_por_caixa)`).
4. **Motor de Otimização Multicritério:** Seleção ótima de pedidos para 1 Eixo + 1 Veículo maximizando score combinado (valor, ocupação e frequência) sem violar capacidade máxima de peso e volume.
5. **Pré-Otimização (Order Splitting):** Fatiamento inteligente de cargas que excedem a capacidade máxima do veículo.
6. **Restrições Dimensionais:** Bloqueio de veículos curtos para pedidos com barras rígidas de 6 metros.
7. **Romaneio de Carga:** Emissão do manifesto de carga impresso/PDF com ordem de descarga fixa por cidade, conferência e alertas de pagamento na entrega.
8. **Auditoria e Transparência:** Registro de decisões de exclusão/limpeza (`CleaningLog`) e explicabilidade da não seleção de pedidos.

### 3.2 O que NÃO ESTÁ no Escopo do MVP (Out of Scope)
- Roteirização dinâmica por GPS/TSP (a ordem das cidades é pré-fixada pelo coordenador).
- Enriquecimento de dados via APIs externas de mapas (proibição do regulamento de anonimização).
- Algoritmos de Machine Learning generativo no núcleo de otimização combinatória (resolvido por solver exato CP-SAT).
- Aplicativo móvel nativo para o motorista (o romaneio é web/PDF).

---

## 4. Escopo Pós-MVP (Fases Futuras)

1. **Expansão para o Eixo Crateús:** Ativação do polo municipal como eixo urbano de alta frequência (84% dos pedidos da empresa).
2. **Alocação Simultânea Multiveículo / Multieixo:** Otimização global da frota inteira (4 caminhões operando simultaneamente em 5 eixos).
3. **Roteirização Fina Intra-cidade:** Cálculo de menor rota rua a rua utilizando OpenStreetMap/OSRM mediante geocodificação autorizada.
4. **App do Motorista (Proof of Delivery):** Confirmação digital de entrega e baixa em tempo real com captura de assinatura e foto de canhoto.
