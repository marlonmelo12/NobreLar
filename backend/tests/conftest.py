"""Configuração global do Pytest para o sistema NobreLOG IA.

Garante que as migrações, seeds e pedidos de teste estejam devidamente
carregados no banco de dados configurado para o ambiente de testes.
"""

import sys
from pathlib import Path
import pytest

# Adiciona o diretório backend ao sys.path para importação de app.*
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.infrastructure.database.session import SessionLocal, engine, Base
from app.infrastructure.database.init_db import init_db
from app.domain.models import Order, OrderItem, City
from app.services.ingest_service import IngestService


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Garante que as tabelas, sementes e pedidos existam antes dos testes de integração."""
    db = SessionLocal()
    try:
        init_db(db)

        # Se não existirem pedidos, executa a ingestão dos dados brutos
        if db.query(Order).count() == 0:
            try:
                ingest_svc = IngestService(db)
                ingest_svc.ingest_all_raw_files()
            except Exception as e:
                print(f"Aviso na ingestão de dados brutos de teste: {e}")

        # Se ainda assim não houver pedidos para o Eixo 4 (ex: ambiente isolado sem CSV),
        # insere pedidos sintéticos válidos para garantir a execução determinística dos testes
        eixo4_count = db.query(Order).filter(Order.axis_id == "eixo-4-norte-serra").count()
        if eixo4_count == 0:
            # Garante cidade
            city = db.query(City).filter(City.name == "IPAPORANGA").first()
            city_id = city.id if city else None

            sample_orders = [
                Order(
                    id="TEST-E4-01",
                    axis_id="eixo-4-norte-serra",
                    city_id=city_id,
                    city_name="IPAPORANGA",
                    value=4500.0,
                    status="Faturado",
                    delivery_status="PENDENTE",
                    date="15/09/2026",
                    total_weight_kg=2000.0,
                    total_volume_m3=1.5,
                    has_long_items=False
                ),
                Order(
                    id="TEST-E4-02",
                    axis_id="eixo-4-norte-serra",
                    city_id=city_id,
                    city_name="IPAPORANGA",
                    value=3800.0,
                    status="Faturado",
                    delivery_status="PENDENTE",
                    date="15/09/2026",
                    total_weight_kg=1800.0,
                    total_volume_m3=1.2,
                    has_long_items=False
                ),
                Order(
                    id="TEST-E4-03",
                    axis_id="eixo-4-norte-serra",
                    city_id=city_id,
                    city_name="PORANGA",
                    value=1200.0,
                    status="Faturado",
                    delivery_status="PENDENTE",
                    date="15/09/2026",
                    total_weight_kg=500.0,
                    total_volume_m3=0.4,
                    has_long_items=True
                )
            ]
            for o in sample_orders:
                db.add(o)
            db.commit()
    finally:
        db.close()
