"""Serviço de ingestão, sanitização e persistência de arquivos CSV de pedidos.

Coordena:
- Leitura dos arquivos de pedidos (Semana 1 a 4 e Dados de Entregas)
- Aplicação dos parsers de IDs, datas, moedas e itens
- Execução das regras de limpeza com registro em CleaningLog
- Cubagem técnica de todos os itens e detecção de peças de 6m
- Mapeamento geográfico para os eixos rodoviários correspondentes
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
from sqlalchemy.orm import Session
import structlog

from app.core.config import settings
from app.core.constants import CITY_TO_AXIS_MAP
from app.domain.models import Order, OrderItem, City, Axis, Product, CleaningLog
from app.services.parsers import (
    sanitize_order_id,
    sanitize_brazilian_date,
    clean_currency,
    parse_order_items,
    parse_address_components
)
from app.services.cleaning import CleaningService
from app.services.cubagem_service import CubagemService
from app.services.geocoder_service import GeocoderService

logger = structlog.get_logger()


class IngestService:
    """Coordena o pipeline de ingestão de dados para o banco de dados."""

    def __init__(self, db: Session):
        self.db = db
        self.cubagem = CubagemService()
        self.geocoder = GeocoderService()

    def ingest_catalog_products(self) -> int:
        """Sincroniza o catálogo técnico do Top 85 com a tabela de produtos no banco."""
        count = 0
        for code, prod_data in self.cubagem.catalog.items():
            existing = self.db.query(Product).filter(Product.code == code).first()
            if not existing:
                p = Product(
                    code=code,
                    description=prod_data["description"],
                    unit="UN",
                    weight_kg=prod_data["unit_weight_kg"],
                    volume_m3=prod_data["unit_volume_m3"],
                    m2_per_box=prod_data.get("m2_per_box"),
                    estimated=prod_data.get("estimated", False),
                    source=prod_data.get("source", "ranking_top85")
                )
                self.db.add(p)
                count += 1
        self.db.commit()
        logger.info(f"Sincronizados {count} novos produtos do catálogo no banco de dados.")
        return count

    def ingest_orders_csv(self, file_path: Path, scope_regional: bool = True) -> Dict[str, Any]:
        """Lê um arquivo CSV de pedidos e carrega os registros válidos no banco de dados."""
        if not file_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

        # Tenta ler com separador ';' e fallback para ','
        try:
            df = pd.read_csv(file_path, sep=";", encoding="utf-8", dtype=str)
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",", encoding="utf-8", dtype=str)
        except Exception:
            df = pd.read_csv(file_path, sep=";", encoding="latin1", dtype=str)
            if len(df.columns) <= 1:
                df = pd.read_csv(file_path, sep=",", encoding="latin1", dtype=str)

        total_read = len(df)
        imported_count = 0
        removed_cleaning_count = 0

        logger.info(f"Iniciando ingestão de {total_read} registros do arquivo {file_path.name}")

        for _, row in df.iterrows():
            row_dict = row.to_dict()

            # 1. Avaliação de Limpeza (Balcão, Cancelados, Crateús)
            is_eligible, cleaning_logs = CleaningService.evaluate_order(row_dict, scope_regional=scope_regional)
            if cleaning_logs:
                for log in cleaning_logs:
                    self.db.add(log)

            if not is_eligible:
                removed_cleaning_count += 1
                continue

            # 2. Sanitização dos campos fundamentais
            raw_id = row_dict.get("Pedido", row_dict.get("ID", row_dict.get("PEDIDO", "")))
            clean_id = sanitize_order_id(raw_id)
            if clean_id == "INVALIDO":
                continue

            # Evita duplicidade de pedido já inserido
            existing = self.db.query(Order).filter(Order.id == clean_id).first()
            if existing:
                continue

            clean_date = sanitize_brazilian_date(row_dict.get("Data", row_dict.get("DATA", "")))
            clean_val = clean_currency(row_dict.get("Valor_Pedido", row_dict.get("VALOR DO PEDIDO", 0.0)))
            seller = str(row_dict.get("Vendedor", row_dict.get("VENDEDOR", ""))).strip()
            city_raw = str(row_dict.get("Cidade", row_dict.get("CIDADE", ""))).strip().upper()
            status = str(row_dict.get("Situacao", row_dict.get("SITUACAO", "Faturado"))).strip()
            deliv_status = str(row_dict.get("Logistica", row_dict.get("LOGISTICA", "ENTREGUE"))).strip()
            pgt_entrega = str(row_dict.get("PGT ENTREGA?", row_dict.get("Situacao_CSV_Entrega", ""))).strip().upper()

            # 3. Mapeamento de Eixo e Cidade
            meta_axis = CITY_TO_AXIS_MAP.get(city_raw)
            if not meta_axis:
                # Cidade não mapeada -> registra em CleaningLog
                self.db.add(CleaningLog(
                    record_reference=clean_id,
                    rule_applied="cidade_fora_do_escopo",
                    action="REMOVIDO",
                    field="Cidade",
                    original_value=city_raw,
                    reason=f"A localidade '{city_raw}' não pertence a nenhum dos 5 eixos regionais mapeados.",
                ))
                removed_cleaning_count += 1
                continue

            axis_id = meta_axis["axis_id"]
            city_obj = self.db.query(City).filter(City.name == city_raw).first()
            city_id = city_obj.id if city_obj else None

            # 4. Endereço e Geocodificação
            addr_raw = row_dict.get("Endereco", row_dict.get("Endereço", row_dict.get("OBSERVAÇÃO", None)))
            addr_parts = parse_address_components(addr_raw)
            lat, lon = self.geocoder.get_coordinates(
                city_name=city_raw,
                address_line=addr_parts.get("address_line"),
                neighborhood=addr_parts.get("neighborhood")
            )

            # 5. Parsing e Cubagem dos Itens
            raw_items = row_dict.get("Itens_Resumo", row_dict.get("ITENS", ""))
            items_parsed = parse_order_items(raw_items)
            cubing_res = self.cubagem.compute_order_cubing(items_parsed)

            # 6. Instanciação e Persistência do Pedido
            order_entity = Order(
                id=clean_id,
                external_id=str(raw_id),
                axis_id=axis_id,
                city_id=city_id,
                address_line=addr_parts.get("address_line"),
                address_number=addr_parts.get("address_number"),
                neighborhood=addr_parts.get("neighborhood"),
                city_name=city_raw,
                state="CE",
                postal_code=addr_parts.get("postal_code"),
                latitude=lat,
                longitude=lon,
                formatted_address=f"{addr_parts.get('address_line') or city_raw}, {city_raw} - CE",
                value=clean_val,
                status=status,
                delivery_status=deliv_status,
                payment_on_delivery=pgt_entrega,
                seller=seller,
                date=clean_date,
                total_weight_kg=cubing_res["total_weight_kg"],
                total_volume_m3=cubing_res["total_volume_m3"],
                has_long_items=cubing_res["has_long_items"],
                is_split=False,
                is_mandatory=False
            )
            self.db.add(order_entity)

            # Adiciona os itens agregados
            for it in cubing_res["items"]:
                self.db.add(OrderItem(
                    order_id=clean_id,
                    product_code=it["product_code"],
                    product_desc=it["product_desc"],
                    quantity=it["effective_quantity"],
                    unit=it["unit"],
                    unit_weight_kg=it["unit_weight_kg"],
                    unit_volume_m3=it["unit_volume_m3"],
                    computed_weight_kg=it["computed_weight_kg"],
                    computed_volume_m3=it["computed_volume_m3"],
                    cubing_source=it["cubing_source"],
                    is_estimated=it["is_estimated"],
                ))

            imported_count += 1

        self.db.commit()

        logger.info(
            f"Ingestão concluída: {imported_count} pedidos importados, "
            f"{removed_cleaning_count} descartados pela limpeza."
        )

        return {
            "file": file_path.name,
            "total_read": total_read,
            "imported": imported_count,
            "removed_cleaning": removed_cleaning_count
        }

    def ingest_all_raw_files(self) -> Dict[str, Any]:
        """Executa a carga em lote de todos os arquivos brutos disponíveis em data/raw/."""
        # 1. Catálogo Top 85
        self.ingest_catalog_products()

        # 2. Arquivos de Pedidos Filtrados por Semana
        results = []
        for week in [1, 2, 3, 4]:
            pattern = f"Pedidos_Filtrados_Semana_{week}*.csv"
            matches = list(settings.DATA_RAW_DIR.glob(pattern))
            for f in matches:
                res = self.ingest_orders_csv(f, scope_regional=True)
                results.append(res)

        return {"status": "SUCESSO", "files_processed": results}
