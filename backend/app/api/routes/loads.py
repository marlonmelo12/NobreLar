"""Rotas de otimização de carga, edição manual auditada, aprovação e romaneio.

Implementa o fluxo principal de montagem de carga:
- Otimização combinatória com OR-Tools CP-SAT
- Pré-processamento com fatiamento de carga (Order Splitting)
- Validação independente e inviolabilidade física e territorial
- Roteirização ótima de paradas com sequenciamento LIFO (Doca)
- Edição manual com verificação de capacidade e rejeição 409 Conflict
- Emissão do Romaneio de Carga em PDF e HTML
"""

import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session
import structlog

from app.api.dependencies import get_db, get_current_user
from app.domain.models import (
    LoadPlan, LoadPlanItem, LoadPlanDecision, LoadPlanAudit,
    Order, Vehicle, Axis, OptimizationProfile, User, City
)
from app.domain.schemas.load_plan_schema import (
    OptimizeRequest, LoadPlanResponse, LoadPlanDecisionResponse,
    LoadPlanAuditResponse, ToggleItemRequest, ApprovePlanRequest
)
from app.core.geo_constants import DEPOT_COORDINATES
from app.core.constants import CITY_TO_AXIS_MAP
from app.services.pre_processor import split_overweight_orders, validate_vehicle_territorial_compatibility
from app.services.optimizer_cpsat import solve_load_allocation
from app.services.fallback import solve_greedy_fallback
from app.services.validation import IndependentValidator
from app.services.tsp_solver import solve_tsp
from app.services.report_service import ReportService

logger = structlog.get_logger()
router = APIRouter(prefix="/load-plans", tags=["Planos de Carga"])


