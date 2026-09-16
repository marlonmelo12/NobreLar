"""Esquemas Pydantic v2 para pedidos e itens componentes."""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OrderItemResponse(BaseModel):
    """Contrato de representação de um item componente do pedido."""
    id: int
    product_code: str
    product_desc: str
    quantity: float
    unit: str
    unit_weight_kg: float
    unit_volume_m3: float
    computed_weight_kg: float
    computed_volume_m3: float
    cubing_source: str
    is_estimated: bool

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Contrato de representação do pedido faturado para composição de carga."""
    id: str
    external_id: Optional[str] = None
    axis_id: str
    city_id: Optional[int] = None
    city_name: str

    # Endereço completo para testes reais e roteirização
    address_line: Optional[str] = None
    address_number: Optional[str] = None
    complement: Optional[str] = None
    neighborhood: Optional[str] = None
    state: str = "CE"
    postal_code: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    formatted_address: Optional[str] = None

    value: float
    status: str
    delivery_status: str
    payment_on_delivery: Optional[str] = None
    seller: Optional[str] = None
    date: str

    total_weight_kg: float
    total_volume_m3: float
    sale_frequency: int = 1

    is_split: bool = False
    parent_order_id: Optional[str] = None
    has_long_items: bool = False
    is_mandatory: bool = False

    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)
