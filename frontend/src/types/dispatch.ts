/**
 * Tipos TypeScript Canônicos — NobreLOG IA (Expedição Desacoplada)
 * Alinhado 100% aos contratos JSON e schemas da API FastAPI.
 */

export enum SituacaoPedidoEnum {
  NORMAL = 'NORMAL',
  URGENTE = 'URGENTE',
  RETIRADA = 'RETIRADA',
  CARRO_HORARIO = 'CARRO HORARIO',
  PROGRAMADO = 'PROGRAMADO',
  TOPIQUE = 'TOPIQUE',
  CANCELADO = 'CANCELADO',
}

export type RecursoLimitante = 'PESO' | 'VOLUME';

export type StatusPagamento = 'A RECEBER' | 'QUITADO';

// ---------------------------------------------------------------------------
// Item no Drill-Down Aninhado (Entrada e Saída)
// ---------------------------------------------------------------------------
export interface ItemPedidoInput {
  codigo: string;
  descricao: string;
  quantidade: number;
  unidade: string;
  preco_unitario?: number;
  subtotal?: number;
}

export interface ItemDrillDown {
  codigo: string;
  descricao: string;
  quantidade: number;
  unidade: string;
  preco_unitario: number;
  peso_unitario_kg: number;
  peso_total_kg: number;
  volume_total_m3: number;
  e_item_6m: boolean;
  cubagem_estimada: boolean;
}

// ---------------------------------------------------------------------------
// Pedido de Entrada (JSON enviado pelo ERP/Frontend)
// ---------------------------------------------------------------------------
export interface DecoupledOrderInput {
  id: string;
  data?: string;
  vendedor?: string;
  cliente?: string;
  cidade: string;
  endereco: string;
  valor: number;
  urgente?: boolean;
  situacao: string;
  pagamento_entrega?: string | null;
  itens: ItemPedidoInput[];
}

export interface DecoupledBatchRequest {
  pedidos: DecoupledOrderInput[];
  perfil_otimizacao?: 'Equilibrado' | 'Priorizar Urgentes' | 'Minimizar Veículos';
  tempo_limite_segundos?: number;
}

// ---------------------------------------------------------------------------
// Contratos de Carga no Caminhão (Carroceria Aberta + LIFO)
// ---------------------------------------------------------------------------
export interface VeiculoCarroceriaInfo {
  id: string;
  nome: string;
  placa: string;
  tipo_carroceria: string;
  capacidade_kg: number;
  volume_util_m3: number;
  permite_barras_6m: boolean;
}

export interface PedidoCarroceriaItem {
  pedido: string;
  external_id: string;
  ordem_carregamento: number;
  posicao_carroceria: string;
  ordem_entrega_prevista: number;
  cliente: string | null;
  cidade: string;
  endereco: string;
  situacao: string;
  peso_total_kg: number;
  volume_total_m3: number;
  valor_total: number;
  urgente: boolean;
  possui_itens_6m: boolean;
  pagamento_na_entrega: string | null;
  itens: ItemDrillDown[];
}

export interface CargaCaminhaoViagem {
  viagem_id: string;
  viagem_numero: number;
  titulo: string;
  eixo_id: string;
  eixo_nome: string;
  veiculo: VeiculoCarroceriaInfo;
  total_pedidos: number;
  peso_total_kg: number;
  volume_total_m3: number;
  faturamento_total: number;
  ocupacao_peso_pct: number;
  ocupacao_volume_pct: number;
  recurso_limitante: RecursoLimitante;
  alerta_carroceria: string;
  pedidos_carroceria: PedidoCarroceriaItem[];
}

export interface TruckLoadResponse {
  status: string;
  total_viagens: number;
  viagens: CargaCaminhaoViagem[];
}

// ---------------------------------------------------------------------------
// Contratos de Ordem de Entrega (Roteirização TSP)
// ---------------------------------------------------------------------------
export interface VeiculoRotaInfo {
  id: string;
  nome: string;
  placa: string;
  tipo: string;
}

export interface ParadaEntregaItem {
  parada: number;
  pedido: string;
  external_id: string;
  cliente: string | null;
  cidade: string;
  endereco_completo: string;
  posicao_na_carroceria: string;
  situacao: string;
  valor_pedido: number;
  status_pagamento: StatusPagamento;
  valor_a_receber: number;
  alerta_cobranca: string | null;
  peso_total_kg: number;
  volume_total_m3: number;
  possui_itens_6m: boolean;
  itens: ItemDrillDown[];
}

export interface RoteiroEntregaViagem {
  viagem_id: string;
  viagem_numero: number;
  titulo: string;
  eixo_id: string;
  eixo_nome: string;
  veiculo: VeiculoRotaInfo;
  total_paradas: number;
  faturamento_total: number;
  total_a_receber_rota: number;
  distancia_estimada_km: number;
  paradas: ParadaEntregaItem[];
}

export interface DeliveryRouteResponse {
  status: string;
  total_viagens: number;
  viagens: RoteiroEntregaViagem[];
}

// ---------------------------------------------------------------------------
// Contratos de Descartes e Resumo Consolidado
// ---------------------------------------------------------------------------
export interface DiscardedCleaningLog {
  pedido: string;
  regra: string;
  motivo: string;
}

export interface DispatchSummary {
  total_records_read: number;
  total_discarded_cleaning: number;
  total_valid_deliveries: number;
  total_allocated_orders: number;
  total_unallocated_orders: number;
  total_trips_generated: number;
  total_invoiced_value: number;
  total_allocated_weight_kg: number;
  total_allocated_volume_m3: number;
}

export interface DecoupledDispatchResponse {
  status: string;
  resumo: DispatchSummary;
  cargas_caminhao: CargaCaminhaoViagem[];
  roteiros_entrega: RoteiroEntregaViagem[];
  descartes_limpeza: DiscardedCleaningLog[];
}