@router.post("/optimize", response_model=LoadPlanResponse, summary="Otimizar e gerar plano de carga por eixo")
def optimize_load_plan(
    req: OptimizeRequest,
    db: Session = Depends(get_db)
):
    """Executa a otimização de carga para determinado eixo rodoviário e veículo."""
    # 1. Validação de entidades
    axis = db.query(Axis).filter(Axis.id == req.axis_id).first()
    if not axis:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Eixo rodoviário não encontrado.")

    vehicle = db.query(Vehicle).filter(Vehicle.id == req.vehicle_id).first()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Veículo não encontrado.")

    # Validação de restrição territorial: se o veículo for restrito a Crateús/distritos
    if vehicle.restricted_to_crateus and req.axis_id != "eixo-0-crateus-urbano":
        # Verifica se o eixo contém cidades externas
        cities_in_axis = db.query(City).filter(City.axis_id == req.axis_id, City.is_external == True).all()
        if cities_in_axis:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    f"Incompatibilidade operacional: o veículo '{vehicle.name}' é restrito ao município de Crateús "
                    f"e seus distritos. Para o eixo intermunicipal '{axis.name}', selecione o caminhão maior (Accelo 815)."
                )
            )

    # 2. Resolução do perfil de otimização
    if req.profile_id:
        profile = db.query(OptimizationProfile).filter(OptimizationProfile.id == req.profile_id).first()
    else:
        profile = db.query(OptimizationProfile).filter(OptimizationProfile.is_default == True).first()

    if not profile:
        profile = db.query(OptimizationProfile).first()

    profile_snapshot = {
        "w_peso": profile.w_peso,
        "w_volume": profile.w_volume,
        "w_valor": profile.w_valor,
        "w_quantidade": profile.w_quantidade,
        "objective_mode": profile.objective_mode,
        "profile_name": profile.name,
    }

    # 3. Busca dos pedidos pendentes faturados do eixo
    raw_orders = db.query(Order).filter(
        Order.axis_id == req.axis_id,
        Order.status == "Faturado"
    ).all()

    orders_dict_list = []
    for o in raw_orders:
        orders_dict_list.append({
            "id": o.id,
            "axis_id": o.axis_id,
            "city_name": o.city_name,
            "address_line": o.address_line,
            "latitude": o.latitude,
            "longitude": o.longitude,
            "total_weight_kg": o.total_weight_kg,
            "total_volume_m3": o.total_volume_m3,
            "total_value": o.value,
            "sale_frequency": o.sale_frequency,
            "has_long_items": o.has_long_items,
            "payment_on_delivery": o.payment_on_delivery,
            "is_mandatory": o.is_mandatory or (req.mandatory_order_ids and o.id in req.mandatory_order_ids),
        })

    # 4. Fatiamento pré-solver (Order Splitting) para cargas que excedem a capacidade útil
    processed_orders = split_overweight_orders(orders_dict_list, max_capacity_kg=vehicle.capacity_kg)

    # 5. Execução do Solver CP-SAT
    solver_result = solve_load_allocation(
        orders=processed_orders,
        capacity_kg=vehicle.capacity_kg,
        capacity_m3=vehicle.useful_volume_m3,
        allows_long_items=vehicle.allows_long_items,
        restricted_to_crateus=vehicle.restricted_to_crateus,
        w_weight=profile.w_peso,
        w_volume=profile.w_volume,
        w_value=profile.w_valor,
        w_freq=profile.w_quantidade,
        objective_mode=profile.objective_mode,
        time_limit_sec=req.time_limit_seconds,
        mandatory_order_ids=req.mandatory_order_ids
    )

    # Fallback heurístico em caso de timeout sem solução incumbente
    if solver_result["status"] in ("UNKNOWN", "TIMEOUT_SEM_SOLUCAO"):
        solver_result = solve_greedy_fallback(
            orders=processed_orders,
            capacity_kg=vehicle.capacity_kg,
            capacity_m3=vehicle.useful_volume_m3,
            allows_long_items=vehicle.allows_long_items,
            restricted_to_crateus=vehicle.restricted_to_crateus,
            w_weight=profile.w_peso,
            w_volume=profile.w_volume,
            w_value=profile.w_valor,
            w_freq=profile.w_quantidade
        )

    # 6. Validação Independente dos Invariantes Físicos
    selected_set = set(solver_result["selected_order_ids"])
    selected_orders = [o for o in processed_orders if o["id"] in selected_set]

    is_valid, validation_errors = IndependentValidator.validate_plan(
        selected_orders=selected_orders,
        capacity_kg=vehicle.capacity_kg,
        capacity_m3=vehicle.useful_volume_m3,
        target_axis_id=req.axis_id,
        allows_long_items=vehicle.allows_long_items,
        restricted_to_crateus=vehicle.restricted_to_crateus
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha crítica: o solver gerou um plano fisicamente inválido: {validation_errors}"
        )

    # 7. Roteirização do Caixeiro Viajante (TSP) para definir ordem de descarga e LIFO de carregamento
    locations = [(DEPOT_COORDINATES["lat"], DEPOT_COORDINATES["lon"])]
    for o in selected_orders:
        lat = o.get("latitude") or DEPOT_COORDINATES["lat"]
        lon = o.get("longitude") or DEPOT_COORDINATES["lon"]
        locations.append((lat, lon))

    tsp_res = solve_tsp(locations, depot_index=0, roundtrip=True)
    delivery_stops = tsp_res["delivery_order"]

    # Atribui a ordem de entrega e doca (LIFO)
    order_id_to_delivery_seq = {}
    for seq_idx, node_idx in enumerate(delivery_stops, start=1):
        if 1 <= node_idx <= len(selected_orders):
            ord_id = selected_orders[node_idx - 1]["id"]
            order_id_to_delivery_seq[ord_id] = seq_idx

    total_selected = len(selected_orders)
    execution_id = f"EXEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"

    # 8. Persistência do Plano de Carga
    plan = LoadPlan(
        execution_id=execution_id,
        axis_id=req.axis_id,
        vehicle_id=req.vehicle_id,
        profile_id=profile.id,
        profile_snapshot=profile_snapshot,
        total_orders=total_selected,
        total_value=solver_result["total_value"],
        total_weight_kg=solver_result["total_weight_kg"],
        total_volume_m3=solver_result["total_volume_m3"],
        weight_occupancy=solver_result["weight_occupancy_pct"],
        volume_occupancy=solver_result["volume_occupancy_pct"],
        limiting_resource=solver_result["limiting_resource"],
        estimated_cubing_pct=0.0,  # Recalculado abaixo
        solver_status=solver_result["status"],
        optimality_gap=solver_result.get("optimality_gap"),
        solve_duration_ms=solver_result["solve_duration_ms"],
        algorithm_version=solver_result["algorithm_version"],
        is_manually_modified=False,
        valid=True,
        created_by="operador"
    )
    db.add(plan)
    db.flush()

    # Persiste os itens selecionados
    for o in selected_orders:
        deliv_seq = order_id_to_delivery_seq.get(o["id"], 1)
        loading_seq = total_selected - deliv_seq + 1  # LIFO: inverso da entrega

        item = LoadPlanItem(
            load_plan_id=plan.id,
            order_id=o["id"],
            delivery_order=deliv_seq,
            loading_order=loading_seq,
            score=o.get("score", 0.0),
            efficiency=o.get("efficiency", 0.0),
            weight_kg=o.get("total_weight_kg", 0.0),
            volume_m3=o.get("total_volume_m3", 0.0),
            value=o.get("total_value", 0.0),
            city_name=o.get("city_name", ""),
        )
        db.add(item)

    # Persiste as decisões explicáveis para cada pedido avaliado
    for d in solver_result["decisions"]:
        dec = LoadPlanDecision(
            load_plan_id=plan.id,
            order_id=d["order_id"],
            included=d["included"],
            score=d["score"],
            efficiency=d["efficiency"],
            peso_pct=d["peso_pct"],
            volume_pct=d["volume_pct"],
            exclusion_reason=d["exclusion_reason"]
        )
        db.add(dec)

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{plan_id}", response_model=LoadPlanResponse, summary="Obter detalhes do plano de carga")
def get_load_plan(plan_id: int, db: Session = Depends(get_db)):
    """Retorna o plano de carga com itens selecionados, ordem de descarga e decisões."""
    plan = db.query(LoadPlan).filter(LoadPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de carga não encontrado.")
    return plan


@router.get("/{plan_id}/decisions", response_model=List[LoadPlanDecisionResponse], summary="Relatório de decisão do solver")
def get_plan_decisions(plan_id: int, db: Session = Depends(get_db)):
    """Retorna os motivos de inclusão ou exclusão de cada pedido avaliado pelo solver."""
    return db.query(LoadPlanDecision).filter(LoadPlanDecision.load_plan_id == plan_id).all()


@router.post("/{plan_id}/items/{order_id}/toggle", response_model=LoadPlanResponse, summary="Edição manual auditada do plano")
def toggle_load_plan_item(
    plan_id: int,
    order_id: str,
    db: Session = Depends(get_db)
):
    """Permite ao aprovador incluir ou remover manualmente um pedido, com validação de capacidade rígida."""
    plan = db.query(LoadPlan).filter(LoadPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de carga não encontrado.")

    vehicle = plan.vehicle
    existing_item = db.query(LoadPlanItem).filter(
        LoadPlanItem.load_plan_id == plan_id,
        LoadPlanItem.order_id == order_id
    ).first()

    w_before = plan.total_weight_kg
    v_before = plan.total_volume_m3

    if existing_item:
        # Ação: REMOVER PEDIDO
        new_w = round(plan.total_weight_kg - existing_item.weight_kg, 2)
        new_v = round(plan.total_volume_m3 - existing_item.volume_m3, 4)
        new_val = round(plan.total_value - existing_item.value, 2)

        db.delete(existing_item)

        # Atualiza a decisão correspondente
        dec = db.query(LoadPlanDecision).filter(
            LoadPlanDecision.load_plan_id == plan_id,
            LoadPlanDecision.order_id == order_id
        ).first()
        if dec:
            dec.included = False
            dec.exclusion_reason = "REMOVIDO_MANUALMENTE"

        plan.total_orders -= 1
        plan.total_weight_kg = new_w
        plan.total_volume_m3 = new_v
        plan.total_value = new_val
        plan.weight_occupancy = round((new_w / vehicle.capacity_kg) * 100, 2)
        plan.volume_occupancy = round((new_v / vehicle.useful_volume_m3) * 100, 2)
        plan.is_manually_modified = True

        # Registra auditoria da remoção
        audit = LoadPlanAudit(
            load_plan_id=plan.id,
            user_id="aprovador",
            action="REMOVE_ORDER",
            order_id=order_id,
            accepted=True,
            weight_before=w_before,
            weight_after=new_w,
            volume_before=v_before,
            volume_after=new_v
        )
        db.add(audit)
        db.commit()
        db.refresh(plan)
        return plan

    else:
        # Ação: INCLUIR PEDIDO MANUALMENTE
        order_obj = db.query(Order).filter(Order.id == order_id).first()
        if not order_obj:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pedido não encontrado.")

        # 1. Validação Rígida de Eixo Rodoviário (Segregação Geográfica Canônica)
        if order_obj.axis_id != plan.axis_id:
            err_msg = (
                f"Inclusão rejeitada por incompatibilidade geográfica: o pedido '{order_id}' pertence ao "
                f"'{order_obj.axis_id}', não podendo ser misturado com a carga do '{plan.axis_id}'."
            )
            audit = LoadPlanAudit(
                load_plan_id=plan.id,
                user_id="aprovador",
                action="ADD_ORDER",
                order_id=order_id,
                accepted=False,
                rejection_reason=err_msg,
                weight_before=w_before,
                weight_after=w_before,
                volume_before=v_before,
                volume_after=v_before
            )
            db.add(audit)
            db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)

        # 2. Validação Dimensional de Peças de 6 Metros
        if order_obj.has_long_items and not vehicle.allows_long_items:
            err_msg = (
                f"Inclusão rejeitada: o pedido '{order_id}' contém peças lineares de 6 metros "
                f"incompatíveis com o compartimento de carga do veículo '{vehicle.name}'."
            )
            audit = LoadPlanAudit(
                load_plan_id=plan.id,
                user_id="aprovador",
                action="ADD_ORDER",
                order_id=order_id,
                accepted=False,
                rejection_reason=err_msg,
                weight_before=w_before,
                weight_after=w_before,
                volume_before=v_before,
                volume_after=v_before
            )
            db.add(audit)
            db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)

        # Simulação dos novos totais
        cand_w = round(plan.total_weight_kg + order_obj.total_weight_kg, 2)
        cand_v = round(plan.total_volume_m3 + order_obj.total_volume_m3, 4)

        # Validação Rígida de Capacidade (RF-013-A e RNF-004)
        if cand_w > vehicle.capacity_kg:
            err_msg = f"Inclusão rejeitada: peso excederia a capacidade máxima ({cand_w:.2f} kg > {vehicle.capacity_kg:.2f} kg)."
            # Registra auditoria da tentativa rejeitada
            audit = LoadPlanAudit(
                load_plan_id=plan.id,
                user_id="aprovador",
                action="ADD_ORDER",
                order_id=order_id,
                accepted=False,
                rejection_reason=err_msg,
                weight_before=w_before,
                weight_after=w_before,
                volume_before=v_before,
                volume_after=v_before
            )
            db.add(audit)
            db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)

        if cand_v > vehicle.useful_volume_m3:
            err_msg = f"Inclusão rejeitada: volume excederia a capacidade máxima ({cand_v:.4f} m³ > {vehicle.useful_volume_m3:.4f} m³)."
            audit = LoadPlanAudit(
                load_plan_id=plan.id,
                user_id="aprovador",
                action="ADD_ORDER",
                order_id=order_id,
                accepted=False,
                rejection_reason=err_msg,
                weight_before=w_before,
                weight_after=w_before,
                volume_before=v_before,
                volume_after=v_before
            )
            db.add(audit)
            db.commit()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_msg)

        # Inclusão aceita
        new_deliv_order = plan.total_orders + 1
        new_item = LoadPlanItem(
            load_plan_id=plan.id,
            order_id=order_id,
            delivery_order=new_deliv_order,
            loading_order=1,
            score=0.0,
            efficiency=0.0,
            weight_kg=order_obj.total_weight_kg,
            volume_m3=order_obj.total_volume_m3,
            value=order_obj.value,
            city_name=order_obj.city_name,
        )
        db.add(new_item)

        # Atualiza a decisão correspondente
        dec = db.query(LoadPlanDecision).filter(
            LoadPlanDecision.load_plan_id == plan_id,
            LoadPlanDecision.order_id == order_id
        ).first()
        if dec:
            dec.included = True
            dec.exclusion_reason = "SELECIONADO_MANUALMENTE"

        plan.total_orders += 1
        plan.total_weight_kg = cand_w
        plan.total_volume_m3 = cand_v
        plan.total_value = round(plan.total_value + order_obj.value, 2)
        plan.weight_occupancy = round((cand_w / vehicle.capacity_kg) * 100, 2)
        plan.volume_occupancy = round((cand_v / vehicle.useful_volume_m3) * 100, 2)
        plan.is_manually_modified = True

        audit = LoadPlanAudit(
            load_plan_id=plan.id,
            user_id="aprovador",
            action="ADD_ORDER",
            order_id=order_id,
            accepted=True,
            weight_before=w_before,
            weight_after=cand_w,
            volume_before=v_before,
            volume_after=cand_v
        )
        db.add(audit)
        db.commit()
        db.refresh(plan)
        return plan


