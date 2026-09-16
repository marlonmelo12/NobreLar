# Guia Completo de Integração Frontend — NobreLOG IA

Este documento fornece a especificação técnica completa, contratos de dados, interfaces TypeScript e exemplos práticos para o desenvolvimento e integração do **Frontend** com a API Desacoplada do **NobreLOG IA**.

---

## 1. Visão Geral da Arquitetura Desacoplada

O backend opera de forma **100% desacoplada e stateless**:
- O Frontend envia um lote JSON contendo os pedidos faturados do dia (sem necessidade de arquivo CSV nem de banco de dados prévio);
- O backend executa em memória:
  1. **Higienização e Auditoria**: Expulga pedidos de retirada no balcão (`RETIRADA`), cancelados (`CANCELADO`) e entregas urbanas de Crateús quando em fluxo intermunicipal, retornando o log auditado de cada descarte;
  2. **Cubagem Técnica e Detecção de Itens Longos**: Calcula peso e volume reais de cada item com o catálogo técnico Top 85 e identifica tubos/barras de 6 metros;
  3. **Segregação Estrita por Eixo**: Impede terminantemente a mistura de eixos incompatíveis na mesma viagem;
  4. **Solver Multi-Viagens (CP-SAT)**: Aloca as cargas respeitando limites de PBT (capacidade de carga líquida em kg) e volume útil ($m^3$) dos caminhões; se a demanda exceder a capacidade da primeira viagem, gera automaticamente viagens subsequentes (Viagem 1, Viagem 2...);
  5. **Roteirização TSP (Caixeiro Viajante)**: Determina a rota ótima de entrega minimizando a distância rodoviária;
  6. **Carregamento LIFO em Carroceria Aberta**: Define a ordem inversa de carregamento na carroceria aberta (o primeiro a ser entregue fica na traseira; o último fica no fundo/assoalho dianteiro).
- O Frontend recebe contratos JSON prontos para renderizar duas telas principais com **drill-down aninhado de itens**, além de endpoints para download dos PDFs oficiais de romaneio.

---

## 2. Endpoints da API

A URL base padrão da API é `http://localhost:8000` (ou a URL de produção configurada).
A documentação interativa Swagger/OpenAPI está disponível em `/docs`.

### 2.1. Arquitetura de Endpoints (POST Único + Restante Somente GET)

| Método | Endpoint | Papel no Frontend |
| :--- | :--- | :--- |
| **`POST`** | `/api/v1/dispatch/orders` | **Endpoint Único de Envio (`POST`)**: Recebe o JSON com os pedidos faturados do dia. Executa a inteligência de alocação e roteirização e armazena os resultados para consulta. |
| **`GET`** | `/api/v1/dispatch/truck-load` | **Tela 1: Cargas no Caminhão (`GET` puro)**: Retorna a alocação de cargas por caminhão (carroceria aberta, LIFO, ocupação peso/volume) com drill-down de itens. |
| **`GET`** | `/api/v1/dispatch/delivery-route` | **Tela 2: Ordem de Entrega / Roteiro (`GET` puro)**: Retorna as paradas ordenadas pelo algoritmo do Caixeiro Viajante (TSP) com endereços, status de cobrança e drill-down. |
| **`GET`** | `/api/v1/dispatch/mock-orders` | **Mocks de Teste (`GET` puro)**: Retorna a coleção mock canônica (L12608361) para testes na interface. |
| **`GET`** | `/api/v1/dispatch/trips/{trip_id}/pdf/loading-sheet` | **PDF de Carga (`GET` puro)**: Download ou visualização do Mapa de Carregamento da Carroceria Aberta (compatível com `<a href>` e `window.open`). |
| **`GET`** | `/api/v1/dispatch/trips/{trip_id}/pdf/delivery-route` | **PDF de Rota (`GET` puro)**: Download ou visualização do Roteiro de Entregas TSP com cobrança. |

