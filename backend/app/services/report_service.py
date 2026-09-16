"""Módulo de geração de Relatórios Operacionais em HTML e PDF para a Expedição e Entregas.

Implementa os dois documentos canônicos obrigatórios:
1. Mapa de Carregamento de Doca (Ordem LIFO / Estivagem no Veículo):
   - Focado na equipe de doca, expedição e estivadores do CD Crateús.
   - Ordenado estritamente por ordem de carregamento na doca (LIFO: 1º carregado vai ao fundo).
   - Contém pesos, volumes, alertas de peças de 6m e checklist de conferência física.

2. Roteiro de Entregas Otimizado (Sequência do Caixeiro Viajante - TSP):
   - Focado no motorista e ajudante de rota em trânsito rodoviário.
   - Ordenado estritamente pela sequência cronológica de paradas calculadas pelo algoritmo TSP.
   - Contém endereços completos, distâncias acumuladas, alertas de cobrança no destino ('A RECEBER')
     e canhotos de assinatura/comprovante de recebimento por cliente.
"""

import io
from typing import Dict, Any, List
from jinja2 import Template
import structlog
from xhtml2pdf import pisa

logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# 1. TEMPLATE: MAPA DE CARREGAMENTO DE DOCA (LIFO)
# ---------------------------------------------------------------------------
LOADING_SHEET_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Mapa de Carregamento de Doca - NobreLOG IA</title>
<style>
    @page {
        size: A4 portrait;
        margin: 12mm 10mm 12mm 10mm;
    }
    body {
        font-family: Helvetica, Arial, sans-serif;
        color: #1e293b;
        font-size: 9pt;
        line-height: 1.3;
    }
    .header {
        border-bottom: 2.5px solid #1e3a8a;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .title {
        font-size: 15pt;
        font-weight: bold;
        color: #1e3a8a;
        margin: 0;
    }
    .subtitle {
        font-size: 9pt;
        color: #64748b;
        margin: 2px 0 0 0;
        font-weight: bold;
    }
    .meta-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 6px 8px;
        margin-bottom: 10px;
    }
    .meta-table {
        width: 100%;
        border-collapse: collapse;
    }
    .meta-table td {
        padding: 2px 4px;
        font-size: 8.5pt;
    }
    .meta-label {
        font-weight: bold;
        color: #334155;
    }
    .alert-banner {
        background-color: #fef3c7;
        border: 1.5px solid #d97706;
        color: #92400e;
        padding: 5px 8px;
        border-radius: 4px;
        font-size: 8.5pt;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .orders-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
    }
    .orders-table th {
        background-color: #1e3a8a;
        color: #ffffff;
        font-size: 8pt;
        padding: 5px 4px;
        text-align: left;
        border: 1px solid #1e3a8a;
    }
    .orders-table td {
        font-size: 8pt;
        padding: 4px;
        border: 1px solid #cbd5e1;
    }
    .orders-table tr:nth-child(even) {
        background-color: #f8fafc;
    }
    .badge-lifo {
        background-color: #0284c7;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 7.5pt;
    }
    .badge-fundo {
        background-color: #0f172a;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 7.5pt;
    }
    .badge-porta {
        background-color: #059669;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 5px;
        border-radius: 3px;
        font-size: 7.5pt;
    }
    .badge-long {
        background-color: #b45309;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 7pt;
    }
    .badge-urgente {
        background-color: #dc2626;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 7pt;
    }
    .check-box {
        font-size: 11pt;
        text-align: center;
        color: #475569;
    }
    .signatures {
        margin-top: 25px;
        width: 100%;
    }
    .signature-box {
        width: 46%;
        border-top: 1.2px solid #334155;
        text-align: center;
        padding-top: 4px;
        font-size: 8pt;
        color: #1e293b;
    }
    .footer {
        margin-top: 15px;
        font-size: 7.5pt;
        color: #94a3b8;
        text-align: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 4px;
    }
</style>
</head>
<body>

<div class="header">
    <table style="width: 100%;">
        <tr>
            <td>
                <div class="title">NOBRE LAR HOME CENTER — EXPEDIÇÃO</div>
                <div class="subtitle">MAPA DE CARREGAMENTO DE DOCA (ESTIVAGEM LIFO) — Romaneio Oficial de Carga</div>
            </td>
            <td style="text-align: right; font-size: 8pt;">
                <strong>Identificador:</strong> {{ plan.execution_id or plan.trip_id }}<br>
                <strong>Emissão:</strong> {{ plan.created_at }}
            </td>
        </tr>
    </table>