@router.post("/{plan_id}/approve", response_model=LoadPlanResponse, summary="Aprovar plano de carga")
def approve_load_plan(
    plan_id: int,
    req: ApprovePlanRequest = None,
    db: Session = Depends(get_db)
):
    """Registra a aprovação formal do plano de carga pelo responsável."""
    plan = db.query(LoadPlan).filter(LoadPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de carga não encontrado.")

    approver = (req.approver_name if req else None) or "aprovador"
    plan.approved_by = approver
    plan.approved_at = datetime.utcnow()

    db.add(LoadPlanAudit(
        load_plan_id=plan.id,
        user_id=approver,
        action="APPROVE",
        accepted=True,
        weight_before=plan.total_weight_kg,
        weight_after=plan.total_weight_kg,
        volume_before=plan.total_volume_m3,
        volume_after=plan.total_volume_m3
    ))

    db.commit()
    db.refresh(plan)
    return plan


@router.get("/{plan_id}/audit", response_model=List[LoadPlanAuditResponse], summary="Trilha de auditoria do plano")
def get_plan_audit(plan_id: int, db: Session = Depends(get_db)):
    """Retorna todas as tentativas de alteração manual e aprovações do plano."""
    return db.query(LoadPlanAudit).filter(LoadPlanAudit.load_plan_id == plan_id).all()


def _get_plan_report_data(plan_id: int, db: Session):
    """Auxiliar para extrair e normalizar dados de relatório de um plano de carga."""
    plan = db.query(LoadPlan).filter(LoadPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plano de carga não encontrado.")

    plan_items = db.query(LoadPlanItem).filter(
        LoadPlanItem.load_plan_id == plan_id
    ).order_by(LoadPlanItem.delivery_order).all()

    items_data = []
    has_long_items = False
    for it in plan_items:
        ord_obj = db.query(Order).filter(Order.id == it.order_id).first()
        is_long = ord_obj.has_long_items if ord_obj else False
        if is_long:
            has_long_items = True
        items_data.append({
            "delivery_order": it.delivery_order,
            "loading_order": it.loading_order,
            "order_id": it.order_id,
            "external_id": ord_obj.external_id if ord_obj else it.order_id,
            "city_name": it.city_name,
            "address_line": ord_obj.address_line if ord_obj else it.city_name,
            "formatted_address": ord_obj.formatted_address if ord_obj else None,
            "weight_kg": it.weight_kg,
            "total_weight_kg": it.weight_kg,
            "volume_m3": it.volume_m3,
            "total_volume_m3": it.volume_m3,
            "value": it.value,
            "total_value": it.value,
            "has_long_items": is_long,
            "is_mandatory": ord_obj.is_mandatory if ord_obj else False,
            "payment_on_delivery": ord_obj.payment_on_delivery if ord_obj else None,
        })

    plan_data = {
        "execution_id": plan.execution_id,
        "created_at": plan.created_at.strftime("%d/%m/%Y %H:%M"),
        "axis_name": plan.axis.name,
        "vehicle_name": plan.vehicle.name,
        "vehicle_plate": plan.vehicle.plate,
        "profile_name": plan.profile_snapshot.get("profile_name", "Padrão"),
        "total_orders": plan.total_orders,
        "total_value": plan.total_value,
        "limiting_resource": plan.limiting_resource,
        "total_weight_kg": plan.total_weight_kg,
        "weight_occupancy": plan.weight_occupancy,
        "total_volume_m3": plan.total_volume_m3,
        "volume_occupancy": plan.volume_occupancy,
        "estimated_cubing_pct": plan.estimated_cubing_pct,
        "algorithm_version": plan.algorithm_version,
        "solver_status": plan.solver_status,
        "solve_duration_ms": plan.solve_duration_ms,
        "has_long_items": has_long_items,
        "items": items_data
    }
    return plan, plan_data


@router.get("/{plan_id}/loading-sheet/pdf", summary="Baixar Mapa de Carregamento de Doca (LIFO) em PDF")
def download_loading_sheet_pdf(plan_id: int, db: Session = Depends(get_db)):
    """Gera o PDF oficial do Mapa de Carregamento de Doca, ordenado por sequência LIFO de estivagem."""
    plan, plan_data = _get_plan_report_data(plan_id, db)
    pdf_bytes = ReportService.generate_loading_sheet_pdf(plan_data)
    filename = f"carregamento_doca_{plan.execution_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{plan_id}/loading-sheet/html", response_class=Response, summary="Visualizar Mapa de Carregamento em HTML")
def view_loading_sheet_html(plan_id: int, db: Session = Depends(get_db)):
    """Retorna o HTML do Mapa de Carregamento de Doca para conferência rápida e impressão nativa."""
    _, plan_data = _get_plan_report_data(plan_id, db)
    html_str = ReportService.render_loading_sheet_html(plan_data)
    return Response(content=html_str, media_type="text/html")


@router.get("/{plan_id}/delivery-route/pdf", summary="Baixar Roteiro de Entregas Otimizado (TSP) em PDF")
def download_delivery_route_pdf(plan_id: int, db: Session = Depends(get_db)):
    """Gera o PDF oficial do Roteiro de Entregas, ordenado pela sequência do Caixeiro Viajante (TSP)."""
    plan, plan_data = _get_plan_report_data(plan_id, db)
    pdf_bytes = ReportService.generate_delivery_route_pdf(plan_data)
    filename = f"roteiro_entregas_tsp_{plan.execution_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{plan_id}/delivery-route/html", response_class=Response, summary="Visualizar Roteiro TSP em HTML")