> [!IMPORTANT]
> **Fluxo de Dados no Frontend**:
> 1. O operador clica para importar/enviar os pedidos $\rightarrow$ Frontend faz **`POST /api/v1/dispatch/orders`** com o JSON dos pedidos faturados.
> 2. Para renderizar a tela de Cargas no Caminhão $\rightarrow$ Frontend faz **`GET /api/v1/dispatch/truck-load`** (sem payload nenhum).
> 3. Para renderizar a tela de Ordem de Entregas $\rightarrow$ Frontend faz **`GET /api/v1/dispatch/delivery-route`** (sem payload nenhum).
> 4. Para baixar/visualizar os PDFs $\rightarrow$ Links nativos HTML `<a href="...">` direto para as rotas **`GET`**.

---

## 3. Semântica de Negócio Obrigatória para a Interface

### 3.1. Caminhão de Carroceria Aberta (Sem Doca/Baú)
O transporte rodoviário regional da Nobre Lar utiliza caminhões de grade baixa com **carroceria aberta** (ex: Mercedes-Benz Accelo 815).
- **Terminologia PROIBIDA na UI**: "Doca", "Baú", "Doca de Carregamento".
- **Terminologia OBRIGATÓRIA na UI**:
  - Tipo de veículo: `"Carroceria Aberta (Grade Baixa)"`.
  - Posições da carga na carroceria:
    - `"Frente da Carroceria (Fundo do Assoalho)"`: primeiros pedidos carregados (últimos a serem entregues);
    - `"Meio da Carroceria"`: pedidos intermediários;
    - `"Traseira da Carroceria"`: últimos pedidos carregados (primeiros a serem descarregados).
  - Alerta operacional para cargas com itens de 6m (`possui_itens_6m: true`):
    > *"Carroceria aberta — Carga com tubos/barras lineares de 6m: fixar com cintas e catracas no assoalho lateral."*

### 3.2. Enum Canônico de Situação (`situacao`)
O campo `situacao` é obrigatório e utiliza estritamente o enum extraído do ERP/CSV:
- `NORMAL`: Entrega regular padrão;
- `URGENTE`: Entrega com prioridade máxima. O solver aloca compulsoriamente na 1ª viagem viável;
- `RETIRADA`: Retirada direta no balcão da loja pelo cliente. Não vai para a carroceria; o backend expurga e lista em `descartes_limpeza`;
- `CARRO HORARIO`: Entrega agendada com janela de horário fixo;
- `PROGRAMADO`: Entrega programada para data futura;
- `TOPIQUE`: Despacho via van ou veículo leve municipal;
- `CANCELADO`: Pedido cancelado. Expurgado automaticamente pelo backend.

> [!IMPORTANT]
> O campo legado `situacao_entrega` foi **completamente removido**. Utilize apenas `situacao`.

### 3.3. Status de Pagamento na Entrega
- Se `status_pagamento == "A RECEBER"`:
  - Exibir badge vermelho/destaque de cobrança;
  - Exibir o campo `valor_a_receber`;
  - Exibir o alerta: *"Exigir comprovante PIX/Dinheiro antes do descarregamento!"*.
- Se `status_pagamento == "QUITADO"`:
  - Exibir badge verde de pedido pago.

---

## 4. Tipagem TypeScript Completa (Copiar e Colar)

Salve o arquivo abaixo no seu projeto frontend (ex: `src/types/dispatch.ts`):

