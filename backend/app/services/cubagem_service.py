"""Módulo de cálculo de cubagem, catálogo técnico e fallback heurístico por categoria.

Implementa os requisitos RF-005, RF-005-A, RF-005-B, RF-006 e RF-006-A:
- Cruzamento com o catálogo técnico oficial (Ranking_Top85_Materiais.csv)
- Conversão de m² de pisos para caixas inteiras via math.ceil
- Fallback heurístico para produtos fora do Top 85
- Detecção e marcação de peças de 6 metros (tubulações e treliças)
- Rastreabilidade total da origem do peso e volume calculados
"""

import re
import math
from pathlib import Path
from typing import Dict, Any, Optional
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class CubagemService:
    """Serviço responsável pela cubagem técnica dos produtos e pedidos."""

    def __init__(self, catalog_csv_path: Optional[Path] = None):
        self.catalog_path = catalog_csv_path or (settings.DATA_RAW_DIR / "Ranking_Top85_Materiais.csv")
        self.catalog: Dict[str, Dict[str, Any]] = {}
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Carrega e trata a base de dados oficial Ranking_Top85_Materiais.csv."""
        if not self.catalog_path.exists():
            logger.warning(f"Arquivo de catálogo não encontrado em: {self.catalog_path}")
            return

        try:
            with open(self.catalog_path, mode="r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            if not lines:
                return

            header = [h.strip() for h in lines[0].split(";")]

            for line in lines[1:]:
                parts = [p.strip() for p in line.split(";")]
                if len(parts) < 8:
                    continue

                code = parts[1].strip()
                desc = parts[2].strip().replace('"', '')
                unit_sales = parts[5].strip()

                # Extrai peso numérico
                raw_peso = parts[6].replace('"', '').replace('≈', '').replace('kg', '').strip()
                peso_match = re.search(r"([\d.,]+)", raw_peso)
                peso = float(peso_match.group(1).replace(',', '.')) if peso_match else 0.0

                # Extrai volume numérico
                raw_vol = parts[7].replace('"', '').replace('≈', '').replace('m3', '').replace('m³', '').strip()
                vol_match = re.search(r"([\d.,]+)", raw_vol)
                vol = float(vol_match.group(1).replace(',', '.')) if vol_match else 0.0

                # Identifica se é estimado na ficha técnica
                dado_estimado = "SIM" in parts[8].upper() if len(parts) > 8 else True

                # Extrai metragem por caixa para pisos (ex: '2,30 m²')
                m2_per_box = None
                m2_match = re.search(r"([\d.,]+)\s*m[²2]", unit_sales, re.IGNORECASE)
                if m2_match:
                    try:
                        m2_per_box = float(m2_match.group(1).replace(',', '.'))
                    except ValueError:
                        m2_per_box = 2.30

                # Identifica peças de 6 metros no catálogo
                d_upper = desc.upper()
                has_long = any(k in d_upper for k in ['6M', '6 METROS', '6000MM', 'CANO', 'TUBO', 'TRELICA'])

                self.catalog[code] = {
                    "code": code,
                    "description": desc,
                    "unit_weight_kg": peso,
                    "unit_volume_m3": vol,
                    "m2_per_box": m2_per_box,
                    "estimated": dado_estimado,
                    "source": "ranking_top85",
                    "has_long_items": has_long,
                }

            logger.info(f"Catálogo técnico Top 85 carregado com {len(self.catalog)} produtos.")

        except Exception as e:
            logger.error(f"Erro ao carregar catálogo técnico Top 85: {e}")

    def classify_and_fallback(self, product_desc: str) -> Dict[str, Any]:
        """Aplica parâmetros médios de classe para produtos fora do Top 85.

        Garante que nenhum pedido seja sumariamente descartado por falta de cubagem,
        conforme especificado no requisito RF-005-B e ADR-0009.
        """
        d = product_desc.upper()

        # 1. Tubulações e Peças Lineares de 6 metros
        if any(k in d for k in ['CANO', 'TUBO', 'TRELICA', 'ESPACADOR 6M', 'FORRO NOVAFORMA', '6000MM', 'BARRA DE FERRO']):
            return {
                "unit_weight_kg": 0.50,
                "unit_volume_m3": 0.0080,
                "has_long_items": True,
                "source": "heuristica_longo",
                "estimated": True,
            }

        # 2. Cimentos e Argamassas
        if any(k in d for k in ['CIMENTO', 'ARGAMASSA', 'GESSO', 'CAL ']):
            return {
                "unit_weight_kg": 15.0,
                "unit_volume_m3": 0.0100,
                "has_long_items": False,
                "source": "heuristica_argamassa",
                "estimated": True,
            }

        # 3. Cerâmicas e Pisos
        if any(k in d for k in ['PISO', 'PORC', 'REV', 'CERBRAS', 'POINTER', 'KARINA', 'REVESTIMENTO']):
            return {
                "unit_weight_kg": 14.0,
                "unit_volume_m3": 0.0090,
                "has_long_items": False,
                "source": "heuristica_piso",
                "estimated": True,
            }

        # 4. Caixas d'Água e Reservatórios
        if any(k in d for k in ['CX. DAGUA', 'CAIXA D AGUA', 'BAKOF', 'FORTLEV', 'RESERVATORIO']):
            return {
                "unit_weight_kg": 15.0,
                "unit_volume_m3": 1.5000,
                "has_long_items": False,
                "source": "heuristica_caixa",
                "estimated": True,
            }

        # 5. Conexões Hidráulicas
        if any(k in d for k in ['JOELHO', 'TEE ', 'ADAPTADOR', 'LUVA', 'CURVA', 'SIFAO', 'VALVULA', 'ENGATE']):
            return {
                "unit_weight_kg": 0.05,
                "unit_volume_m3": 0.0003,
                "has_long_items": False,
                "source": "heuristica_conexao",
                "estimated": True,
            }

        # 6. Louças Sanitárias e Pias
        if any(k in d for k in ['VASO', 'BACIA', 'LOUCA', 'CUBA', 'LAVATORIO', 'ASSENTO', 'PIA ']):
            return {
                "unit_weight_kg": 20.0,
                "unit_volume_m3": 0.1000,
                "has_long_items": False,
                "source": "heuristica_louca",
                "estimated": True,
            }

        # 7. Elétrica e Iluminação
        if any(k in d for k in ['CABO', 'FIO', 'DISJUNTOR', 'TOMADA', 'LUMINARIA', 'REFLETOR', 'LAMPADA', 'INTERRUPTOR']):
            return {
                "unit_weight_kg": 0.10,
                "unit_volume_m3": 0.0005,
                "has_long_items": False,
                "source": "heuristica_eletrica",
                "estimated": True,
            }

        # 8. Tintas e Químicos
        if any(k in d for k in ['TINTA', 'LATEX', 'TEXT.', 'VERNIZ', 'MASSA CORRIDA', 'SELADOR', 'ESMALTE']):
            return {
                "unit_weight_kg": 18.0,
                "unit_volume_m3": 0.0200,
                "has_long_items": False,
                "source": "heuristica_tinta",
                "estimated": True,
            }

        # Fallback Geral (Miudezas, Ferramentas, Parafusos e Fixação)
        return {
            "unit_weight_kg": 0.25,
            "unit_volume_m3": 0.0008,
            "has_long_items": False,
            "source": "heuristica_geral",
            "estimated": True,
        }

    def compute_item_cubing(self, product_code: str, product_desc: str, quantity: float, unit: str) -> Dict[str, Any]:
        """Calcula a cubagem de um item individual de pedido.

        Aplica conversão de m² para caixas quando aplicável (RF-006).
        """
        # 1. Consulta no Top 85
        if product_code in self.catalog:
            prod_info = self.catalog[product_code]
            unit_w = prod_info["unit_weight_kg"]
            unit_v = prod_info["unit_volume_m3"]
            m2_box = prod_info.get("m2_per_box")
            source = prod_info["source"]
            is_est = prod_info["estimated"]
            has_long = prod_info["has_long_items"]
        else:
            # 2. Fallback heurístico por categoria
            fb = self.classify_and_fallback(product_desc)
            unit_w = fb["unit_weight_kg"]
            unit_v = fb["unit_volume_m3"]
            m2_box = 2.30 if "piso" in fb["source"] else None
            source = fb["source"]
            is_est = fb["estimated"]
            has_long = fb["has_long_items"]

        # Conversão de piso (m² comercializados -> caixas inteiras arredondadas para cima)
        effective_qty = quantity
        if unit.upper() in ["MT", "M2", "M²"] and m2_box and m2_box > 0:
            effective_qty = float(math.ceil(round(quantity / m2_box, 6)))

        tot_w = round(effective_qty * unit_w, 2)
        tot_v = round(effective_qty * unit_v, 4)

        return {
            "product_code": product_code,
            "product_desc": product_desc,
            "quantity": quantity,
            "effective_quantity": effective_qty,
            "unit": unit,
            "unit_weight_kg": unit_w,
            "unit_volume_m3": unit_v,
            "computed_weight_kg": tot_w,
            "computed_volume_m3": tot_v,
            "cubing_source": source,
            "is_estimated": is_est,
            "has_long_items": has_long,
        }

    def compute_order_cubing(self, items: list) -> Dict[str, Any]:
        """Agrega o peso, volume e indicadores de cubagem para todos os itens do pedido."""
        total_w = 0.0
        total_v = 0.0
        estimated_w = 0.0
        estimated_v = 0.0
        has_long = False
        computed_items = []

        for it in items:
            res = self.compute_item_cubing(
                product_code=it.get("product_code", "00000"),
                product_desc=it.get("product_desc", ""),
                quantity=it.get("quantity", 1.0),
                unit=it.get("unit", "UN")
            )
            computed_items.append(res)
            total_w += res["computed_weight_kg"]
            total_v += res["computed_volume_m3"]

            if res["is_estimated"]:
                estimated_w += res["computed_weight_kg"]
                estimated_v += res["computed_volume_m3"]

            if res["has_long_items"]:
                has_long = True

        est_pct_w = (estimated_w / total_w) if total_w > 0 else 0.0
        est_pct_v = (estimated_v / total_v) if total_v > 0 else 0.0

        return {
            "items": computed_items,
            "total_weight_kg": round(total_w, 2),
            "total_volume_m3": round(total_v, 4),
            "has_long_items": has_long,
            "estimated_weight_pct": round(est_pct_w * 100, 2),
            "estimated_volume_pct": round(est_pct_v * 100, 2),
        }
