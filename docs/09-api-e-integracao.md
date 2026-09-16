# 09. API REST e Contratos de Integração

A API segue os padrões RESTful com documentação OpenAPI/Swagger interativa gerada automaticamente em `/docs`.
Para documentação detalhada com interfaces TypeScript e exemplos de código para React/Vue/Angular, consulte o [Guia de Integração Frontend](GUIA_INTEGRACAO_FRONTEND.md).

---

## 1. API Desacoplada (Consumo Direto pelo Frontend)

Projetada para operação sem dependência de upload de arquivos CSV, ingerindo lotes de pedidos em JSON estruturado diretamente do ERP ou da interface web.

### 1.1 Endpoints Desacoplados (POST Único de Pedidos + GET Exclusivo para Carga e Rota)
- `POST /api/v1/dispatch/orders` (ou `/process-orders`): **Endpoint Único de Envio (POST)** que recebe o JSON de pedidos, calcula e armazena os planos em memória.
- `GET /api/v1/dispatch/truck-load`: Retorna **exclusivamente via GET** a montagem de carga nos caminhões (carroceria aberta) com drill-down.
- `GET /api/v1/dispatch/delivery-route`: Retorna **exclusivamente via GET** o roteiro de entrega (TSP) com endereços e cobrança.
- `GET /api/v1/dispatch/trips/{trip_id}/pdf/loading-sheet`: Emissão e download direto do PDF oficial do Mapa de Carregamento da Carroceria via `GET`.
- `GET /api/v1/dispatch/trips/{trip_id}/pdf/delivery-route`: Emissão e download direto do PDF oficial do Roteiro de Entregas TSP via `GET`.

Consulte o [Guia Completo de Integração Frontend](GUIA_INTEGRACAO_FRONTEND.md) para os contratos de dados completos e tipos TypeScript.

---

## 2. Endpoints Clássicos com Persistência em Banco

### 2.1 Ingestão e Status de Dados
- `POST /api/v1/ingest/upload`: Recebe arquivo CSV (multipart/form-data), executa validação Pandera e grava no banco SQLite/Postgres.
- `GET /api/v1/orders/pending?axis_id={id}`: Lista pedidos elegíveis faturados para o eixo informado.
- `GET /api/v1/cleaning-logs`: Retorna histórico de itens descartados e motivos de limpeza.

### 2.2 Otimização e Montagem de Cargas por Eixo/Veículo
- `POST /api/v1/load-plans/optimize`: Dispara a resolução do CP-SAT para um par específico de eixo e veículo.
  
#### Request Body (`OptimizeRequestSchema`):
```json
{
  "axis_id": "eixo-4-norte-serra",
  "vehicle_id": "accelo-815-01",
  "profile_id": "default-balanced",
  "time_limit_sec": 30.0,
  "mandatory_order_ids": ["L12609324"],
  "excluded_order_ids": []
}
```

#### Response Body (`OptimizeResponseSchema`):
```json
{
  "status": "OPTIMAL",
  "execution_time_ms": 420,
  "load_plan_id": "lp-9842a1",
  "summary": {
    "total_orders_selected": 8,
    "total_weight_kg": 4720.50,
    "total_volume_m3": 14.20,
    "total_value_rs": 18450.80,
    "weight_occupancy_pct": 98.34,
    "volume_occupancy_pct": 76.75,
    "limiting_resource": "PESO",
    "estimated_cubage_pct": 4.12
  },
  "selected_orders": [
    {
      "order_id": "L12609291-P1",
      "city_name": "Ipaporanga",
      "weight_kg": 4000.0,
      "volume_m3": 2.30,
      "value_rs": 4700.0,
      "delivery_order": 1,
      "payment_on_delivery": false
    }
  ],
  "unselected_orders_decisions": [
    {
      "order_id": "L12609829",
      "reason": "EXCEDE_CAPACIDADE_PESO_RESTANTE",
      "score": 0.452
    }
  ]
}
```

### 2.3 Romaneio e Expedição
- `GET /api/v1/load-plans/{id}/manifest/pdf`: Retorna o manifesto de carga em formato PDF binário via streaming.
- `POST /api/v1/load-plans/{id}/approve`: Finaliza o plano e emite o romaneio definitivo.