```typescript
/**
 * Tipos canônicos da API Desacoplada do NobreLOG IA.
 * Compatível com TypeScript 4.5+ e frameworks modernos (React, Vue, Vite, Next.js).
 */

// ---------------------------------------------------------------------------
// 1. Enums de Negócio
// ---------------------------------------------------------------------------
export enum SituacaoPedidoEnum {
  NORMAL = 'NORMAL',
  URGENTE = 'URGENTE',
  RETIRADA = 'RETIRADA',
  CARRO_HORARIO = 'CARRO HORARIO',
  PROGRAMADO = 'PROGRAMADO',
  TOPIQUE = 'TOPIQUE',
  CANCELADO = 'CANCELADO',
}

export type PerfilOtimizacao = 'Equilibrado' | 'Faturamento' | 'Eficiencia_Peso';

// ---------------------------------------------------------------------------
// 2. Payloads de Entrada (Request)
// ---------------------------------------------------------------------------
export interface ItemInput {
  codigo?: string;           // Código SKU (ex: "23717")
  descricao: string;         // Descrição técnica (ex: "PISO POINTER PIETRA 60X60")
  quantidade: number;        // Quantidade (ex: 14.6)
  unidade: string;           // UN, MT, KG, CX, SC
  preco_unitario?: number;   // Preço bruto unitário (R$)
  subtotal?: number;         // Preço total da linha (R$)
}

export interface OrderInput {
  id: string;                // Número do pedido (ex: "L12608361")
  data?: string;             // Data de emissão (ex: "03/08/2026")
  vendedor?: string;         // Nome do vendedor
  cliente?: string;          // Nome ou razão social do cliente
  cidade: string;            // Município de destino (ex: "IPAPORANGA")
  endereco?: string;         // Logradouro, número, bairro e CEP
  valor?: number;            // Valor total líquido (R$)
  urgente?: boolean;         // Flag booleana de urgência
  situacao: SituacaoPedidoEnum | string; // Enum canônico
  pagamento_entrega?: string | null; // "A RECEBER", "SIM" ou null
  itens: ItemInput[];        // Lista de produtos
}

export interface BatchRequest {
  pedidos: OrderInput[];
  perfil_otimizacao?: PerfilOtimizacao;
  tempo_limite_segundos?: number; // Padrão: 20.0s
}

// ---------------------------------------------------------------------------
// 3. Drill-Down de Itens
// ---------------------------------------------------------------------------
export interface ItemDrillDown {
  codigo: string;
  descricao: string;
  quantidade: number;
  unidade: string;
  peso_unitario_kg: number;
  peso_total_kg: number;
  volume_total_m3: number;
  e_item_6m: boolean;        // Se for peça de 6 metros
  cubagem_estimada: boolean; // Se usou fallback heurístico
}

// ---------------------------------------------------------------------------
// 4. Visão 1: Carga no Caminhão (Carroceria Aberta)
// ---------------------------------------------------------------------------
export interface TruckLoadOrderItem {
  pedido: string;
  external_id: string;
  ordem_carregamento: number;      // 1 = primeiro a carregar no fundo
  posicao_carroceria: string;      // "Frente da Carroceria (Fundo do Assoalho)", etc.
  ordem_entrega_prevista: number;  // Ordem prevista da parada
  cliente?: string | null;
  cidade: string;
  endereco?: string | null;
  situacao: string;                // "NORMAL", "URGENTE", etc.
  peso_total_kg: number;
  volume_total_m3: number;
  valor_total: number;
  urgente: boolean;
  possui_itens_6m: boolean;
  pagamento_na_entrega?: string | null;
  itens: ItemDrillDown[];          // DRILL-DOWN ANINHADO
}

export interface VehicleInfo {
  id: string;
  nome: string;
  placa: string;
  tipo_carroceria: string;         // "Carroceria Aberta (Grade Baixa)"
  capacidade_kg: number;           // Ex: 4800 kg
  volume_util_m3: number;          // Ex: 18.5 m3
  permite_barras_6m: boolean;
}

export interface TruckLoadTrip {
  viagem_id: string;
  viagem_numero: number;
  titulo: string;
  eixo_id: string;
  eixo_nome: string;
  veiculo: VehicleInfo;
  total_pedidos: int;
  peso_total_kg: number;
  volume_total_m3: number;
  faturamento_total: number;
  ocupacao_peso_pct: number;       // Ex: 92.4%
  ocupacao_volume_pct: number;     // Ex: 68.1%
  recurso_limitante: 'PESO' | 'VOLUME' | 'EQUILIBRADO';
  alerta_carroceria?: string | null;
  pedidos_carroceria: TruckLoadOrderItem[];
}

export interface TruckLoadResponse {
  status: 'SUCESSO' | 'ERRO';
  total_viagens: number;
  viagens: TruckLoadTrip[];
}

// ---------------------------------------------------------------------------
// 5. Visão 2: Ordem de Entrega (Roteiro TSP)
// ---------------------------------------------------------------------------
export interface DeliveryRouteStopItem {
  parada: number;                  // 1ª parada, 2ª parada...
  pedido: string;
  external_id: string;
  cliente?: string | null;
  cidade: string;
  endereco_completo: string;
  posicao_na_carroceria: string;
  situacao: string;
  valor_pedido: number;
  status_pagamento: 'QUITADO' | 'A RECEBER';
  valor_a_receber: number;
  alerta_cobranca?: string | null;
  peso_total_kg: number;
  volume_total_m3: number;
  possui_itens_6m: boolean;
  itens: ItemDrillDown[];          // DRILL-DOWN ANINHADO
}

export interface DeliveryRouteTrip {
  viagem_id: string;
  viagem_numero: number;
  titulo: string;
  eixo_id: string;
  eixo_nome: string;
  veiculo: Record<string, any>;
  total_paradas: number;
  faturamento_total: number;
  total_a_receber_rota: number;
  distancia_estimada_km: number;
  paradas: DeliveryRouteStopItem[];
}

export interface DeliveryRouteResponse {
  status: 'SUCESSO' | 'ERRO';
  total_viagens: number;
  viagens: DeliveryRouteTrip[];
}

// ---------------------------------------------------------------------------
// 6. Resposta Consolidada Completa
// ---------------------------------------------------------------------------
export interface CleaningDiscardLog {
  pedido: string;
  regra: 'retirada_balcao' | 'pedido_cancelado' | 'cidade_nao_mapeada' | string;
  motivo: string;
}

export interface DispatchSummary {
  pedidos_recebidos: number;
  pedidos_elegiveis: number;
  pedidos_descartados_limpeza: number;
  pedidos_alocados_viagens: number;
  pedidos_pendentes_proximo_dia: number;
  total_viagens_geradas: number;
  faturamento_total_expedido: number;
  peso_total_expedido_kg: number;
  volume_total_expedido_m3: number;
  taxa_atendimento_pedidos_pct: number;
}

export interface DecoupledDispatchResponse {
  status: 'SUCESSO' | 'ERRO';
  resumo: DispatchSummary;
  cargas_caminhao: TruckLoadTrip[];
  roteiros_entrega: DeliveryRouteTrip[];
  descartes_limpeza: CleaningDiscardLog[];
}
```

