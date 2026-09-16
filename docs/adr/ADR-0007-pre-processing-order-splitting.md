# ADR-0007: Pré-processamento de Fatiamento de Cargas (Order Splitting)

## Status
**ACEITO**

## Contexto
A auditoria dos dados revelou pedidos individuais de até 5.387 kg (100 sacos de cimento), excedendo a capacidade máxima de 4.800 kg do maior caminhão (Accelo 815). Sob a premissa de indivisibilidade pura, o solver binário seria forçado a rejeitar os pedidos de maior faturamento.

## Decisão
Implementar um serviço de pré-processamento (*Order Splitting*) que desmembra pedidos com \(Peso > Cap_{max}\) em subpedidos vinculados (`-P1`, `-P2`) antes de enviá-los ao solver.

## Consequências
- **Positivas:**
  - Preserva a formulação matemática binária simples e ultra-rápida do CP-SAT.
  - Permite transportar as maiores vendas da empresa sem violar a física da frota.
