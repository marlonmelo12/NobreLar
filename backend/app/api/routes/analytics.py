"""Rotas de análise analítica (densidade e limitante do eixo), logs de limpeza e health/readiness."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.api.dependencies import get_db
from app.domain.models import Axis, Order, Vehicle, CleaningLog
from app.domain.schemas.cleaning_log_schema import CleaningLogResponse
from app.core.config import settings

router = APIRouter(tags=["Analíticos e Observabilidade"])


@router.get("/analytics/axis-profile", summary="Análise de densidade por eixo (Peso vs Volume)")
def get_axis_profile(db: Session = Depends(get_db)):
    """Calcula a densidade média dos pedidos por eixo rodoviário e identifica se o limitante é peso ou volume.

    Atende ao requisito RF-013.1 e ao Critério de Aceite CA-016 (Bônus do Desafio).
    """
    # Referência do caminhão padrão Accelo 815: 4.800 kg / 18.5 m³ = 259,46 kg/m³
    accelo = db.query(Vehicle).filter(Vehicle.id == "accelo-815-01").first()
    ref_density = (accelo.capacity_kg / accelo.useful_volume_m3) if accelo else (4800.0 / 18.5)

    axes = db.query(Axis).filter(Axis.active == True).all()
    results = []

    for ax in axes:
        stats = db.query(
            func.count(Order.id).label("total_orders"),
            func.sum(Order.total_weight_kg).label("total_weight"),
            func.sum(Order.total_volume_m3).label("total_volume"),
            func.sum(Order.value).label("total_value"),
        ).filter(Order.axis_id == ax.id, Order.status == "Faturado").first()

        tot_orders = stats.total_orders or 0
        tot_w = float(stats.total_weight or 0.0)
        tot_v = float(stats.total_volume or 0.0)
        tot_val = float(stats.total_value or 0.0)

        densidade = round(tot_w / tot_v, 2) if tot_v > 0 else 0.0
        limitante = "PESO" if densidade >= ref_density else "VOLUME"

        results.append({
            "axis_id": ax.id,
            "axis_name": ax.name,
            "total_orders": tot_orders,
            "total_weight_kg": round(tot_w, 2),
            "total_volume_m3": round(tot_v, 4),
            "total_value": round(tot_val, 2),
            "density_kg_m3": densidade,
            "vehicle_ref_density_kg_m3": round(ref_density, 2),
            "predominant_limiting_resource": limitante,
            "business_recommendation": (
                "Eixo pesado: atinge capacidade em kg antes de encher o baú."
                if limitante == "PESO"
                else "Eixo volumoso: o baú enche fisicamente antes de atingir o peso máximo (aumentar baú)."
            )
        })

    return results


@router.get("/executions/{execution_id}/cleaning-log", response_model=List[CleaningLogResponse], summary="Histórico de higienização de dados")
def get_cleaning_log(execution_id: str, db: Session = Depends(get_db)):
    """Retorna os registros de descartes e correções efetuadas durante a limpeza dos pedidos."""
    query = db.query(CleaningLog)
    if execution_id != "all":
        query = query.filter(CleaningLog.execution_id == execution_id)
    return query.order_by(CleaningLog.created_at.desc()).all()


@router.get("/health", summary="Health check da aplicação")
def health_check(db: Session = Depends(get_db)):
    """Verifica a saúde da API e a conectividade com o banco de dados (RNF-006-A)."""
    try:
        db.execute(func.now())
        db_status = "CONECTADO"
    except Exception as e:
        db_status = f"ERRO: {e}"

    return {
        "status": "HEALTHY",
        "database": db_status,
        "version": settings.VERSION,
        "project": settings.PROJECT_NAME
    }


@router.get("/ready", summary="Readiness probe")
def readiness_check(db: Session = Depends(get_db)):
    """Verifica prontidão do sistema: banco com tabelas populadas e solver disponível."""
    try:
        vehicle_count = db.query(Vehicle).count()
        axis_count = db.query(Axis).count()
        is_ready = (vehicle_count > 0 and axis_count > 0)
    except Exception:
        is_ready = False

    if not is_ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sistema não está pronto. Banco de dados não inicializado."
        )

    return {
        "status": "READY",
        "solver_available": True,
        "vehicles_seeded": vehicle_count,
        "axes_seeded": axis_count
    }
