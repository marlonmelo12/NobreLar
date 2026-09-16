"""Módulo de esquemas de dados Pydantic v2 do NobreLOG IA."""

from app.domain.schemas.auth_schema import LoginRequest, TokenResponse
from app.domain.schemas.vehicle_schema import VehicleResponse
from app.domain.schemas.profile_schema import ProfileCreate, ProfileResponse
from app.domain.schemas.order_schema import OrderItemResponse, OrderResponse
from app.domain.schemas.load_plan_schema import (
    OptimizeRequest,
    LoadPlanItemResponse,
    LoadPlanDecisionResponse,
    LoadPlanAuditResponse,
    LoadPlanResponse,
    ToggleItemRequest,
    ApprovePlanRequest,
)
from app.domain.schemas.cleaning_log_schema import CleaningLogResponse

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "VehicleResponse",
    "ProfileCreate",
    "ProfileResponse",
    "OrderItemResponse",
    "OrderResponse",
    "OptimizeRequest",
    "LoadPlanItemResponse",
    "LoadPlanDecisionResponse",
    "LoadPlanAuditResponse",
    "LoadPlanResponse",
    "ToggleItemRequest",
    "ApprovePlanRequest",
    "CleaningLogResponse",
]
