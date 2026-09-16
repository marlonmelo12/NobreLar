# 08. Rotas Regionais, Geografia e Dimensionamento de Frota

---

## 1. Mapeamento dos 5 Eixos Rodoviários Intermunicipais

A partir da análise do histórico operacional da Nobre Lar em Crateús, as entregas externas são divididas em 5 corredores logísticos regionais:

| Eixo | Denominação Operacional | Cidades, Distritos e Assentamentos Atendidos | Perfil de Carga Predominante |
| :---: | :--- | :--- | :--- |
| **Eixo 1** | **Fronteira Piauí** | Buriti dos Montes (PI), Barro Vermelho, Tucuns, Queimadas, Filomena | Viagens longas; cargas pesadas completas (R$ 35,8k faturados). |
| **Eixo 2** | **Sertão Central** | Sucesso, Tamboril, Nova Russas, Fazenda | Rota mista; entregas agendadas consolidadas. |
| **Eixo 3** | **Eixo Sul** | Independência, Assentamento São José, Adão | Volume regular contínuo (23 pedidos, R$ 36,3k faturados). |
| **Eixo 4** | **Norte e Serra** | Ipaporanga, Poranga, Ararendá, Vaca Morta, Curral Velho | Cargas de alto valor e peso maciço (Ipaporanga R$ 53,1k / Poranga R$ 35,6k). |
| **Eixo 5** | **Inhamuns** | Novo Oriente, Realejo, Santana, Monte Nebo, Santo André, Quiterianópolis | Obras de grande porte (Realejo: maior ticket médio, R$ 6.603). |

---

## 2. Dimensionamento e Especificação Técnica da Frota

A frota operacional da empresa possui três classes de veículos, com seus limites cadastrais nominais e limites operacionais úteis calculados:

| Veículo / Modelo | Capacidade Nominal (kg) | Cubagem Cadastrada | Cubagem Útil Real (\(m^3\)) | Comprimento Útil (m) | Comporta Barras de 6m? | Tipo de Operação Recomendada |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **Moto de Carga (Titan 160)** | 300 | 0,383 \(m^3\) | 0,38 \(m^3\) | 0,80 | ❌ NÃO | Fracionado urgente leve e miudezas (elétrica/tintas). |
| **Kia Bongo / Hyundai HR** | 1.700 | 2,179 \(m^3\) | 6,50 \(m^3\) | 3,10 | ❌ NÃO (ou c/ suporte) | Cargas médias rápidas intraurbanas e vilas próximas. |
| **Mercedes-Benz Accelo 815** | 4.800 | 2,454 \(m^3\)\* | **18,50 \(m^3\)** | 5,50 | ⚠️ SIM (aberto / suporte) | Cargas pesadas de cimento, cerâmica e eixos longos. |

*\*Nota Técnica: O valor cadastral histórico de 2,45 m³ para o Accelo 815 reflete um erro na planilha base (limitação no nível do chão). O sistema adota a Cubagem Útil Real com fator de estivagem (18,50 m³) para evitar falsos travamentos por volume.*

---

## 3. Matriz de Ordenação de Descarga (Sequência de Paradas)

A ordem de atendimento das cidades no eixo é uma **configuração determinística** no MVP, cadastrada em `City.delivery_order`. 

O motor de carregamento calcula automaticamente a ordem inversa de estivagem no caminhão:
```
Parada 1 (Ipaporanga)  --> Carregado por ÚLTIMO (na porta da caçamba)
Parada 2 (Poranga)     --> Carregado no MEIO
Parada 3 (Ararendá)    --> Carregado no FUNDO da caçamba
```
