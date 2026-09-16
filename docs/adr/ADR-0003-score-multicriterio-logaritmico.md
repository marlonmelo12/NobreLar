# ADR-0003: Função Objetivo com Score Multicritério Logarítmico

## Status
**ACEITO**

## Contexto
A base de dados da Nobre Lar apresenta grande disparidade de ticket médio (de R$ 14 a R$ 22.976). Se a função objetivo maximizasse diretamente o valor financeiro linear, um único pedido pesado ou de valor extremo canibalizaria toda a carga, prejudicando o atendimento de cidades inteiras.

## Decisão
Implementamos um score ponderado normalizado com atenuação logarítmica para valor e frequência de venda:
$$S_i = w_w \cdot \left(rac{W_i}{CAP_W}ight) + w_v \cdot \left(rac{V_i}{CAP_V}ight) + w_f \cdot \left(rac{\log(1 + 	ext{Valor}_i)}{\log(1 + 	ext{Valor}_{max})}ight) + w_q \cdot \left(rac{\log(1 + 	ext{Freq}_i)}{\log(1 + 	ext{Freq}_{max})}ight)$$

## Consequências
- **Positivas:**
  - Equilíbrio matemático entre aproveitamento físico do caminhão e faturamento da empresa.
  - Suporte a múltiplos perfis de otimização configuráveis pelo gestor.
