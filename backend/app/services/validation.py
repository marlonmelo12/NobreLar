"""Módulo de validação independente das soluções e planos de carga.

Implementa os requisitos RF-010 e RNF-004:
- Recalcula diretamente sobre o conjunto selecionado todos os invariantes físicos
- Não confia no solver nem herda eventuais erros de arredondamento do modelo matemático
- Verifica adequação de capacidade, eixo, unicidade, limpeza, restrição de 6m e restrição territorial
- Bloqueia a aprovação ou persistência de qualquer plano inválido
"""

from typing import List, Dict, Any, Tuple, Optional, Set
import structlog
from app.core.constants import CITY_TO_AXIS_MAP

logger = structlog.get_logger()


class SolutionValidationError(Exception):
    """Exceção levantada quando um plano de carga viola qualquer invariante de negócio ou física."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


class IndependentValidator:
    """Validador isolado e independente de planos de carga."""

    @staticmethod
    def validate_plan(
        selected_orders: List[Dict[str, Any]],
        capacity_kg: float,
        capacity_m3: float,
        target_axis_id: str,
        allows_long_items: bool,
        restricted_to_crateus: bool = False,
        cleaning_discarded_ids: Optional[set] = None
    ) -> Tuple[bool, List[str]]:
        """Valida exaustivamente o conjunto de pedidos selecionados para um plano de carga.

        Retorna:
            (is_valid, list_of_errors)
        """
        errors: List[str] = []
        discarded_set = cleaning_discarded_ids or set()

        if not selected_orders:
            # Plano vazio é matematicamente viável, porém sem carga
            return True, []

        tot_weight = 0.0
        tot_volume = 0.0
        seen_ids = set()

        for o in selected_orders:
            order_id = o.get("id", "SEM_ID")

            # 1. Verificação de Duplicidade
            if order_id in seen_ids:
                errors.append(f"Invariante violado: pedido duplicado '{order_id}' no plano de carga.")
            seen_ids.add(order_id)

            # 2. Verificação de Pedidos Descartados na Limpeza
            if order_id in discarded_set:
                errors.append(f"Invariante violado: pedido '{order_id}' foi descartado na limpeza e não pode compor carga.")

            # 3. Verificação de Eixo Rodoviário Correto
            order_axis = o.get("axis_id")
            if target_axis_id and order_axis and order_axis != target_axis_id:
                errors.append(
                    f"Invariante violado: pedido '{order_id}' pertence ao eixo '{order_axis}', "
                    f"divergente do eixo requisitado '{target_axis_id}'."
                )

            # 4. Verificação de Restrição Dimensional de 6 metros
            has_long = o.get("has_long_items", False)
            if has_long and not allows_long_items:
                errors.append(
                    f"Invariante dimensional violado: pedido '{order_id}' contém peças de 6 metros "
                    f"e o veículo alocado não comporta peças lineares longas."
                )

            # 5. Verificação de Restrição Territorial
            if restricted_to_crateus:
                city_name = str(o.get("city_name", "")).strip().upper()
                meta_city = CITY_TO_AXIS_MAP.get(city_name)
                if meta_city and meta_city.get("is_external", False):
                    errors.append(
                        f"Invariante territorial violado: pedido '{order_id}' tem destino em '{city_name}' "
                        f"(cidade externa), mas o veículo selecionado é restrito a Crateús e seus distritos."
                    )

            # Acumula dimensões físicas
            tot_weight += float(o.get("total_weight_kg", o.get("weight_kg", 0.0)))
            tot_volume += float(o.get("total_volume_m3", o.get("volume_m3", 0.0)))

        # 6. Inviolabilidade Absoluta da Capacidade de Peso
        if tot_weight > (capacity_kg + 0.001):
            errors.append(
                f"Invariante de peso violado: peso total ({tot_weight:.2f} kg) "
                f"excede a capacidade máxima do caminhão ({capacity_kg:.2f} kg)."
            )

        # 7. Inviolabilidade Absoluta da Capacidade de Volume
        if tot_volume > (capacity_m3 + 0.001):
            errors.append(
                f"Invariante de volume violado: volume total ({tot_volume:.4f} m³) "
                f"excede a capacidade cúbica máxima do caminhão ({capacity_m3:.4f} m³)."
            )

        is_valid = len(errors) == 0
        if not is_valid:
            logger.error(f"Validação independente REJEITOU plano de carga: {errors}")
        else:
            logger.info("Validação independente confirmou que o plano de carga respeita 100% dos invariantes.")

        return is_valid, errors
