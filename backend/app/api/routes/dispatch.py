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


class DispatchStateStore:
    """Armazenamento em memória do último processamento de despacho logístico."""
    def __init__(self):
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_trips: Optional[List[Dict[str, Any]]] = None

    def set_result(self, result: Dict[str, Any], trips: List[Dict[str, Any]]):
        self.last_result = result
        self.last_trips = trips

    def clear(self):
        self.last_result = None
        self.last_trips = None

    def get_trips(
        self,
        pipeline: DailyDispatchPipeline,
        profile_name: str = "Equilibrado",
        time_limit: float = 20.0
    ) -> List[Dict[str, Any]]:
        if self.last_trips is not None:
            return self.last_trips
        return []


dispatch_state = DispatchStateStore()


@router.get(
    "/trips/{trip_id}/pdf/loading-sheet",
    summary="Emite PDF do Mapa de Carregamento da Carroceria Aberta via GET"
)
def get_trip_loading_sheet_pdf(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Gera e retorna diretamente o PDF do mapa de carregamento (LIFO) para visualização ou download no navegador."""
    pipeline = DailyDispatchPipeline(db=db)
    trips = dispatch_state.get_trips(pipeline)
    if not trips:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum lote de viagens disponível.")

    matched_trip = next((t for t in trips if t["trip_id"] == trip_id), None)
    if not matched_trip:
        if trip_id in ("default", "current", "1", "viagem-1") and trips:
            matched_trip = trips[0]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Viagem '{trip_id}' não encontrada.")

    try:
        pdf_bytes = ReportService.generate_loading_sheet_pdf(matched_trip)
        filename = f"mapa_carregamento_{trip_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Erro ao gerar PDF de carregamento via GET: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get(
    "/trips/{trip_id}/pdf/delivery-route",
    summary="Emite PDF do Roteiro de Entregas TSP via GET"
)
def get_trip_delivery_route_pdf(
    trip_id: str,
    db: Session = Depends(get_db)
):
    """Gera e retorna diretamente o PDF do roteiro de entregas TSP com cobrança para visualização ou download no navegador."""
    pipeline = DailyDispatchPipeline(db=db)
    trips = dispatch_state.get_trips(pipeline)
    if not trips:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nenhum lote de viagens disponível.")

    matched_trip = next((t for t in trips if t["trip_id"] == trip_id), None)
    if not matched_trip:
        if trip_id in ("default", "current", "1", "viagem-1") and trips:
            matched_trip = trips[0]
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Viagem '{trip_id}' não encontrada.")

    try:
        pdf_bytes = ReportService.generate_delivery_route_pdf(matched_trip)
        filename = f"roteiro_entregas_{trip_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"inline; filename={filename}"}
        )
    except Exception as e:
        logger.error(f"Erro ao gerar PDF de roteiro TSP via GET: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))



def _extract_batch_orders_and_params(
    payload: Union[DecoupledBatchRequest, DecoupledOrderInput, List[DecoupledOrderInput], List[Dict[str, Any]], Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], str, float]:
    """Extrai a lista de pedidos brutos e parâmetros a partir de múltiplos formatos JSON suportados (lote ou pedido único)."""
    profile_name = "Equilibrado"
    time_limit = 20.0

    if isinstance(payload, DecoupledBatchRequest):
        orders_raw = [o.model_dump(by_alias=True) for o in payload.pedidos]
        profile_name = payload.perfil_otimizacao or profile_name
        time_limit = payload.tempo_limite_segundos or time_limit
    elif isinstance(payload, DecoupledOrderInput):
        orders_raw = [payload.model_dump(by_alias=True)]
    elif isinstance(payload, dict):
        p_list = payload.get("pedidos") or payload.get("orders")
        if p_list is None and ("id" in payload or "itens" in payload or "items" in payload or "cidade" in payload or "pedido" in payload):
            orders_raw = [payload]
        else:
            p_list = p_list or []
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


# ===========================================================================
# 1. ENDPOINT ÚNICO DE POST: RECEBE O JSON COM OS PEDIDOS PARA PROCESSAMENTO
# ===========================================================================
@router.post(
    "/orders",
    summary="Recebe o JSON com os pedidos faturados para processar cargas e rotas (Endpoint Único POST)",
    response_model=DecoupledDispatchResponse
)
@router.post(
    "/process-orders",
    summary="Processamento desacoplado de pedidos via JSON (Endpoint Único POST)",
    response_model=DecoupledDispatchResponse
)
def submit_and_process_orders_post(
    payload: Union[DecoupledBatchRequest, DecoupledOrderInput, List[DecoupledOrderInput], Dict[str, Any], List[Dict[str, Any]]],
    db: Session = Depends(get_db)
):
    """Recebe o JSON estruturado com os pedidos faturados do Frontend/ERP.
    
    Executa a higienização, cubagem técnica, divisão de eixos, otimização multi-viagens (CP-SAT)
    e roteirização (TSP). O resultado fica armazenado para consulta imediata via GET.
    """
    orders_raw, profile_name, time_limit = _extract_batch_orders_and_params(payload)
    if not orders_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum pedido fornecido no lote.")

    pipeline = DailyDispatchPipeline(db=db)
    raw_res = pipeline.process_orders_collection(
        raw_orders=orders_raw,
        profile_name=profile_name,
        time_limit_seconds=time_limit
    )
    result = pipeline.process_orders_json(
        orders=orders_raw,
        profile_name=profile_name,
        time_limit_seconds=time_limit
    )
    dispatch_state.set_result(result, raw_res.get("trips", []))
    return result


# ===========================================================================
# 2. ENDPOINTS EXCLUSIVAMENTE GET: RETORNAM OS DADOS DE CARGA E ROTA
# ===========================================================================
@router.get(
    "/truck-load",
    summary="Retorna exclusivamente via GET os dados de Carga no Caminhão (Carroceria Aberta)",
    response_model=TruckLoadResponse
)
@router.get(
    "/process-orders/truck-load",
    summary="Retorna exclusivamente via GET os dados de Carga no Caminhão (Alias)",
    response_model=TruckLoadResponse
)
def get_truck_load(
    perfil_otimizacao: str = "Equilibrado",
    tempo_limite_segundos: float = 20.0,
    db: Session = Depends(get_db)
):
    """Retorna via GET as cargas alocadas em cada caminhão de carroceria aberta com drill-down de itens."""
    pipeline = DailyDispatchPipeline(db=db)
    trips = dispatch_state.get_trips(pipeline, perfil_otimizacao, tempo_limite_segundos)
    if not trips:
        return {
            "status": "SUCESSO",
            "total_viagens": 0,
            "viagens": []
        }

    trips_formatted = pipeline.format_truck_load_response(trips)
    return {
        "status": "SUCESSO",
        "total_viagens": len(trips_formatted),
        "viagens": trips_formatted
    }


@router.get(
    "/delivery-route",
    summary="Retorna exclusivamente via GET os dados de Rota de Entrega (Roteiro TSP)",
    response_model=DeliveryRouteResponse
)
@router.get(
    "/process-orders/delivery-route",
    summary="Retorna exclusivamente via GET os dados de Rota de Entrega (Alias)",
    response_model=DeliveryRouteResponse
)
def get_delivery_route(
    perfil_otimizacao: str = "Equilibrado",
    tempo_limite_segundos: float = 20.0,
    db: Session = Depends(get_db)
):
    """Retorna via GET a ordem cronológica de entregas TSP com dados do cliente, paradas e drill-down."""
    pipeline = DailyDispatchPipeline(db=db)
    trips = dispatch_state.get_trips(pipeline, perfil_otimizacao, tempo_limite_segundos)
    if not trips:
        return {
            "status": "SUCESSO",
            "total_viagens": 0,
            "viagens": []
        }

    trips_formatted = pipeline.format_delivery_route_response(trips)
    return {
        "status": "SUCESSO",
        "total_viagens": len(trips_formatted),
        "viagens": trips_formatted
    }


@router.get(
    "/process-orders",
    summary="Consulta consolidada completa via GET (usando pedidos em memória)",
    response_model=DecoupledDispatchResponse
)
def get_orders_decoupled_summary(
    perfil_otimizacao: str = "Equilibrado",
    tempo_limite_segundos: float = 20.0,
    db: Session = Depends(get_db)
):
    """Retorna a visão consolidada completa (Cargas + Rotas + Descartes) diretamente via GET."""
    if dispatch_state.last_result:
        return dispatch_state.last_result

    return {
        "status": "SUCESSO",
        "resumo": {
            "total_records_read": 0,
            "total_discarded_cleaning": 0,
            "total_valid_deliveries": 0,
            "total_allocated_orders": 0,
            "total_unallocated_orders": 0,
            "total_trips_generated": 0,
            "total_invoiced_value": 0.0,
            "total_allocated_weight_kg": 0.0,
            "total_allocated_volume_m3": 0.0,
        },
        "cargas_caminhao": [],
        "roteiros_entrega": [],
        "descartes_limpeza": []
    }


@router.post(
    "/clear",
    summary="Limpa todos os dados de despacho e rotas em memória",
    response_model=Dict[str, Any]
)
def clear_dispatch_state():
    """Reseta e zera os planos de despacho e roteiros em memória."""
    dispatch_state.clear()
    return {"status": "SUCESSO", "mensagem": "Estado de despacho limpo com sucesso."}


