# ADR-0001: Não utilizar Machine Learning no Núcleo de Decisão

## Status
**ACEITO**

## Contexto
O desafio propõe o desenvolvimento de uma solução inteligente de alocação de cargas. Havia a hipótese de utilizar modelos de Machine Learning (como regressão, árvores de decisão ou redes neurais) ou Modelos de Linguagem (LLMs) para selecionar os pedidos que compõem o caminhão.

## Decisão
Decidimos **NÃO utilizar Machine Learning nem LLMs no núcleo do motor de otimização combinatória**. 
O problema de alocação de carga é estritamente um problema de Pesquisa Operacional (*Multidimensional Knapsack Problem*) com restrições rígidas (*hard constraints* de peso e volume).

## Consequências
- **Positivas:**
  - Garantia matemática absoluta de que a capacidade do caminhão nunca será violada (\(\sum peso \le Cap\)).
  - Solução ótima ou com gap garantido encontrada em frações de segundo.
  - Explicabilidade determinística de cada decisão de inclusão ou rejeição.
  - Zero custo de tokens de IA e zero latência de chamadas externas de API.
- **Negativas:**
  - Exige modelagem matemática rigorosa em vez de abordagens empíricas por tentativa e erro.
