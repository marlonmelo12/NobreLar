"""Esquemas Pydantic v2 para registros de limpeza e descartes."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class CleaningLogResponse(BaseModel):
    """Contrato do log de higienização e descarte de dados."""
    id: int
    execution_id: Optional[str] = None
    record_reference: str
    rule_applied: str
    action: str
    field: str
    original_value: Optional[str] = None
    corrected_value: Optional[str] = None
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
