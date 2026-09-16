"""Modelos de dados relacionais SQLAlchemy 2.0 para o sistema NobreLOG IA.

Implementa todas as entidades canônicas especificadas no documento de
implantação v3.0, com suporte a endereços reais, fatiamento de carga (order splitting),
restrições dimensionais (6m), controle territorial e auditoria integral.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Text, JSON, Index
)
from sqlalchemy.orm import relationship
from app.infrastructure.database.session import Base


class User(Base):
    """Usuário do sistema com controle de acesso baseado em papéis (RBAC)."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="operador")  # operador, aprovador, admin
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class Vehicle(Base):
    """Veículo de carga com capacidade física e restrições operacionais."""
    __tablename__ = "vehicles"

    id = Column(String(50), primary_key=True)  # ex: 'accelo-815-01'
    name = Column(String(100), nullable=False)
    plate = Column(String(20), nullable=False)
    capacity_kg = Column(Float, nullable=False)
    useful_volume_m3 = Column(Float, nullable=False)
    useful_length_m = Column(Float, nullable=False, default=5.50)
    allows_long_items = Column(Boolean, nullable=False, default=False)
    restricted_to_crateus = Column(Boolean, nullable=False, default=False)
    operates_intermunicipal = Column(Boolean, nullable=False, default=True)
    active = Column(Boolean, nullable=False, default=True)

    load_plans = relationship("LoadPlan", back_populates="vehicle")