</div>

<div class="meta-box">
    <table class="meta-table">
        <tr>
            <td style="width: 35%;"><span class="meta-label">Eixo Rodoviário:</span> {{ plan.axis_name }}</td>
            <td style="width: 40%;"><span class="meta-label">Veículo:</span> {{ plan.vehicle_name }}</td>
            <td style="width: 25%;"><span class="meta-label">Placa:</span> <strong>{{ plan.vehicle_plate }}</strong></td>
        </tr>
        <tr>
            <td><span class="meta-label">Total Pedidos:</span> {{ plan.total_orders }}</td>
            <td><span class="meta-label">Faturamento Carga:</span> R$ {{ "%.2f"|format(plan.total_value) }}</td>
            <td><span class="meta-label">Limitante:</span> <strong>{{ plan.limiting_resource or 'PESO' }}</strong></td>
        </tr>
        <tr>
            <td><span class="meta-label">Ocupação Peso:</span> {{ "%.1f"|format(plan.total_weight_kg) }} kg (<strong>{{ "%.1f"|format(plan.weight_occupancy) }}%</strong>)</td>
            <td colspan="2"><span class="meta-label">Ocupação Volume:</span> {{ "%.3f"|format(plan.total_volume_m3) }} m³ (<strong>{{ "%.1f"|format(plan.volume_occupancy) }}%</strong>)</td>
        </tr>
    </table>
</div>

{% if plan.has_long_items %}
<div class="alert-banner">
    [AVISO] ATENÇÃO EXPEDIÇÃO: CARGA COM TUBOS/BARRAS DE 6 METROS — ACOMODAR NO SUPORTE OU ASSOALHO LATERAL
</div>
{% endif %}

<div style="margin-bottom: 6px; font-size: 8pt; color: #475569;">
    <strong>Regra de Estivagem (LIFO):</strong> Os pedidos devem ser colocados no caminhão rigorosamente na ordem abaixo (o 1º a carregar fica no fundo do baú; o último fica próximo à porta para a 1ª entrega).
</div>

<table class="orders-table">
    <thead>
        <tr>
            <th style="width: 14%; text-align: center;">Ordem Doca (LIFO)</th>
            <th style="width: 10%; text-align: center;">Descarga</th>
            <th style="width: 14%;">Pedido</th>
            <th style="width: 18%;">Cidade / Distrito</th>
            <th style="width: 11%; text-align: right;">Peso (kg)</th>
            <th style="width: 10%; text-align: right;">Volume (m³)</th>
            <th style="width: 16%; text-align: center;">Alertas de Estiva</th>
            <th style="width: 7%; text-align: center;">Conf.</th>
        </tr>
    </thead>
    <tbody>
        {% for it in plan['loading_items'] %}
        <tr>
            <td style="text-align: center;">
                {% if loop.first %}
                <span class="badge-fundo">1º (FUNDO)</span>
                {% elif loop.last %}
                <span class="badge-porta">{{ it.loading_order }}º (PORTA)</span>
                {% else %}
                <span class="badge-lifo">{{ it.loading_order }}º Carregar</span>
                {% endif %}
            </td>
            <td style="text-align: center; font-weight: bold;">{{ it.delivery_order }}ª Parada</td>
            <td><strong>{{ it.external_id or it.order_id or it.id }}</strong></td>
            <td>{{ it.city_name }}</td>
            <td style="text-align: right;">{{ "%.1f"|format(it.weight_kg or it.total_weight_kg or 0.0) }}</td>
            <td style="text-align: right;">{{ "%.3f"|format(it.volume_m3 or it.total_volume_m3 or 0.0) }}</td>
            <td style="text-align: center;">
                {% if it.has_long_items %}
                <span class="badge-long">6 METROS</span>
                {% endif %}
                {% if it.is_mandatory or it.is_urgent %}
                <span class="badge-urgente">URGENTE</span>
                {% endif %}
                {% if not it.has_long_items and not (it.is_mandatory or it.is_urgent) %}
                <span style="font-size: 7.5pt; color: #64748b;">Padrão</span>
                {% endif %}
            </td>
            <td class="check-box">[ &nbsp; ]</td>
        </tr>
        {% endfor %}
        <tr style="background-color: #f1f5f9; font-weight: bold;">
            <td colspan="4" style="text-align: right;">TOTAIS DA CARGA:</td>
            <td style="text-align: right;">{{ "%.1f"|format(plan.total_weight_kg) }} kg</td>
            <td style="text-align: right;">{{ "%.3f"|format(plan.total_volume_m3) }} m³</td>
            <td colspan="2" style="text-align: center;">{{ plan.total_orders }} Pedidos</td>
        </tr>
    </tbody>
