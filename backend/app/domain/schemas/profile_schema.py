"""Esquemas Pydantic v2 para perfis de otimização multicritério."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict


class ProfileCreate(BaseModel):
    """Contrato de criação de um novo perfil de otimização."""
    name: str = Field(..., description="Nome do perfil (ex: Comercial, Capacidade)")
    w_peso: float = Field(0.25, ge=0.0, le=1.0, description="Peso para consumo de kg")
    w_volume: float = Field(0.25, ge=0.0, le=1.0, description="Peso para consumo de m³")
    w_valor: float = Field(0.30, ge=0.0, le=1.0, description="Peso para valor faturado")
    w_quantidade: float = Field(0.20, ge=0.0, le=1.0, description="Peso para frequência de vendas")
    objective_mode: str = Field("score_agregado", description="'score_agregado' ou 'eficiencia'")
    is_default: bool = Field(False, description="Se é o perfil padrão da operação")
    description: Optional[str] = Field(None, description="Descrição operacional do perfil")

    @field_validator("w_quantidade")
    @classmethod
    def validate_weights_sum(cls, v, info):
        """Valida que a soma dos 4 pesos seja rigorosamente 1.0 (RF-009-B)."""
        data = info.data
        w_p = data.get("w_peso", 0.0)
        w_v = data.get("w_volume", 0.0)
        w_val = data.get("w_valor", 0.0)
        tot = w_p + w_v + w_val + v
        if abs(tot - 1.0) > 1e-5:
            raise ValueError(f"A soma dos pesos deve ser exatamente 1.0 (obtido: {tot:.4f}).")
        return v


class ProfileResponse(BaseModel):
    """Contrato de leitura de um perfil de otimização."""
    id: int
    name: str
    w_peso: float
    w_volume: float
    w_valor: float
    w_quantidade: float
    objective_mode: str
    is_default: bool
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
