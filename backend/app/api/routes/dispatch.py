"""Rotas da API para o pipeline de faturamento diário e expedição multi-viagens."""

import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Response
from sqlalchemy.orm import Session
import structlog

from app.core.config import settings
from app.infrastructure.database.session import get_db
from app.services.dispatch_pipeline import DailyDispatchPipeline
from app.services.report_service import ReportService

logger = structlog.get_logger()
router = APIRouter(prefix="/dispatch", tags=["Expedição Diária & Multi-Viagens"])


@router.post(
    "/daily-pipeline",
    summary="Processa arquivo de faturamento diário com filtros, eixos e múltiplas viagens",
    description="Recebe o CSV de faturamento completo do dia, descarta vendas de balcão e cancelados, "
                "prioriza pedidos urgentes, classifica por eixos e aloca os caminhões em viagens sucessivas."
)
async def process_daily_dispatch(
    file: UploadFile = File(..., description="Arquivo CSV de faturamento diário"),
    profile_name: str = Form("Equilibrado", description="Perfil de otimização (Equilibrado, Comercial, etc.)"),
    time_limit_seconds: float = Form(20.0, description="Tempo limite do solver por viagem"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Processa o upload de um CSV diário e gera o plano consolidado de viagens."""
    if not file.filename.endswith((".csv", ".txt")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato inválido. Envie um arquivo CSV com separador ';' ou ','."
        )

    # Grava arquivo temporário seguro
    with NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = Path(tmp.name)

    try:
        pipeline = DailyDispatchPipeline(db=db)
        result = pipeline.process_daily_billing(
            csv_file_path_or_df=tmp_path,
            profile_name=profile_name,
            time_limit_seconds=time_limit_seconds
        )
        return result
    except Exception as e:
        logger.error(f"Erro no processamento do faturamento diário: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno no processamento do pipeline diário: {str(e)}"
        )
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


@router.post(
    "/simulate-mock",
    summary="Executa a simulação oficial com o arquivo mock de faturamento diário",
    description="Executa o pipeline completo utilizando o arquivo mock com dados realistas da região de Crateús, "
                "pedidos balcão, cancelados, urgentes, peças de 6m e sobrecarga de viagens em múltiplos eixos."
)
def simulate_daily_mock(
    profile_name: str = "Equilibrado",
    time_limit_seconds: float = 20.0,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Executa a simulação completa com a base mock oficial."""
    mock_file = settings.DATA_RAW_DIR / "mock_faturamento_diario.csv"
    if not mock_file.exists():
        # Tenta caminhos alternativos
        candidates = [
            Path("/data/raw/mock_faturamento_diario.csv"),
            Path("./data/raw/mock_faturamento_diario.csv"),
            settings.BASE_DIR.parent / "data" / "raw" / "mock_faturamento_diario.csv",
        ]
        for c in candidates:
            if c.exists():
                mock_file = c
                break

    if not mock_file.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arquivo mock oficial não encontrado em: {mock_file}"
        )

    pipeline = DailyDispatchPipeline(db=db)
    result = pipeline.process_daily_billing(
        csv_file_path_or_df=mock_file,
        profile_name=profile_name,
        time_limit_seconds=time_limit_seconds
    )
    return result


@router.post(
    "/trips/loading-sheet/pdf",
    summary="Emite PDF do Mapa de Carregamento de Doca para uma viagem do pipeline"
)
def generate_trip_loading_sheet_pdf(trip_data: Dict[str, Any]):
    """Recebe os dados de uma viagem gerada no pipeline e retorna o PDF de carregamento (LIFO)."""
    try:
        pdf_bytes = ReportService.generate_loading_sheet_pdf(trip_data)
        trip_id = trip_data.get("trip_id", "viagem")
        filename = f"carregamento_doca_{trip_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Erro ao emitir PDF de carregamento da viagem: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na geração do PDF de carregamento: {str(e)}"
        )


@router.post(
    "/trips/delivery-route/pdf",
    summary="Emite PDF do Roteiro de Entregas TSP para uma viagem do pipeline"
)
def generate_trip_delivery_route_pdf(trip_data: Dict[str, Any]):
    """Recebe os dados de uma viagem gerada no pipeline e retorna o PDF do roteiro de entregas TSP."""
    try:
        pdf_bytes = ReportService.generate_delivery_route_pdf(trip_data)
        trip_id = trip_data.get("trip_id", "viagem")
        filename = f"roteiro_entregas_tsp_{trip_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Erro ao emitir PDF de roteiro TSP da viagem: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro na geração do PDF do roteiro TSP: {str(e)}"
        )

