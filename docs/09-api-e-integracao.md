# 09. API REST e Contratos de Integração

A API segue os padrões RESTful com documentação OpenAPI/Swagger interativa gerada automaticamente em `/docs`.

---

## 1. Endpoints Principais

### 1.1 Ingestão e Status de Dados
- `POST /api/v1/ingest/upload`: Recebe arquivo CSV (multipart/form-data), executa validação Pandera e grava no banco.
- `GET /api/v1/orders/pending?axis_id={id}`: Lista pedidos elegíveis faturados para o eixo informado.
- `GET /api/v1/cleaning-logs`: Retorna histórico de itens descartados e motivos de limpeza.

### 1.2 Otimização e Montagem de Cargas
- `POST /api/v1/load-plans/optimize`: Dispara a resolução do CP-SAT para um par de eixo e veículo.
  
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

### 1.3 Romaneio e Expedição
- `GET /api/v1/load-plans/{id}/manifest/pdf`: Retorna o manifesto de carga em formato PDF binário via streaming.
- `POST /api/v1/load-plans/{id}/approve`: Finaliza o plano e emite o romaneio definitivo.
