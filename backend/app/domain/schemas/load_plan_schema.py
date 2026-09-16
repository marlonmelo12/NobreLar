"""Esquemas Pydantic v2 para requisições e respostas de planos de carga, decisões e auditoria."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class OptimizeRequest(BaseModel):
    """Contrato de solicitação de otimização de carga para um par (Eixo, Veículo)."""
    axis_id: str = Field(..., description="Identificador do eixo rodoviário (ex: eixo-4-norte-serra)")
    vehicle_id: str = Field(..., description="Identificador do veículo da frota (ex: accelo-815-01)")
    profile_id: Optional[int] = Field(None, description="ID do perfil de otimização (se None, usa o default)")
    time_limit_seconds: float = Field(30.0, ge=1.0, le=120.0, description="Tempo limite em segundos para o solver")
    mandatory_order_ids: Optional[List[str]] = Field(None, description="Lista de IDs de pedidos obrigatórios (SLA)")


class LoadPlanItemResponse(BaseModel):
    """Contrato do pedido alocado na carga, incluindo sequência LIFO."""
    id: int
    order_id: str
    delivery_order: int
    loading_order: int
    score: float
    efficiency: float
    weight_kg: float
    volume_m3: float
    value: float
    city_name: str
    address_line: Optional[str] = None
    payment_on_delivery: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class LoadPlanDecisionResponse(BaseModel):
    """Contrato explicável do motivo de inclusão ou exclusão de cada pedido."""
    order_id: str
    included: bool
    score: float
    efficiency: float
    peso_pct: float
    volume_pct: float
    exclusion_reason: str

    model_config = ConfigDict(from_attributes=True)


class LoadPlanAuditResponse(BaseModel):
    """Registro de auditoria de modificações manuais e aprovações."""
    id: int
    user_id: str
    action: str
    order_id: Optional[str] = None
    accepted: bool
    rejection_reason: Optional[str] = None
    weight_before: Optional[float] = None
    weight_after: Optional[float] = None
    volume_before: Optional[float] = None
    volume_after: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoadPlanResponse(BaseModel):
    """Contrato detalhado do plano de carga gerado pelo otimizador ou editado."""
    id: int
    execution_id: str
    axis_id: str
    vehicle_id: str
    profile_id: int
    profile_snapshot: Dict[str, Any]

    total_orders: int
    total_value: float
    total_weight_kg: float
    total_volume_m3: float
    weight_occupancy: float
    volume_occupancy: float
    limiting_resource: str
    estimated_cubing_pct: float

    solver_status: str
    optimality_gap: Optional[float] = None
    solve_duration_ms: int
    algorithm_version: str

    is_manually_modified: bool
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    valid: bool
    created_by: str
    created_at: datetime

    items: List[LoadPlanItemResponse] = []
    decisions: List[LoadPlanDecisionResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ToggleItemRequest(BaseModel):
    """Contrato para inclusão ou remoção manual de um pedido no plano."""
    order_id: str = Field(..., description="ID do pedido a ser alternado (incluído/removido)")


class ApprovePlanRequest(BaseModel):
    """Contrato para aprovação formal do plano de carga."""
    approver_name: Optional[str] = Field(None, description="Nome do aprovador responsável")