---

## 5. Exemplo Real de Consumo (JSON de Entrada)

Exemplo de payload enviado no corpo da requisição `POST /api/v1/dispatch/process-orders`:

```json
{
  "perfil_otimizacao": "Equilibrado",
  "tempo_limite_segundos": 20.0,
  "pedidos": [
    {
      "id": "L12608401",
      "data": "03/08/2026",
      "vendedor": "MASCILON",
      "cliente": "AGROPECUARIA IPAPORANGA",
      "cidade": "IPAPORANGA",
      "endereco": "Rua Franklin José Vieira, 100, Centro, CEP 62290-000, Ipaporanga - CE",
      "valor": 4800.00,
      "urgente": true,
      "situacao": "URGENTE",
      "pagamento_entrega": null,
      "itens": [
        {
          "codigo": "21503",
          "descricao": "CIMENTO POTY TODAS OBRAS 50KG",
          "quantidade": 40.0,
          "unidade": "UN",
          "preco_unitario": 38.00,
          "subtotal": 1520.00
        },
        {
          "codigo": "14900",
          "descricao": "ARGAMASSA VARANDAS E QUINTAIS 15KG QUARTZOLIT",
          "quantidade": 20.0,
          "unidade": "UN",
          "preco_unitario": 22.90,
          "subtotal": 458.00
        }
      ]
    },
    {
      "id": "L12608402",
      "data": "03/08/2026",
      "vendedor": "CAMILA",
      "cliente": "FERRAGISTA E HIDRAULICA DO NORTE",
      "cidade": "IPAPORANGA",
      "endereco": "Av. 22 de Setembro, 240, Centro, Ipaporanga - CE",
      "valor": 1500.00,
      "urgente": true,
      "situacao": "URGENTE",
      "pagamento_entrega": "A RECEBER",
      "itens": [
        {
          "codigo": "10200",
          "descricao": "TUBO ESGOTO 100MM 6M TIGRE",
          "quantidade": 15.0,
          "unidade": "UN",
          "preco_unitario": 100.00,
          "subtotal": 1500.00
        }
      ]
    }
  ]
}
```