class Axis(Base):
    """Eixo rodoviário regional intermunicipal ou urbano."""
    __tablename__ = "axes"

    id = Column(String(50), primary_key=True)  # ex: 'eixo-4-norte-serra'
    name = Column(String(100), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    cities = relationship("City", back_populates="axis")
    orders = relationship("Order", back_populates="axis")
    load_plans = relationship("LoadPlan", back_populates="axis")


class City(Base):
    """Cidade, distrito ou localidade atendida por determinado eixo."""
    __tablename__ = "cities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    axis_id = Column(String(50), ForeignKey("axes.id"), nullable=False)
    delivery_order = Column(Integer, nullable=False, default=1)
    is_district = Column(Boolean, nullable=False, default=False)
    parent_municipality = Column(String(100), nullable=True)  # ex: 'CRATEUS'
    is_external = Column(Boolean, nullable=False, default=True)  # True = viagem intermunicipal
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    axis = relationship("Axis", back_populates="cities")
    orders = relationship("Order", back_populates="city")


class Product(Base):
    """Produto/SKU com ficha técnica e indicadores de cubagem."""
    __tablename__ = "products"

    code = Column(String(50), primary_key=True)
    description = Column(String(255), nullable=False)
    unit = Column(String(20), nullable=False)
    weight_kg = Column(Float, nullable=False, default=0.0)
    volume_m3 = Column(Float, nullable=False, default=0.0)
    m2_per_box = Column(Float, nullable=True)
    estimated = Column(Boolean, nullable=False, default=False)
    source = Column(String(50), nullable=False, default="ausente")  # ranking_top85, heuristica_categoria, etc.


class Order(Base):
    """Pedido faturado elegível para composição de carga."""
    __tablename__ = "orders"

    id = Column(String(50), primary_key=True)  # 'L12608278' ou 'L12609291-P1'
    external_id = Column(String(50), nullable=True, index=True)
    axis_id = Column(String(50), ForeignKey("axes.id"), nullable=False, index=True)
    city_id = Column(Integer, ForeignKey("cities.id"), nullable=True)

    # Endereço completo para testes reais e roteirização
    address_line = Column(String(255), nullable=True)
    address_number = Column(String(50), nullable=True)
    complement = Column(String(100), nullable=True)
    neighborhood = Column(String(100), nullable=True)
    city_name = Column(String(100), nullable=False, index=True)
    state = Column(String(10), nullable=False, default="CE")
    postal_code = Column(String(20), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    formatted_address = Column(String(255), nullable=True)

    # Valores comerciais e de entrega
    value = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="Faturado")
    delivery_status = Column(String(50), nullable=False, default="ENTREGUE")
    payment_on_delivery = Column(String(50), nullable=True)  # ex: 'A RECEBER'
    seller = Column(String(100), nullable=True)
    date = Column(String(20), nullable=False, index=True)  # YYYY-MM-DD

    # Dimensões físicas calculadas
    total_weight_kg = Column(Float, nullable=False, default=0.0)
    total_volume_m3 = Column(Float, nullable=False, default=0.0)
    sale_frequency = Column(Integer, nullable=False, default=1)

    # Regras estruturais
    is_split = Column(Boolean, nullable=False, default=False)
    parent_order_id = Column(String(50), nullable=True, index=True)
    has_long_items = Column(Boolean, nullable=False, default=False)
    is_mandatory = Column(Boolean, nullable=False, default=False)

    axis = relationship("Axis", back_populates="orders")
    city = relationship("City", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Item componente de um pedido com cubagem calculada."""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), ForeignKey("orders.id"), nullable=False, index=True)
    product_code = Column(String(50), nullable=False, index=True)
    product_desc = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False, default=1.0)
    unit = Column(String(20), nullable=False)

    unit_weight_kg = Column(Float, nullable=False, default=0.0)
    unit_volume_m3 = Column(Float, nullable=False, default=0.0)
    computed_weight_kg = Column(Float, nullable=False, default=0.0)
    computed_volume_m3 = Column(Float, nullable=False, default=0.0)
    cubing_source = Column(String(50), nullable=False, default="ausente")
    is_estimated = Column(Boolean, nullable=False, default=False)

    order = relationship("Order", back_populates="items")


class OptimizationProfile(Base):
    """Perfil parametrizado de pesos para a função objetivo multicritério."""
    __tablename__ = "optimization_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    w_peso = Column(Float, nullable=False, default=0.25)
    w_volume = Column(Float, nullable=False, default=0.25)
    w_valor = Column(Float, nullable=False, default=0.30)
    w_quantidade = Column(Float, nullable=False, default=0.20)
    objective_mode = Column(String(50), nullable=False, default="score_agregado")
    is_default = Column(Boolean, nullable=False, default=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class LoadPlan(Base):
    """Plano de carga oficial gerado pelo otimizador ou editado."""
    __tablename__ = "load_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(50), unique=True, nullable=False, index=True)
    axis_id = Column(String(50), ForeignKey("axes.id"), nullable=False)
    vehicle_id = Column(String(50), ForeignKey("vehicles.id"), nullable=False)
    profile_id = Column(Integer, ForeignKey("optimization_profiles.id"), nullable=False)
    profile_snapshot = Column(JSON, nullable=False)  # Snapshot dos pesos para garantir determinismo

    total_orders = Column(Integer, nullable=False, default=0)
    total_value = Column(Float, nullable=False, default=0.0)
    total_weight_kg = Column(Float, nullable=False, default=0.0)
    total_volume_m3 = Column(Float, nullable=False, default=0.0)
    weight_occupancy = Column(Float, nullable=False, default=0.0)
    volume_occupancy = Column(Float, nullable=False, default=0.0)
    limiting_resource = Column(String(20), nullable=False, default="PESO")
    estimated_cubing_pct = Column(Float, nullable=False, default=0.0)

    solver_status = Column(String(50), nullable=False, default="OPTIMAL")
    optimality_gap = Column(Float, nullable=True)
    solve_duration_ms = Column(Integer, nullable=False, default=0)
    algorithm_version = Column(String(50), nullable=False, default="cpsat-v3.0")

    is_manually_modified = Column(Boolean, nullable=False, default=False)
    approved_by = Column(String(100), nullable=True)
    approved_at = Column(DateTime, nullable=True)
    valid = Column(Boolean, nullable=False, default=True)
    created_by = Column(String(100), nullable=False, default="sistema")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    axis = relationship("Axis", back_populates="load_plans")
    vehicle = relationship("Vehicle", back_populates="load_plans")
    items = relationship("LoadPlanItem", back_populates="load_plan", cascade="all, delete-orphan")
    decisions = relationship("LoadPlanDecision", back_populates="load_plan", cascade="all, delete-orphan")
    audits = relationship("LoadPlanAudit", back_populates="load_plan", cascade="all, delete-orphan")


class LoadPlanItem(Base):
    """Pedido selecionado e alocado na carga, com sequência LIFO."""
    __tablename__ = "load_plan_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    load_plan_id = Column(Integer, ForeignKey("load_plans.id"), nullable=False, index=True)
    order_id = Column(String(50), nullable=False, index=True)
    delivery_order = Column(Integer, nullable=False)  # Ordem de entrega ao cliente
    loading_order = Column(Integer, nullable=False)   # Ordem de carregamento na doca (LIFO)

    score = Column(Float, nullable=False, default=0.0)
    efficiency = Column(Float, nullable=False, default=0.0)
    weight_kg = Column(Float, nullable=False, default=0.0)
    volume_m3 = Column(Float, nullable=False, default=0.0)
    value = Column(Float, nullable=False, default=0.0)
    city_name = Column(String(100), nullable=False)

    load_plan = relationship("LoadPlan", back_populates="items")


class LoadPlanDecision(Base):
    """Registro explicável de inclusão ou exclusão de cada pedido avaliado."""
    __tablename__ = "load_plan_decisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    load_plan_id = Column(Integer, ForeignKey("load_plans.id"), nullable=False, index=True)
    order_id = Column(String(50), nullable=False, index=True)
    included = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False, default=0.0)
    efficiency = Column(Float, nullable=False, default=0.0)
    peso_pct = Column(Float, nullable=False, default=0.0)
    volume_pct = Column(Float, nullable=False, default=0.0)
    exclusion_reason = Column(String(100), nullable=False)  # SELECIONADO, EXCEDE_PESO_INDIVIDUAL, etc.

    load_plan = relationship("LoadPlan", back_populates="decisions")


class LoadPlanAudit(Base):
    """Trilha de auditoria para modificações manuais e aprovações."""
    __tablename__ = "load_plan_audits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    load_plan_id = Column(Integer, ForeignKey("load_plans.id"), nullable=False, index=True)
    user_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # ADD_ORDER, REMOVE_ORDER, APPROVE, REJECT
    order_id = Column(String(50), nullable=True)
    accepted = Column(Boolean, nullable=False)
    rejection_reason = Column(String(255), nullable=True)
    weight_before = Column(Float, nullable=True)
    weight_after = Column(Float, nullable=True)
    volume_before = Column(Float, nullable=True)
    volume_after = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    load_plan = relationship("LoadPlan", back_populates="audits")


class CleaningLog(Base):
    """Registro de limpeza, padronização e exclusão de pedidos descartados."""
    __tablename__ = "cleaning_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(50), nullable=True, index=True)
    record_reference = Column(String(100), nullable=False, index=True)  # ex: 'L12608278'
    rule_applied = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)  # REMOVIDO, CORRIGIDO, MARCADO_REVISAO
    field = Column(String(50), nullable=False)
    original_value = Column(String(255), nullable=True)
    corrected_value = Column(String(255), nullable=True)
    reason = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


# Índices estratégicos para consultas operacionais rápidas
Index("idx_orders_axis_status_date", Order.axis_id, Order.status, Order.date)
Index("idx_decisions_plan_included", LoadPlanDecision.load_plan_id, LoadPlanDecision.included)
