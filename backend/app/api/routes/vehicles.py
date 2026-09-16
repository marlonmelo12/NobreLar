"""Rotas de consulta e gestão da frota de veículos."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domain.models import Vehicle
from app.domain.schemas.vehicle_schema import VehicleResponse

router = APIRouter(prefix="/vehicles", tags=["Veículos"])


@router.get("", response_model=List[VehicleResponse], summary="Listar frota de veículos")
def list_vehicles(db: Session = Depends(get_db)):
    """Retorna todos os veículos ativos cadastrados na frota."""
    return db.query(Vehicle).filter(Vehicle.active == True).all()


@router.get("/{vehicle_id}", response_model=VehicleResponse, summary="Detalhes do veículo")
def get_vehicle(vehicle_id: str, db: Session = Depends(get_db)):
    """Retorna os dados técnicos e restrições operacionais de um veículo."""
    v = db.query(Vehicle).filter(Vehicle.id == vehicle_id).first()
    if not v:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")
    return v
