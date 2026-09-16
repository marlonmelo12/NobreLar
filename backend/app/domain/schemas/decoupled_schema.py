"""Esquemas Pydantic v2 para API Desacoplada: Carroceria Aberta e Drill-Down de Itens.

Implementa a estrutura canônica dos pedidos, suporte a carroceria aberta (sem menções a doca/baú)
e contratos JSON com itens aninhados para consumo direto pelo Frontend.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# 0. Enums de Negócio do Domínio Nobre Lar
# ---------------------------------------------------------------------------
class SituacaoPedidoEnum(str, Enum):
    """Situação operacional canônica extraída do CSV/ERP da Nobre Lar."""
    NORMAL = "NORMAL"
    URGENTE = "URGENTE"
    RETIRADA = "RETIRADA"
    CARRO_HORARIO = "CARRO HORARIO"
    PROGRAMADO = "PROGRAMADO"
    TOPIQUE = "TOPIQUE"
    CANCELADO = "CANCELADO"


# ---------------------------------------------------------------------------
# 1. Esquemas de Entrada (JSON Ingestion)
# ---------------------------------------------------------------------------
class DecoupledItemInput(BaseModel):
    """Item componente de um pedido faturado."""
    codigo: Optional[str] = Field(None, alias="product_code", description="Código SKU do produto")
    descricao: str = Field(..., alias="product_desc", description="Descrição do produto")
    quantidade: float = Field(1.0, alias="quantity", ge=0.001, description="Quantidade do produto")
    unidade: str = Field("UN", alias="unit", description="Unidade de medida (UN, MT, KG, CX)")
    preco_unitario: Optional[float] = Field(0.0, alias="unit_price", description="Preço bruto unitário")
    subtotal: Optional[float] = Field(0.0, description="Subtotal do item")

    model_config = ConfigDict(populate_by_name=True)


class DecoupledOrderInput(BaseModel):
    """Pedido faturado de venda enviado para processamento logístico."""
    id: str = Field(..., alias="pedido", description="Identificador único ou número do pedido (ex: L12608361)")
    data: Optional[str] = Field(None, description="Data de emissão (ex: 03/08/2026)")
    vendedor: Optional[str] = Field(None, description="Nome do vendedor")
    cliente: Optional[str] = Field(None, description="Nome do cliente destinatário")
    cidade: str = Field(..., alias="city", description="Cidade ou distrito de entrega")
    endereco: Optional[str] = Field(None, alias="address", description="Endereço completo de entrega")
    valor: Optional[float] = Field(0.0, alias="total_pedido", description="Valor líquido total do pedido")
    urgente: bool = Field(False, alias="is_urgent", description="Flag de prioridade máxima")
    situacao: str = Field(
        SituacaoPedidoEnum.NORMAL.value,
        description="Situação operacional canônica: NORMAL, URGENTE, RETIRADA, CARRO HORARIO, PROGRAMADO, TOPIQUE, CANCELADO"
    )
    pagamento_entrega: Optional[str] = Field(None, description="'A RECEBER', 'SIM' ou None se já quitado")
    itens: List[DecoupledItemInput] = Field(default_factory=list, description="Lista de itens do pedido")

    model_config = ConfigDict(populate_by_name=True)


class DecoupledBatchRequest(BaseModel):
    """Lote de pedidos faturados para processamento e roteirização."""
    pedidos: List[DecoupledOrderInput] = Field(..., description="Lista de pedidos faturados")
    perfil_otimizacao: Optional[str] = Field("Equilibrado", description="Perfil de otimização de frota")
    tempo_limite_segundos: Optional[float] = Field(20.0, ge=1.0, le=120.0, description="Tempo limite do solver por viagem")


# ---------------------------------------------------------------------------
# 2. Esquemas de Saída com Drill-Down de Itens
# ---------------------------------------------------------------------------
class ItemDrillDown(BaseModel):
    """Drill-down detalhado de cada produto contido no pedido."""
    codigo: str
    descricao: str
    quantidade: float
    unidade: str
    peso_unitario_kg: float
    peso_total_kg: float
    volume_total_m3: float
    e_item_6m: bool
    cubagem_estimada: bool


# --- VISÃO 1: Carga no Caminhão (Carroceria Aberta) ---
class TruckLoadOrderItem(BaseModel):
    """Pedido posicionado na carroceria aberta do caminhão com itens aninhados."""
    pedido: str
    external_id: str
    ordem_carregamento: int
    posicao_carroceria: Optional[str] = None
    ordem_entrega_prevista: int
    cliente: Optional[str] = None
    cidade: str
    endereco: Optional[str] = None
    situacao: str = Field("NORMAL", description="Situação operacional: NORMAL, URGENTE, CARRO HORARIO, etc.")
    peso_total_kg: float
    volume_total_m3: float
    valor_total: float
    urgente: bool
    possui_itens_6m: bool
    pagamento_na_entrega: Optional[str] = None
    itens: List[ItemDrillDown] = []  # DRILL-DOWN ANINHADO


class TruckLoadTrip(BaseModel):
    """Plano de carga de uma viagem em caminhão de carroceria aberta."""
    viagem_id: str
    viagem_numero: int
    titulo: str
    eixo_id: str
    eixo_nome: str
    veiculo: Dict[str, Any]
    total_pedidos: int
    peso_total_kg: float
    volume_total_m3: float
    faturamento_total: float
    ocupacao_peso_pct: float
    ocupacao_volume_pct: float
    recurso_limitante: str
    alerta_carroceria: Optional[str] = None
    pedidos_carroceria: List[TruckLoadOrderItem] = []


class TruckLoadResponse(BaseModel):
    """Resposta formatada para a tela de Carregamento na Carroceria Aberta."""
    status: str
    total_viagens: int
    viagens: List[TruckLoadTrip]


# --- VISÃO 2: Ordem de Entrega (Roteiro TSP) ---
class DeliveryRouteStopItem(BaseModel):
    """Parada de entrega com dados completos de rota, cobrança e drill-down de itens."""
    parada: int
    pedido: str
    external_id: str
    cliente: Optional[str] = None
    cidade: str
    endereco_completo: str
    posicao_na_carroceria: Optional[str] = None
    situacao: str = Field("NORMAL", description="Situação operacional: NORMAL, URGENTE, CARRO HORARIO, etc.")
    valor_pedido: float
    status_pagamento: str  # "QUITADO" ou "A RECEBER"
    valor_a_receber: float
    alerta_cobranca: Optional[str] = None
    peso_total_kg: float
    volume_total_m3: float
    possui_itens_6m: bool
    itens: List[ItemDrillDown] = []  # DRILL-DOWN ANINHADO


class DeliveryRouteTrip(BaseModel):
    """Roteiro de entregas de uma viagem avaliado pelo Caixeiro Viajante (TSP)."""
    viagem_id: str
    viagem_numero: int
    titulo: str
    eixo_id: str
    eixo_nome: str
    veiculo: Dict[str, Any]
    total_paradas: int
    faturamento_total: float
    total_a_receber_rota: float
    distancia_estimada_km: float
    paradas: List[DeliveryRouteStopItem] = []


class DeliveryRouteResponse(BaseModel):
    """Resposta formatada para a tela de Ordem de Entregas (TSP)."""
    status: str
    total_viagens: int
    viagens: List[DeliveryRouteTrip]


# --- VISÃO 3: Resposta Consolidada Completa ---
class PedidoNaoAlocadoItem(BaseModel):
    """Pedido validado porém não alocado em nenhuma viagem da janela atual."""
    pedido: str
    external_id: str
    cliente: Optional[str] = None
    cidade: str
    eixo_id: Optional[str] = None
    endereco: Optional[str] = None
    situacao: str = "NORMAL"
    peso_total_kg: float = 0.0
    volume_total_m3: float = 0.0
    valor_total: float = 0.0
    urgente: bool = False
    motivo: str = "Capacidade ou disponibilidade de frota excedida"
    itens: List[Dict[str, Any]] = []


class DecoupledDispatchResponse(BaseModel):
    """Resposta consolidada que fornece ambas as visões (Carroceria e Roteiro TSP) mais não alocados."""
    status: str
    resumo: Dict[str, Any]
    cargas_caminhao: List[TruckLoadTrip]
    roteiros_entrega: List[DeliveryRouteTrip]
    descartes_limpeza: List[Dict[str, Any]]
    pedidos_nao_alocados: List[PedidoNaoAlocadoItem] = []


# --- VISÃO 4: Listagem Unificada de Todos os Pedidos ---
class UnifiedOrderItem(BaseModel):
    """Representação unificada de um pedido para a tela geral de pedidos."""
    id: str
    external_id: str
    cliente: Optional[str] = None
    cidade: Optional[str] = None
    endereco: Optional[str] = None
    situacao: str = "NORMAL"
    peso_kg: float = 0.0
    volume_m3: float = 0.0
    valor: float = 0.0
    status: str = "PENDENTE"  # ALOCADO | NAO_ALOCADO | DESCARTADO | PENDENTE
    status_label: str = "Pendente"
    viagem_id: Optional[str] = None
    viagem_titulo: Optional[str] = None
    veiculo_nome: Optional[str] = None
    veiculo_placa: Optional[str] = None
    eixo_nome: Optional[str] = None
    ordem_carregamento: Optional[int] = None
    ordem_entrega: Optional[int] = None
    motivo: Optional[str] = None
    itens: List[Dict[str, Any]] = []


class AllOrdersResponse(BaseModel):
    """Resposta com todos os pedidos do sistema (alocados, não alocados e descartados)."""
    status: str
    total: int
    total_alocados: int
    total_nao_alocados: int
    total_descartados: int
    pedidos: List[UnifiedOrderItem] = []