</table>

<table class="signatures">
    <tr>
        <td class="signature-box">
            <strong>Conferente de Expedição / Doca</strong><br>
            Carga conferida, pesada e estivada conforme a ordem física
        </td>
        <td style="width: 8%;"></td>
        <td class="signature-box">
            <strong>Motorista do Veículo</strong><br>
            Recebi os volumes lacrados e conferidos para transporte
        </td>
    </tr>
</table>

<div class="footer">
    NobreLOG IA — Otimizador de Carga por Eixo | CD Crateús - CE | Documento Operacional de Pátio
</div>

</body>
</html>
"""

# ---------------------------------------------------------------------------
# 2. TEMPLATE: ROTEIRO DE ENTREGAS OTIMIZADO (CAIXEIRO VIAJANTE - TSP)
# ---------------------------------------------------------------------------
DELIVERY_ROUTE_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Roteiro de Entregas TSP - NobreLOG IA</title>
<style>
    @page {
        size: A4 portrait;
        margin: 12mm 10mm 12mm 10mm;
    }
    body {
        font-family: Helvetica, Arial, sans-serif;
        color: #1e293b;
        font-size: 8.5pt;
        line-height: 1.3;
    }
    .header {
        border-bottom: 2.5px solid #047857;
        padding-bottom: 6px;
        margin-bottom: 10px;
    }
    .title {
        font-size: 15pt;
        font-weight: bold;
        color: #047857;
        margin: 0;
    }
    .subtitle {
        font-size: 9pt;
        color: #64748b;
        margin: 2px 0 0 0;
        font-weight: bold;
    }
    .meta-box {
        background-color: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 4px;
        padding: 6px 8px;
        margin-bottom: 10px;
    }
    .meta-table {
        width: 100%;
        border-collapse: collapse;
    }
    .meta-table td {
        padding: 2px 4px;
        font-size: 8.5pt;
    }
    .meta-label {
        font-weight: bold;
        color: #334155;
    }
    .alert-cash {
        background-color: #fee2e2;
        border: 1.5px solid #dc2626;
        color: #991b1b;
        padding: 5px 8px;
        border-radius: 4px;
        font-size: 8.5pt;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .route-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 12px;
    }
    .route-table th {
        background-color: #047857;
        color: #ffffff;
        font-size: 8pt;
        padding: 5px 4px;
        text-align: left;
        border: 1px solid #047857;
    }
    .route-table td {
        font-size: 8pt;
        padding: 5px 4px;
        border: 1px solid #cbd5e1;
        vertical-align: top;
    }
    .route-table tr:nth-child(even) {
        background-color: #f8fafc;
    }
    .badge-parada {
        background-color: #047857;
        color: #ffffff;
        font-weight: bold;
        padding: 3px 6px;
        border-radius: 3px;
        font-size: 8pt;
        display: inline-block;
    }
    .badge-receber {
        background-color: #dc2626;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 7pt;
    }
    .badge-pago {
        background-color: #16a34a;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 7pt;
    }
    .stub-box {
        font-size: 7pt;
        color: #475569;
        border-top: 1px dashed #94a3b8;
        padding-top: 3px;
        margin-top: 3px;
    }
    .footer {
        margin-top: 10px;
        font-size: 7.5pt;
        color: #94a3b8;
        text-align: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 4px;
    }
</style>
</head>
<body>

<div class="header">
    <table style="width: 100%;">
        <tr>
            <td>
                <div class="title">NOBRE LAR HOME CENTER — TRANSPORTE</div>
                <div class="subtitle">ROTEIRO DE ENTREGAS OTIMIZADO (ALGORITMO DO CAIXEIRO VIAJANTE - TSP)</div>
            </td>
            <td style="text-align: right; font-size: 8pt;">
                <strong>Viagem:</strong> {{ plan.execution_id or plan.trip_id }}<br>
                <strong>Emissão:</strong> {{ plan.created_at }}
            </td>
        </tr>
    </table>
</div>

<div class="meta-box">
    <table class="meta-table">
        <tr>
            <td style="width: 35%;"><span class="meta-label">Eixo Rodoviário:</span> {{ plan.axis_name }}</td>
            <td style="width: 40%;"><span class="meta-label">Veículo:</span> {{ plan.vehicle_name }}</td>
            <td style="width: 25%;"><span class="meta-label">Placa:</span> <strong>{{ plan.vehicle_plate }}</strong></td>
        </tr>
        <tr>
            <td><span class="meta-label">Total de Paradas:</span> {{ plan.total_orders }} entregas</td>
            <td><span class="meta-label">Distância Prevista:</span> <strong>{{ "%.1f"|format(plan.estimated_tortuosity_distance_km or 0.0) }} km</strong> (Ida/Volta CD)</td>
            <td><span class="meta-label">Faturamento Carga:</span> R$ {{ "%.2f"|format(plan.total_value) }}</td>
        </tr>
        <tr>
            <td><span class="meta-label">A Cobrar na Rota:</span> <strong style="color: #dc2626;">R$ {{ "%.2f"|format(plan.total_cash_to_collect or 0.0) }}</strong></td>
            <td colspan="2"><span class="meta-label">Peso Total Carga:</span> {{ "%.1f"|format(plan.total_weight_kg) }} kg | Volume: {{ "%.3f"|format(plan.total_volume_m3) }} m³</td>
        </tr>
    </table>
</div>

{% if plan.has_cash_collection %}
<div class="alert-cash">
    [AVISO] ATENÇÃO MOTORISTA: ESTA CARGA POSSUI PEDIDOS COM PAGAMENTO NO ATO DA ENTREGA (TOTAL A COBRAR: R$ {{ "%.2f"|format(plan.total_cash_to_collect) }}). EXIJA COMPROVANTE ANTES DO DESCARREGAMENTO!
</div>
{% endif %}

<table class="route-table">
    <thead>
        <tr>
            <th style="width: 9%; text-align: center;">Parada</th>
            <th style="width: 14%;">Pedido / Ref.</th>
            <th style="width: 18%;">Cidade / Distrito</th>
            <th style="width: 28%;">Endereço de Entrega</th>
            <th style="width: 13%; text-align: right;">Valor / Cobrança</th>
            <th style="width: 18%;">Comprovante de Recebimento</th>
        </tr>
    </thead>
    <tbody>
        {% for it in plan['delivery_items'] %}
        <tr>
            <td style="text-align: center;">
                <span class="badge-parada">{{ it.delivery_order }}ª</span><br>
                <span style="font-size: 6.5pt; color: #64748b;">(Doca {{ it.loading_order }}º)</span>
            </td>
            <td>
                <strong>{{ it.external_id or it.order_id or it.id }}</strong><br>
                <span style="font-size: 7pt; color: #64748b;">{{ "%.1f"|format(it.weight_kg or it.total_weight_kg or 0.0) }} kg | {{ "%.3f"|format(it.volume_m3 or it.total_volume_m3 or 0.0) }} m³</span>
            </td>
            <td><strong>{{ it.city_name }}</strong></td>
            <td>{{ it.address_line or it.formatted_address or it.city_name }}</td>
            <td style="text-align: right;">
                R$ {{ "%.2f"|format(it.value or it.total_value or 0.0) }}<br>
                {% if it.payment_on_delivery in ["A RECEBER", "SIM", "RECEBER"] %}
                <span class="badge-receber">A RECEBER</span>
                <div style="font-size: 6.5pt; color: #dc2626; margin-top: 2px;">
                    Cód. PIX/Recibo: ______
                </div>
                {% else %}
                <span class="badge-pago">QUITADO</span>
                {% endif %}
            </td>
            <td>
                <div class="stub-box">
                    Assinatura Cliente:<br>
                    ___________________________<br>
                    Nome/RG: ___________________
                </div>
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<div class="footer">
    Sequência avaliada e otimizada pelo Algoritmo do Caixeiro Viajante (TSP) com matriz de distâncias e tortuosidade rodoviária (1,28) a partir do CD Crateús | NobreLOG IA
</div>

</body>
</html>
"""


