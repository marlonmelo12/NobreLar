"""Módulo de limpeza de dados e geração de registros de auditoria (CleaningLog).

Implementa as regras canônicas obrigatórias de exclusão do desafio:
- Pedidos com retirada no balcão (Situacao_CSV_Entrega == 'RETIRADA')
- Pedidos cancelados (Logistica == 'CANCELADO' ou Situacao == 'Cancelado')
- Entregas locais urbanas em Crateús quando o escopo for expedição regional intermunicipal
"""

from typing import List, Dict, Any, Tuple
import structlog
from app.domain.models import CleaningLog

logger = structlog.get_logger()


class CleaningService:
    """Serviço responsável pela higienização e auditoria de registros brutos."""

    @staticmethod
    def evaluate_order(order_dict: Dict[str, Any], scope_regional: bool = True) -> Tuple[bool, List[CleaningLog]]:
        """Avalia se um pedido deve ser descartado segundo as regras do desafio.

        Retorna:
            (is_eligible, cleaning_logs)
        """
        logs: List[CleaningLog] = []
        raw_id = str(order_dict.get("Pedido", order_dict.get("id", "SEM_ID")))

        # 1. Regra de Balcão (Retirada direta pelo cliente na loja)
        sit_val = str(
            order_dict.get("situacao")
            or order_dict.get("SITUACAO")
            or order_dict.get("Situacao_CSV_Entrega")
            or ""
        ).strip().upper()

        if sit_val == "RETIRADA":
            logs.append(CleaningLog(
                record_reference=raw_id,
                rule_applied="retirada_balcao",
                action="REMOVIDO",
                field="situacao",
                original_value=sit_val,
                corrected_value=None,
                reason="Regra de negócio: pedidos com retirada no balcão não compõem carga de transporte rodoviário.",
            ))
            return False, logs

        # 2. Regra de Cancelamento
        logistica = str(order_dict.get("Logistica", order_dict.get("logistica", ""))).strip().upper()
        situacao_cadastral = str(order_dict.get("Situacao", "")).strip().upper()
        if logistica == "CANCELADO" or situacao_cadastral == "CANCELADO" or sit_val == "CANCELADO":
            logs.append(CleaningLog(
                record_reference=raw_id,
                rule_applied="pedido_cancelado",
                action="REMOVIDO",
                field="situacao",
                original_value=f"Logistica={logistica}|Situacao={sit_val or situacao_cadastral}",
                corrected_value=None,
                reason="Regra de negócio: pedidos cancelados são expurgados do planejamento de carregamento.",
            ))
            return False, logs

        # 3. Regra de Entregas em Crateús (quando em planejamento de eixos regionais externos)
        cidade = str(order_dict.get("Cidade", "")).strip().upper()
        if scope_regional and cidade == "CRATEUS":
            logs.append(CleaningLog(
                record_reference=raw_id,
                rule_applied="entrega_local_crateus",
                action="REMOVIDO",
                field="Cidade",
                original_value=cidade,
                corrected_value=None,
                reason="Regra do desafio: entregas locais em Crateús pertencem à logística urbana e não aos 5 eixos regionais.",
            ))
            return False, logs

        return True, logs
