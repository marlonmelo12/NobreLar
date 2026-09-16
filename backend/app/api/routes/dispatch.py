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
    DecoupledDispatchResponse,
    AllOrdersResponse,
    UnifiedOrderItem
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


SAMPLE_API_ORDERS: List[Dict[str, Any]] = [
    {
        "id": "L1260901",
        "data": "16/09/2026",
        "vendedor": "Vendedor Loja CD",
        "cliente": "Construtora Vale do Poty",
        "cidade": "CRATEUS",
        "endereco": "Rua Dom Pedro II, 450, Centro, Crateús - CE",
        "valor": 4850.00,
        "urgente": True,
        "situacao": "URGENTE",
        "pagamento_entrega": "QUITADO",
        "itens": [
            {
                "codigo": "01042",
                "descricao": "Piso Cerâmico Esmaltado 60x60 Bold",
                "quantidade": 40.0,
                "unidade": "CX",
                "preco_unitario": 52.50
            },
            {
                "codigo": "00318",
                "descricao": "Argamassa AC-III Cinza 20kg",
                "quantidade": 25.0,
                "unidade": "SC",
                "preco_unitario": 34.00
            },
            {
                "codigo": "00105",
                "descricao": "Cimento CP II-E-32 50kg",
                "quantidade": 30.0,
                "unidade": "SC",
                "preco_unitario": 38.00
            }
        ]
    },
    {
        "id": "L1260902",
        "data": "16/09/2026",
        "vendedor": "Balcão Crateús",
        "cliente": "Marcenaria e Reforma Silva",
        "cidade": "CRATEUS",
        "endereco": "Av. Sargento Hermínio, 1200, São Vicente, Crateús - CE",
        "valor": 2150.00,
        "urgente": False,
        "situacao": "NORMAL",
        "pagamento_entrega": "A RECEBER",
        "itens": [
            {
                "codigo": "01045",
                "descricao": "Porcelanato Polido 84x84 Retificado",
                "quantidade": 20.0,
                "unidade": "CX",
                "preco_unitario": 78.90
            },
            {
                "codigo": "00412",
                "descricao": "Rejunte Porcelanato Resinado Branco 1kg",
                "quantidade": 10.0,
                "unidade": "UN",
                "preco_unitario": 18.50
            },
            {
                "codigo": "00890",
                "descricao": "Tinta Acrílica Fosca Standard 18L",
                "quantidade": 2.0,
                "unidade": "UN",
                "preco_unitario": 198.00
            }
        ]
    },
    {
        "id": "L1260903",
        "data": "16/09/2026",
        "vendedor": "Equipe Regional Sertão",
        "cliente": "Comercial e Construção Tamboril",
        "cidade": "TAMBORIL",
        "endereco": "Rua Coronel Oliveira, 230, Centro, Tamboril - CE",
        "valor": 5400.00,
        "urgente": False,
        "situacao": "NORMAL",
        "pagamento_entrega": "QUITADO",
        "itens": [
            {
                "codigo": "00105",
                "descricao": "Cimento CP II-E-32 50kg",
                "quantidade": 50.0,
                "unidade": "SC",
                "preco_unitario": 38.00
            },
            {
                "codigo": "01042",
                "descricao": "Piso Cerâmico 60x60",
                "quantidade": 35.0,
                "unidade": "CX",
                "preco_unitario": 48.00
            }
        ]
    },
    {
        "id": "L1260904",
        "data": "16/09/2026",
        "vendedor": "Balcão Rápido",
        "cliente": "Cliente Retirada Loja",
        "cidade": "CRATEUS",
        "endereco": "Retirada no Balcão CD Crateús",
        "valor": 350.00,
        "urgente": False,
        "situacao": "RETIRADA",
        "pagamento_entrega": "QUITADO",
        "itens": [
            {
                "codigo": "00912",
                "descricao": "Torneira Monocomando Gourmet",
                "quantidade": 1.0,
                "unidade": "UN",
                "preco_unitario": 350.00
            }
        ]
    },
    {
        "id": "L1260905",
        "data": "16/09/2026",
        "vendedor": "Televendas",
        "cliente": "Cliente Cancelamento",
        "cidade": "INDEPENDENCIA",
        "endereco": "Rua Principal, 50",
        "valor": 1200.00,
        "urgente": False,
        "situacao": "CANCELADO",
        "pagamento_entrega": "QUITADO",
        "itens": [
            {
                "codigo": "01042",
                "descricao": "Piso Cerâmico 60x60",
                "quantidade": 20.0,
                "unidade": "CX",
                "preco_unitario": 60.00
            }
        ]
    }
]