def view_delivery_route_html(plan_id: int, db: Session = Depends(get_db)):
    """Retorna o HTML do Roteiro de Entregas Otimizado (TSP) para o motorista."""
    _, plan_data = _get_plan_report_data(plan_id, db)
    html_str = ReportService.render_delivery_route_html(plan_data)
    return Response(content=html_str, media_type="text/html")


@router.get("/{plan_id}/manifest/pdf", summary="Baixar Romaneio em PDF (Retrocompatível)")
def download_manifest_pdf(plan_id: int, db: Session = Depends(get_db)):
    """Gera e retorna o PDF do Romaneio de Carga (equivalente ao Mapa de Carregamento de Doca)."""
    plan, plan_data = _get_plan_report_data(plan_id, db)
    pdf_bytes = ReportService.generate_loading_sheet_pdf(plan_data)
    filename = f"romaneio_{plan.execution_id}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/{plan_id}/manifest/html", response_class=Response, summary="Visualizar Romaneio em HTML (Retrocompatível)")
def get_manifest_html(plan_id: int, db: Session = Depends(get_db)):
    """Retorna o HTML formatado do Romaneio de Carga."""
    _, plan_data = _get_plan_report_data(plan_id, db)
    html_str = ReportService.render_loading_sheet_html(plan_data)
    return Response(content=html_str, media_type="text/html")
