"""Rotas de consulta de pedidos e eixos rodoviários."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domain.models import Order, Axis, City
from app.domain.schemas.order_schema import OrderResponse

router = APIRouter(tags=["Pedidos e Eixos"])


@router.get("/orders", response_model=List[OrderResponse], summary="Listar pedidos com filtros")
def list_orders(
    axis_id: Optional[str] = Query(None, description="Filtrar por eixo rodoviário"),
    city_name: Optional[str] = Query(None, description="Filtrar por cidade/distrito"),
    status: Optional[str] = Query(None, description="Filtrar por status do pedido"),
    date: Optional[str] = Query(None, description="Filtrar por data (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """Retorna os pedidos elegíveis cadastrados no banco de dados conforme os filtros informados."""
    query = db.query(Order)
    if axis_id:
        query = query.filter(Order.axis_id == axis_id)
    if city_name:
        query = query.filter(Order.city_name == city_name.upper())
    if status:
        query = query.filter(Order.status == status)
    if date:
        query = query.filter(Order.date == date)

    return query.all()


@router.get("/axes", summary="Listar eixos rodoviários e localidades")
def list_axes(db: Session = Depends(get_db)):
    """Retorna a lista de eixos rodoviários ativos e as respectivas cidades atendidas."""
    axes = db.query(Axis).filter(Axis.active == True).all()
    res = []
    for ax in axes:
        cities = db.query(City).filter(City.axis_id == ax.id).order_by(City.delivery_order).all()
        res.append({
            "id": ax.id,
            "name": ax.name,
            "cities": [
                {
                    "id": c.id,
                    "name": c.name,
                    "delivery_order": c.delivery_order,
                    "is_district": c.is_district,
                    "parent_municipality": c.parent_municipality,
                    "is_external": c.is_external,
                    "latitude": c.latitude,
                    "longitude": c.longitude,
                }
                for c in cities
            ]
        })
    return res
