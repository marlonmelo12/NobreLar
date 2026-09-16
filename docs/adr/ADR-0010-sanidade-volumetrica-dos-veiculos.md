# ADR-0010: Parametrização da Cubagem Útil Operacional da Frota

## Status
**ACEITO**

## Contexto
A planilha histórica atribuía ao caminhão Accelo 815 uma cubagem irrisória de 2,4543 m³. Com esse valor, uma única caixa d'água de 1.000L ocuparia 86% do caminhão, bloqueando o veículo com apenas 250 kg de carga.

## Decisão
Parametrizar a entidade `Vehicle` com as dimensões internas reais da carroceria (\(C 	imes L 	imes A\)) e aplicar um Fator de Estivagem Operacional de 85%, definindo a capacidade cúbica útil do Accelo 815 em 18,50 m³.