---

## 6. Exemplo de Resposta do Backend (JSON de Saída)

A resposta é estruturada com ambas as visões com drill-down:

```json
{
  "status": "SUCESSO",
  "resumo": {
    "pedidos_recebidos": 2,
    "pedidos_elegiveis": 2,
    "pedidos_descartados_limpeza": 0,
    "pedidos_alocados_viagens": 2,
    "pedidos_pendentes_proximo_dia": 0,
    "total_viagens_geradas": 1,
    "faturamento_total_expedido": 6300.00,
    "peso_total_expedido_kg": 2420.00,
    "volume_total_expedido_m3": 2.45,
    "taxa_atendimento_pedidos_pct": 100.0
  },
  "cargas_caminhao": [
    {
      "viagem_id": "VIAGEM-eixo-1-ipaporanga-poranga-V1",
      "viagem_numero": 1,
      "titulo": "Eixo 1 (Ipaporanga / Poranga) — Viagem 1",
      "eixo_id": "eixo-1-ipaporanga-poranga",
      "eixo_nome": "Eixo 1 (Ipaporanga / Poranga)",
      "veiculo": {
        "id": "accelo-815-01",
        "nome": "Mercedes-Benz Accelo 815 (Caminhão Médio)",
        "placa": "POC-8151",
        "tipo_carroceria": "Carroceria Aberta (Grade Baixa)",
        "capacidade_kg": 4800.0,
        "volume_util_m3": 18.5,
        "permite_barras_6m": true
      },
      "total_pedidos": 2,
      "peso_total_kg": 2420.0,
      "volume_total_m3": 2.45,
      "faturamento_total": 6300.0,
      "ocupacao_peso_pct": 50.42,
      "ocupacao_volume_pct": 13.24,
      "recurso_limitante": "PESO",
      "alerta_carroceria": "Carroceria aberta — Carga com tubos/barras lineares de 6m: fixar com cintas e catracas no assoalho lateral.",
      "pedidos_carroceria": [
        {
          "pedido": "L12608401",
          "external_id": "L12608401",
          "ordem_carregamento": 1,
          "posicao_carroceria": "Frente da Carroceria (Fundo do Assoalho)",
          "ordem_entrega_prevista": 2,
          "cliente": "AGROPECUARIA IPAPORANGA",
          "cidade": "IPAPORANGA",
          "endereco": "Rua Franklin José Vieira, 100, Centro, CEP 62290-000, Ipaporanga - CE",
          "situacao": "URGENTE",
          "peso_total_kg": 2300.0,
          "volume_total_m3": 1.45,
          "valor_total": 4800.0,
          "urgente": true,
          "possui_itens_6m": false,
          "pagamento_na_entrega": null,
          "itens": [
            {
              "codigo": "21503",
              "descricao": "CIMENTO POTY TODAS OBRAS 50KG",
              "quantidade": 40.0,
              "unidade": "UN",
              "peso_unitario_kg": 50.0,
              "peso_total_kg": 2000.0,
              "volume_total_m3": 1.15,
              "e_item_6m": false,
              "cubagem_estimada": false
            }
          ]
        },
        {
          "pedido": "L12608402",
          "external_id": "L12608402",
          "ordem_carregamento": 2,
          "posicao_carroceria": "Traseira da Carroceria",
          "ordem_entrega_prevista": 1,
          "cliente": "FERRAGISTA E HIDRAULICA DO NORTE",
          "cidade": "IPAPORANGA",
          "endereco": "Av. 22 de Setembro, 240, Centro, Ipaporanga - CE",
          "situacao": "URGENTE",
          "peso_total_kg": 120.0,
          "volume_total_m3": 1.0,
          "valor_total": 1500.0,
          "urgente": true,
          "possui_itens_6m": true,
          "pagamento_na_entrega": "A RECEBER",
          "itens": [
            {
              "codigo": "10200",
              "descricao": "TUBO ESGOTO 100MM 6M TIGRE",
              "quantidade": 15.0,
              "unidade": "UN",
              "peso_unitario_kg": 8.0,
              "peso_total_kg": 120.0,
              "volume_total_m3": 1.0,
              "e_item_6m": true,
              "cubagem_estimada": false
            }
          ]
        }
      ]
    }
  ],
  "roteiros_entrega": [
    {
      "viagem_id": "VIAGEM-eixo-1-ipaporanga-poranga-V1",
      "viagem_numero": 1,
      "titulo": "Eixo 1 (Ipaporanga / Poranga) — Viagem 1",
      "eixo_id": "eixo-1-ipaporanga-poranga",
      "eixo_nome": "Eixo 1 (Ipaporanga / Poranga)",
      "total_paradas": 2,
      "faturamento_total": 6300.0,
      "total_a_receber_rota": 1500.0,
      "distancia_estimada_km": 44.8,
      "paradas": [
        {
          "parada": 1,
          "pedido": "L12608402",
          "external_id": "L12608402",
          "cliente": "FERRAGISTA E HIDRAULICA DO NORTE",
          "cidade": "IPAPORANGA",
          "endereco_completo": "Av. 22 de Setembro, 240, Centro, Ipaporanga - CE",
          "posicao_na_carroceria": "Traseira da Carroceria",
          "situacao": "URGENTE",
          "valor_pedido": 1500.0,
          "status_pagamento": "A RECEBER",
          "valor_a_receber": 1500.0,
          "alerta_cobranca": "Exigir comprovante PIX/Dinheiro antes do descarregamento!",
          "peso_total_kg": 120.0,
          "volume_total_m3": 1.0,
          "possui_itens_6m": true,
          "itens": [ ... ]
        },
        {
          "parada": 2,
          "pedido": "L12608401",
          "external_id": "L12608401",
          "cliente": "AGROPECUARIA IPAPORANGA",
          "cidade": "IPAPORANGA",
          "endereco_completo": "Rua Franklin José Vieira, 100, Centro, CEP 62290-000, Ipaporanga - CE",
          "posicao_na_carroceria": "Frente da Carroceria (Fundo do Assoalho)",
          "situacao": "URGENTE",
          "valor_pedido": 4800.0,
          "status_pagamento": "QUITADO",
          "valor_a_receber": 0.0,
          "alerta_cobranca": null,
          "peso_total_kg": 2300.0,
          "volume_total_m3": 1.45,
          "possui_itens_6m": false,
          "itens": [ ... ]
        }
      ]
    }
  ],
  "descartes_limpeza": []
}
```

