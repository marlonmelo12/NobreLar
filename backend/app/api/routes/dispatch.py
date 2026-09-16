import json
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Any, Optional, List, Union, Tuple
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Response
from sqlalchemy.orm import Session
import structlog

from app.core.config import settings
from app.infrastructure.database.session import get_db
from app.services.dispatch_pipeline import DailyDispatchPipeline
from app.services.report_service import ReportService
from app.domain.schemas.decoupled_schema import (
    DecoupledBatchRequest,
    DecoupledOrderInput,
    TruckLoadResponse,
    DeliveryRouteResponse,
    DecoupledDispatchResponse
)

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


# ===========================================================================
# ENDPOINTS DESACOPLADOS: JSON INGESTION & DRILL-DOWN PARA O FRONTEND
# ===========================================================================

@router.get(
    "/mock-orders",
    summary="Retorna a lista de pedidos mock estruturados baseados no pedido oficial da Nobre Lar",
    response_model=List[Dict[str, Any]]
)
def get_mock_orders_json():
    """Retorna a coleção mock JSON estruturada baseada no espelho do pedido L12608361 da Nobre Lar."""
    mock_candidates = [
        settings.DATA_RAW_DIR / "mock_pedidos_estrutura.json",
        Path("/data/raw/mock_pedidos_estrutura.json"),
        Path("./data/raw/mock_pedidos_estrutura.json"),
        settings.BASE_DIR.parent / "data" / "raw" / "mock_pedidos_estrutura.json",
    ]
    for p in mock_candidates:
        if p.exists():
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except Exception as e:
                logger.error(f"Erro ao ler mock de pedidos: {e}")

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Arquivo mock_pedidos_estrutura.json não encontrado."
    )


def _extract_batch_orders_and_params(
    payload: Union[DecoupledBatchRequest, List[DecoupledOrderInput], List[Dict[str, Any]], Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], str, float]:
    """Extrai a lista de pedidos brutos e parâmetros a partir de múltiplos formatos JSON suportados."""
    profile_name = "Equilibrado"
    time_limit = 20.0

    if isinstance(payload, DecoupledBatchRequest):
        orders_raw = [o.model_dump(by_alias=True) for o in payload.pedidos]
        profile_name = payload.perfil_otimizacao or profile_name
        time_limit = payload.tempo_limite_segundos or time_limit
    elif isinstance(payload, dict):
        p_list = payload.get("pedidos") or payload.get("orders") or []
        orders_raw = []
        for o in p_list:
            if hasattr(o, "model_dump"):
                orders_raw.append(o.model_dump(by_alias=True))
            elif isinstance(o, dict):
                orders_raw.append(o)
        profile_name = payload.get("perfil_otimizacao", profile_name)
        time_limit = float(payload.get("tempo_limite_segundos", time_limit))
    elif isinstance(payload, list):
        orders_raw = []
        for o in payload:
            if hasattr(o, "model_dump"):
                orders_raw.append(o.model_dump(by_alias=True))
            elif isinstance(o, dict):
                orders_raw.append(o)
    else:
        orders_raw = []

    return orders_raw, profile_name, time_limit


@router.post(
    "/process-orders",
    summary="Processamento desacoplado completo via JSON (retorna ambas as visões com drill-down)",
    response_model=DecoupledDispatchResponse
)
def process_orders_decoupled(
    payload: Union[DecoupledBatchRequest, List[DecoupledOrderInput]],
    db: Session = Depends(get_db)
):
    """Processa o lote de pedidos JSON em memória e retorna tanto a visão de Cargas na Carroceria quanto o Roteiro TSP."""
    orders_raw, profile_name, time_limit = _extract_batch_orders_and_params(payload)
    if not orders_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum pedido fornecido no lote.")

    pipeline = DailyDispatchPipeline(db=db)
    result = pipeline.process_orders_json(
        orders=orders_raw,
        profile_name=profile_name,
        time_limit_seconds=time_limit
    )
    return result


@router.post(
    "/process-orders/truck-load",
    summary="Retorna os pedidos organizados para Carga no Caminhão (Carroceria Aberta) com drill-down de itens",
    response_model=TruckLoadResponse
)
def process_orders_truck_load(
    payload: Union[DecoupledBatchRequest, List[DecoupledOrderInput]],
    db: Session = Depends(get_db)
):
    """Retorna especificamente a visão de montagem de carga na carroceria aberta para o Frontend da expedição."""
    orders_raw, profile_name, time_limit = _extract_batch_orders_and_params(payload)
    if not orders_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum pedido fornecido no lote.")

    pipeline = DailyDispatchPipeline(db=db)
    raw_res = pipeline.process_orders_collection(
        raw_orders=orders_raw,
        profile_name=profile_name,
        time_limit_seconds=time_limit
    )
    trips_formatted = pipeline.format_truck_load_response(raw_res["trips"])
    return {
        "status": "SUCESSO",
        "total_viagens": len(trips_formatted),
        "viagens": trips_formatted
    }


@router.post(
    "/process-orders/delivery-route",
    summary="Retorna a Ordem de Entrega (Roteiro TSP) com endereços, recebíveis e drill-down de itens",
    response_model=DeliveryRouteResponse
)
def process_orders_delivery_route(
    payload: Union[DecoupledBatchRequest, List[DecoupledOrderInput]],
    db: Session = Depends(get_db)
):
    """Retorna especificamente a visão cronológica de entregas TSP com dados do cliente e produtos por parada."""
    orders_raw, profile_name, time_limit = _extract_batch_orders_and_params(payload)
    if not orders_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum pedido fornecido no lote.")

    pipeline = DailyDispatchPipeline(db=db)
    raw_res = pipeline.process_orders_collection(
        raw_orders=orders_raw,
        profile_name=profile_name,
        time_limit_seconds=time_limit
    )
    trips_formatted = pipeline.format_delivery_route_response(raw_res["trips"])
    return {
        "status": "SUCESSO",
        "total_viagens": len(trips_formatted),
        "viagens": trips_formatted
    }


