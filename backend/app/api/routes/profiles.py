"""Rotas de perfis de otimização multicritério."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domain.models import OptimizationProfile
from app.domain.schemas.profile_schema import ProfileCreate, ProfileResponse

router = APIRouter(prefix="/optimization-profiles", tags=["Perfis de Otimização"])


@router.get("", response_model=List[ProfileResponse], summary="Listar perfis de otimização")
def list_profiles(db: Session = Depends(get_db)):
    """Retorna todos os perfis configurados de pesos multicritério."""
    return db.query(OptimizationProfile).all()


@router.post("", response_model=ProfileResponse, status_code=status.HTTP_201_CREATED, summary="Criar novo perfil")
def create_profile(profile_in: ProfileCreate, db: Session = Depends(get_db)):
    """Cadastra um novo perfil de otimização validando rigorosamente a soma dos pesos igual a 1.0."""
    existing = db.query(OptimizationProfile).filter(OptimizationProfile.name == profile_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Já existe um perfil cadastrado com o nome '{profile_in.name}'."
        )

    # Se este perfil for marcado como default, remove o default anterior
    if profile_in.is_default:
        db.query(OptimizationProfile).update({OptimizationProfile.is_default: False})

    p = OptimizationProfile(
        name=profile_in.name,
        w_peso=profile_in.w_peso,
        w_volume=profile_in.w_volume,
        w_valor=profile_in.w_valor,
        w_quantidade=profile_in.w_quantidade,
        objective_mode=profile_in.objective_mode,
        is_default=profile_in.is_default,
        description=profile_in.description,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p
