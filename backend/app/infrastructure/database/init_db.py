"""Inicialização e carga de dados semente (seeds) do banco de dados NobreLOG IA.

Cria as tabelas e popula a frota oficial, perfis de otimização,
eixos rodoviários, cidades e usuários iniciais.
"""

import structlog
from sqlalchemy.orm import Session
from app.infrastructure.database.session import engine, Base
from app.infrastructure.security.passwords import get_password_hash
from app.core.seeds import (
    DEFAULT_VEHICLES,
    DEFAULT_PROFILES,
    DEFAULT_AXES,
    DEFAULT_USERS,
)
from app.core.constants import CITY_TO_AXIS_MAP
from app.core.geo_constants import REGION_COORDINATES_CACHE
from app.domain.models import (
    User,
    Vehicle,
    Axis,
    City,
    OptimizationProfile,
)

logger = structlog.get_logger()


def init_db(db: Session) -> None:
    """Cria tabelas e popula os dados semente fundamentais se o banco estiver vazio."""
    logger.info("Verificando e criando tabelas do banco de dados...")
    Base.metadata.create_all(bind=engine)

    # 1. Usuários do Sistema (RBAC)
    if db.query(User).count() == 0:
        logger.info("Populando usuários iniciais do sistema...")
        for u in DEFAULT_USERS:
            db.add(User(
                username=u["username"],
                password_hash=get_password_hash(u["password"]),
                role=u["role"],
            ))
        db.commit()

    # 2. Eixos Rodoviários
    if db.query(Axis).count() == 0:
        logger.info("Populando eixos rodoviários...")
        for ax in DEFAULT_AXES:
            db.add(Axis(
                id=ax["id"],
                name=ax["name"],
                active=ax["active"],
            ))
        db.commit()

    # 3. Cidades e Distritos
    if db.query(City).count() == 0:
        logger.info("Populando cidades e distritos com coordenadas oficiais...")
        for city_name, meta in CITY_TO_AXIS_MAP.items():
            coords = REGION_COORDINATES_CACHE.get(city_name)
            lat = coords[0] if coords else None
            lon = coords[1] if coords else None

            db.add(City(
                name=city_name,
                axis_id=meta["axis_id"],
                delivery_order=meta["delivery_order"],
                is_district=meta["is_district"],
                parent_municipality=meta.get("parent_municipality"),
                is_external=meta.get("is_external", True),
                latitude=lat,
                longitude=lon,
            ))
        db.commit()

    # 4. Frota de Veículos
    if db.query(Vehicle).count() == 0:
        logger.info("Populando frota oficial de veículos...")
        for v in DEFAULT_VEHICLES:
            db.add(Vehicle(
                id=v["id"],
                name=v["name"],
                plate=v["plate"],
                capacity_kg=v["capacity_kg"],
                useful_volume_m3=v["useful_volume_m3"],
                useful_length_m=v["useful_length_m"],
                allows_long_items=v["allows_long_items"],
                restricted_to_crateus=v["restricted_to_crateus"],
                operates_intermunicipal=v["operates_intermunicipal"],
                active=v["active"],
            ))
        db.commit()

    # 5. Perfis de Otimização Multicritério
    if db.query(OptimizationProfile).count() == 0:
        logger.info("Populando perfis de otimização padrão...")
        for p in DEFAULT_PROFILES:
            db.add(OptimizationProfile(
                id=p["id"],
                name=p["name"],
                w_peso=p["w_peso"],
                w_volume=p["w_volume"],
                w_valor=p["w_valor"],
                w_quantidade=p["w_quantidade"],
                objective_mode=p["objective_mode"],
                is_default=p["is_default"],
                description=p.get("description"),
            ))
        db.commit()

    logger.info("Inicialização do banco de dados concluída com sucesso!")