---

## 7. Exemplo de Integração Frontend (React + Axios / Fetch)

### Serviço API (`src/services/dispatchService.ts`):
```typescript
import axios from 'axios';
import {
  OrderInput,
  DecoupledDispatchResponse,
  TruckLoadResponse,
  DeliveryRouteResponse
} from '../types/dispatch';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1/dispatch';

export const dispatchService = {
  /**
   * Obtém a coleção mock oficial para testar a interface.
   */
  async getMockOrders(): Promise<OrderInput[]> {
    const res = await axios.get<OrderInput[]>(`${API_BASE_URL}/mock-orders`);
    return res.data;
  },

  /**
   * Consulta direta via GET: Carrega as cargas nos caminhões (Carroceria Aberta).
   * Não requer envio de body! Ideal para renderizar a tela inicial.
   */
  async getTruckLoad(perfilOtimizacao = 'Equilibrado'): Promise<TruckLoadResponse> {
    const res = await axios.get<TruckLoadResponse>(`${API_BASE_URL}/truck-load`, {
      params: { perfil_otimizacao: perfilOtimizacao }
    });
    return res.data;
  },

  /**
   * Consulta direta via GET: Carrega o roteiro de entrega TSP.
   * Não requer envio de body! Ideal para renderizar a tela de rotas.
   */
  async getDeliveryRoute(perfilOtimizacao = 'Equilibrado'): Promise<DeliveryRouteResponse> {
    const res = await axios.get<DeliveryRouteResponse>(`${API_BASE_URL}/delivery-route`, {
      params: { perfil_otimizacao: perfilOtimizacao }
    });
    return res.data;
  },

  /**
   * Processa um lote customizado de pedidos enviado pelo usuário via POST.
   */
  async processOrders(
    pedidos: OrderInput[],
    perfilOtimizacao = 'Equilibrado'
  ): Promise<DecoupledDispatchResponse> {
    const res = await axios.post<DecoupledDispatchResponse>(`${API_BASE_URL}/process-orders`, {
      pedidos,
      perfil_otimizacao: perfilOtimizacao,
      tempo_limite_segundos: 20.0
    });
    return res.data;
  },

  /**
   * Dispara o download do PDF oficial de carregamento da carroceria.
   */
  async downloadLoadingSheetPdf(tripId: string): Promise<void> {
    const response = await axios.get(`${API_BASE_URL}/trips/${tripId}/pdf/loading-sheet`, {
      responseType: 'blob'
    });
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `mapa_carregamento_${tripId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  /**
   * Dispara o download do PDF oficial do roteiro TSP de entrega.
   */
  async downloadDeliveryRoutePdf(tripId: string): Promise<void> {
    const response = await axios.get(`${API_BASE_URL}/trips/${tripId}/pdf/delivery-route`, {
      responseType: 'blob'
    });
    const blob = new Blob([response.data], { type: 'application/pdf' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `roteiro_entregas_${tripId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }
};
```

---

## 8. Recomendações de UI/UX para o Frontend

1. **Visão 1: Cartões de Viagem e Carroceria Aberta**:
   - Renderizar barra de progresso dupla: **Ocupação de Peso (%)** e **Ocupação de Volume (%)**;
   - Se houver `alerta_carroceria`, renderizar um banner de atenção âmbar/laranja destacando a fixação de barras e tubos de 6 metros;
   - Mostrar a lista de pedidos ordenados por `ordem_carregamento`:
     - Badge da posição: `"Frente / Fundo"`, `"Meio"`, `"Traseira"`;
     - Botão expansível com ícone chevron para acionar o **Drill-Down de Itens** do pedido;
   - Botão no cabeçalho do cartão: **"Baixar Mapa de Carregamento (PDF)"**.

2. **Visão 2: Ordem de Entrega (Roteiro TSP)**:
   - Renderizar as paradas como uma linha do tempo vertical (1ª parada, 2ª parada...);
   - Exibir badge com o município e endereço completo;
   - Se `status_pagamento === "A RECEBER"`, destacar em vermelho com o valor e o aviso de cobrança obrigatória;
   - Acordeão do drill-down mostrando exatamente os produtos a descarregar naquela residência ou obra;
   - Botão no topo da rota: **"Baixar Roteiro de Entregas (PDF)"**.

3. **Seção de Auditoria (Descartes de Limpeza)**:
   - Tabela colapsável mostrando os pedidos retirados no balcão e os cancelados, informando o motivo da higienização automática (`motivo`), garantindo total transparência com o operador logístico.