class ReportService:
    """Serviço de geração e renderização de relatórios operacionais em HTML e PDF."""

    @staticmethod
    def _normalize_plan_data(data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza campos para compatibilidade tanto com LoadPlan quanto com Trip do pipeline."""
        norm = dict(data)
        items = norm.get("items", [])

        # Garante lista ordenada para doca (loading_order crescente)
        loading_items = sorted(items, key=lambda x: x.get("loading_order", 1))
        # Garante lista ordenada para entregas TSP (delivery_order crescente)
        delivery_items = sorted(items, key=lambda x: x.get("delivery_order", 1))

        norm["loading_items"] = loading_items
        norm["delivery_items"] = delivery_items

        # Total de cobrança em dinheiro/PIX na entrega
        total_cash = 0.0
        has_long = False
        for it in items:
            pgt = str(it.get("payment_on_delivery", "")).upper()
            if pgt in ("A RECEBER", "SIM", "RECEBER"):
                total_cash += float(it.get("value", it.get("total_value", 0.0)))
            if it.get("has_long_items", False):
                has_long = True

        norm["total_cash_to_collect"] = total_cash
        norm["has_cash_collection"] = total_cash > 0.0
        norm["has_long_items"] = has_long or norm.get("has_long_items", False)

        # Percentuais de ocupação
        if "weight_occupancy" not in norm and "weight_occupancy_pct" in norm:
            norm["weight_occupancy"] = norm["weight_occupancy_pct"]
        if "volume_occupancy" not in norm and "volume_occupancy_pct" in norm:
            norm["volume_occupancy"] = norm["volume_occupancy_pct"]

        if "created_at" not in norm:
            from datetime import datetime
            norm["created_at"] = datetime.now().strftime("%d/%m/%Y %H:%M")

        return norm

    # -----------------------------------------------------------------------
    # Documento 1: Mapa de Carregamento de Doca (LIFO)
    # -----------------------------------------------------------------------
    @classmethod
    def render_loading_sheet_html(cls, plan_data: Dict[str, Any]) -> str:
        """Gera o HTML do Mapa de Carregamento de Doca (Ordem LIFO)."""
        norm_data = cls._normalize_plan_data(plan_data)
        template = Template(LOADING_SHEET_HTML_TEMPLATE)
        return template.render(plan=norm_data)

    @classmethod
    def generate_loading_sheet_pdf(cls, plan_data: Dict[str, Any]) -> bytes:
        """Gera o arquivo binário PDF do Mapa de Carregamento de Doca (LIFO)."""
        html_content = cls.render_loading_sheet_html(plan_data)
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

        if pisa_status.err:
            logger.error("Erro ao gerar PDF de Carregamento de Doca com xhtml2pdf.")
            raise RuntimeError("Falha na geração do PDF de carregamento de doca.")

        return pdf_buffer.getvalue()

    # -----------------------------------------------------------------------
    # Documento 2: Roteiro de Entregas Otimizado (TSP)
    # -----------------------------------------------------------------------
    @classmethod
    def render_delivery_route_html(cls, plan_data: Dict[str, Any]) -> str:
        """Gera o HTML do Roteiro de Entregas Otimizado (Caixeiro Viajante - TSP)."""
        norm_data = cls._normalize_plan_data(plan_data)
        template = Template(DELIVERY_ROUTE_HTML_TEMPLATE)
        return template.render(plan=norm_data)

    @classmethod
    def generate_delivery_route_pdf(cls, plan_data: Dict[str, Any]) -> bytes:
        """Gera o arquivo binário PDF do Roteiro de Entregas Otimizado (TSP)."""
        html_content = cls.render_delivery_route_html(plan_data)
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

        if pisa_status.err:
            logger.error("Erro ao gerar PDF do Roteiro de Entregas TSP com xhtml2pdf.")
            raise RuntimeError("Falha na geração do PDF do roteiro de entregas TSP.")

        return pdf_buffer.getvalue()

    # -----------------------------------------------------------------------
    # Retrocompatibilidade
    # -----------------------------------------------------------------------
    @classmethod
    def render_manifest_html(cls, plan_data: Dict[str, Any]) -> str:
        """Renderiza o romaneio unificado (retrocompatível)."""
        return cls.render_loading_sheet_html(plan_data)

    @classmethod
    def generate_manifest_pdf(cls, plan_data: Dict[str, Any]) -> bytes:
        """Gera o PDF do romaneio unificado (retrocompatível)."""
        return cls.generate_loading_sheet_pdf(plan_data)