class DispatchStateStore:
    """Armazenamento em memória do processamento de despacho logístico."""
    def __init__(self):
        self.last_result: Optional[Dict[str, Any]] = None
        self.last_trips: Optional[List[Dict[str, Any]]] = None
        self.staged_orders: Optional[List[Dict[str, Any]]] = None
        self.staged_params: Dict[str, Any] = {"profile_name": "Equilibrado", "time_limit": 20.0}

    def set_result(self, result: Dict[str, Any], trips: List[Dict[str, Any]]):
        self.last_result = result
        self.last_trips = trips
        self.staged_orders = None

    def set_staged(
        self,
        orders_raw: List[Dict[str, Any]],
        staged_result: Dict[str, Any],
        profile_name: str = "Equilibrado",
        time_limit: float = 20.0
    ):
        self.staged_orders = orders_raw
        self.staged_params = {"profile_name": profile_name, "time_limit": time_limit}
        self.last_result = staged_result
        self.last_trips = []

    def clear(self):
        self.last_result = None
        self.last_trips = None
        self.staged_orders = None
        self.staged_params = {"profile_name": "Equilibrado", "time_limit": 20.0}

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


def _build_staged_orders_response(pipeline: DailyDispatchPipeline, orders_raw: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Cria resposta intermediária onde pedidos válidos ficam como 'não alocados' aguardando execução dos limites."""
    valid_orders = []
    discarded_logs = []

    for row_dict in orders_raw:
        is_valid, order_data, discard_log = pipeline._normalize_single_order(row_dict)
        if not is_valid:
            if discard_log:
                discarded_logs.append(discard_log)
        else:
            order_data["motivo_nao_alocacao"] = "Aguardando execução do controle de limites e roteirização"
            valid_orders.append(order_data)

    unallocated_formatted = pipeline.format_unallocated_orders_response(valid_orders)
    total_val = sum(o["total_value"] for o in valid_orders)

    return {
        "status": "SUCESSO",
        "resumo": {
            "total_records_read": len(orders_raw),
            "total_discarded_cleaning": len(discarded_logs),
            "total_valid_deliveries": len(valid_orders),
            "total_allocated_orders": 0,
            "total_unallocated_orders": len(valid_orders),
            "total_trips_generated": 0,
            "total_invoiced_value": round(total_val, 2),
            "total_allocated_weight_kg": 0.0,
            "total_allocated_volume_m3": 0.0,
        },
        "cargas_caminhao": [],
        "roteiros_entrega": [],
        "descartes_limpeza": discarded_logs,
        "pedidos_nao_alocados": unallocated_formatted
    }


@router.post(
    "/stage",
    summary="Carrega e armazena os pedidos desalocados para exibição no dashboard antes da execução",
    response_model=DecoupledDispatchResponse
)
def stage_orders_post(
    payload: Union[DecoupledBatchRequest, DecoupledOrderInput, List[DecoupledOrderInput], Dict[str, Any], List[Dict[str, Any]]],
    db: Session = Depends(get_db)
):
    """Armazena os pedidos enviados via JSON em estado desalocado para pré-visualização no Dashboard."""
    orders_raw, profile_name, time_limit = _extract_batch_orders_and_params(payload)
    if not orders_raw:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nenhum pedido fornecido no lote.")

    pipeline = DailyDispatchPipeline(db=db)
    staged_res = _build_staged_orders_response(pipeline, orders_raw)
    dispatch_state.set_staged(orders_raw, staged_res, profile_name, time_limit)
    return staged_res


@router.post(
    "/simulate",
    summary="Simula a carga de pedidos da API (inicialmente desalocados)",
    response_model=DecoupledDispatchResponse
)
def simulate_api_load(
    payload: Optional[Union[DecoupledBatchRequest, DecoupledOrderInput, List[DecoupledOrderInput], Dict[str, Any], List[Dict[str, Any]]]] = None,
    db: Session = Depends(get_db)
):
    """Simula uma carga de pedidos faturados vindos da API, deixando-os inicialmente desalocados no Dashboard."""
    orders_raw = None
    profile_name = "Equilibrado"
    time_limit = 20.0

    if payload:
        orders_raw, profile_name, time_limit = _extract_batch_orders_and_params(payload)

    if not orders_raw:
        orders_raw = SAMPLE_API_ORDERS

    pipeline = DailyDispatchPipeline(db=db)
    staged_res = _build_staged_orders_response(pipeline, orders_raw)
    dispatch_state.set_staged(orders_raw, staged_res, profile_name, time_limit)
    return staged_res


@router.post(
    "/execute-limits",
    summary="Executa o controle dos limites e roteirização sobre os pedidos desalocados",
    response_model=DecoupledDispatchResponse
)
def execute_limits_and_route(
    payload: Optional[Union[DecoupledBatchRequest, DecoupledOrderInput, List[DecoupledOrderInput], Dict[str, Any], List[Dict[str, Any]]]] = None,
    db: Session = Depends(get_db)
):
    """Dispara a alocação de cargas e roteirização com pontos a partir dos pedidos carregados/desalocados."""
    orders_raw = None
    profile_name = dispatch_state.staged_params.get("profile_name", "Equilibrado")
    time_limit = dispatch_state.staged_params.get("time_limit", 20.0)

    if payload:
        extracted, p_name, t_limit = _extract_batch_orders_and_params(payload)
        if extracted:
            orders_raw = extracted
            profile_name = p_name
            time_limit = t_limit

    if not orders_raw:
        orders_raw = dispatch_state.staged_orders

    if not orders_raw:
        # Se nenhum pedido foi carregado, usa os pedidos de simulação padrão
        orders_raw = SAMPLE_API_ORDERS

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
        "descartes_limpeza": [],
        "pedidos_nao_alocados": []
    }


@router.get(
    "/orders",
    summary="Lista todos os pedidos (alocados, não alocados e descartados) com detalhes e status",
    response_model=AllOrdersResponse
)
def get_all_orders_summary():
    """Retorna a listagem unificada de todos os pedidos processados no lote atual:
    - Pedidos Alocados (em quais viagens, veículos e paradas foram alocados)
    - Pedidos Não Alocados (motivo da não alocação, volume, peso, valor)
    - Pedidos Descartados na Higienização (regras de expurgo como balcão ou cancelamento)
    """
    res = dispatch_state.last_result
    if not res:
        return {
            "status": "SUCESSO",
            "total": 0,
            "total_alocados": 0,
            "total_nao_alocados": 0,
            "total_descartados": 0,
            "pedidos": []
        }

    unified_orders: List[Dict[str, Any]] = []

    # 1. Pedidos Alocados (a partir de cargas_caminhao)
    cargas = res.get("cargas_caminhao", [])
    for trip in cargas:
        v_info = trip.get("veiculo", {})
        for ord_item in trip.get("pedidos_carroceria", []):
            unified_orders.append({
                "id": str(ord_item.get("pedido")),
                "external_id": str(ord_item.get("external_id", ord_item.get("pedido"))),
                "cliente": ord_item.get("cliente"),
                "cidade": ord_item.get("cidade"),
                "endereco": ord_item.get("endereco"),
                "situacao": ord_item.get("situacao", "NORMAL"),
                "peso_kg": round(float(ord_item.get("peso_total_kg", 0.0)), 2),
                "volume_m3": round(float(ord_item.get("volume_total_m3", 0.0)), 4),
                "valor": round(float(ord_item.get("valor_total", 0.0)), 2),
                "status": "ALOCADO",
                "status_label": "Alocado",
                "viagem_id": trip.get("viagem_id"),
                "viagem_titulo": trip.get("titulo"),
                "veiculo_nome": v_info.get("nome"),
                "veiculo_placa": v_info.get("placa"),
                "eixo_nome": trip.get("eixo_nome"),
                "ordem_carregamento": ord_item.get("ordem_carregamento"),
                "ordem_entrega": ord_item.get("ordem_entrega_prevista"),
                "motivo": None,
                "itens": ord_item.get("itens", [])
            })

    # 2. Pedidos Não Alocados
    nao_alocados = res.get("pedidos_nao_alocados", [])
    for ord_item in nao_alocados:
        unified_orders.append({
            "id": str(ord_item.get("pedido")),
            "external_id": str(ord_item.get("external_id", ord_item.get("pedido"))),
            "cliente": ord_item.get("cliente"),
            "cidade": ord_item.get("cidade"),
            "endereco": ord_item.get("endereco"),
            "situacao": ord_item.get("situacao", "NORMAL"),
            "peso_kg": round(float(ord_item.get("peso_total_kg", 0.0)), 2),
            "volume_m3": round(float(ord_item.get("volume_total_m3", 0.0)), 4),
            "valor": round(float(ord_item.get("valor_total", 0.0)), 2),
            "status": "NAO_ALOCADO",
            "status_label": "Não Alocado",
            "viagem_id": None,
            "viagem_titulo": None,
            "veiculo_nome": None,
            "veiculo_placa": None,
            "eixo_nome": ord_item.get("eixo_id"),
            "ordem_carregamento": None,
            "ordem_entrega": None,
            "motivo": ord_item.get("motivo", "Capacidade ou disponibilidade de frota excedida"),
            "itens": ord_item.get("itens", [])
        })

    # 3. Pedidos Descartados na Higienização
    descartes = res.get("descartes_limpeza", [])
    for disc in descartes:
        unified_orders.append({
            "id": str(disc.get("pedido")),
            "external_id": str(disc.get("pedido")),
            "cliente": None,
            "cidade": None,
            "endereco": None,
            "situacao": disc.get("regra", "DESCARTE"),
            "peso_kg": 0.0,
            "volume_m3": 0.0,
            "valor": 0.0,
            "status": "DESCARTADO",
            "status_label": "Descartado",
            "viagem_id": None,
            "viagem_titulo": None,
            "veiculo_nome": None,
            "veiculo_placa": None,
            "eixo_nome": None,
            "ordem_carregamento": None,
            "ordem_entrega": None,
            "motivo": disc.get("motivo"),
            "itens": []
        })

    total_alocados = len([o for o in unified_orders if o["status"] == "ALOCADO"])
    total_nao_alocados = len([o for o in unified_orders if o["status"] == "NAO_ALOCADO"])
    total_descartados = len([o for o in unified_orders if o["status"] == "DESCARTADO"])

    return {
        "status": "SUCESSO",
        "total": len(unified_orders),
        "total_alocados": total_alocados,
        "total_nao_alocados": total_nao_alocados,
        "total_descartados": total_descartados,
        "pedidos": unified_orders
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


