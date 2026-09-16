"""Módulo de geração de Romaneio de Carga para Expedição em HTML e PDF.

Implementa os requisitos RF-014 e Seção 17:
- Cabeçalho com identificação do plano, veículo, motorista, eixo e data
- Tabela de pedidos ordenada pela sequência de descarga
- Indicação explícita da sequência inversa LIFO para estivagem na doca
- Tarja destacada para pedidos com cobrança na entrega ('A RECEBER')
- Percentual de cubagem estimada como indicador de confiabilidade
- Campos oficiais de assinatura do conferente e do motorista
"""

import io
from typing import Dict, Any
from jinja2 import Template
import structlog
from xhtml2pdf import pisa

logger = structlog.get_logger()

ROMANEIO_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<title>Romaneio de Carga - NobreLOG IA</title>
<style>
    @page {
        size: A4 portrait;
        margin: 15mm 10mm 15mm 10mm;
    }
    body {
        font-family: Helvetica, Arial, sans-serif;
        color: #333333;
        font-size: 10pt;
        line-height: 1.3;
    }
    .header {
        border-bottom: 2px solid #1e3a8a;
        padding-bottom: 8px;
        margin-bottom: 12px;
    }
    .title {
        font-size: 16pt;
        font-weight: bold;
        color: #1e3a8a;
        margin: 0;
    }
    .subtitle {
        font-size: 10pt;
        color: #64748b;
        margin: 2px 0 0 0;
    }
    .meta-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 4px;
        padding: 8px;
        margin-bottom: 12px;
    }
    .meta-table {
        width: 100%;
        border-collapse: collapse;
    }
    .meta-table td {
        padding: 3px 6px;
        font-size: 9pt;
    }
    .meta-label {
        font-weight: bold;
        color: #475569;
    }
    .orders-table {
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 15px;
    }
    .orders-table th {
        background-color: #1e3a8a;
        color: #ffffff;
        font-size: 9pt;
        padding: 5px;
        text-align: left;
        border: 1px solid #1e3a8a;
    }
    .orders-table td {
        font-size: 8.5pt;
        padding: 5px;
        border: 1px solid #cbd5e1;
    }
    .orders-table tr:nth-child(even) {
        background-color: #f8fafc;
    }
    .badge-receber {
        background-color: #dc2626;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 7.5pt;
        display: inline-block;
    }
    .badge-lifo {
        background-color: #0284c7;
        color: #ffffff;
        font-weight: bold;
        padding: 2px 4px;
        border-radius: 3px;
        font-size: 8pt;
    }
    .signatures {
        margin-top: 30px;
        width: 100%;
    }
    .signature-box {
        width: 45%;
        border-top: 1px solid #333333;
        text-align: center;
        padding-top: 5px;
        font-size: 9pt;
    }
    .footer {
        margin-top: 15px;
        font-size: 8pt;
        color: #94a3b8;
        text-align: center;
        border-top: 1px solid #e2e8f0;
        padding-top: 5px;
    }
</style>
</head>
<body>

<div class="header">
    <table style="width: 100%;">
        <tr>
            <td>
                <div class="title">NOBRE LAR HOME CENTER — EXPEDIÇÃO</div>
                <div class="subtitle">Romaneio Oficial de Carga e Sequência de Descarga (NobreLOG IA)</div>
            </td>
            <td style="text-align: right;">
                <strong>Execução:</strong> {{ plan.execution_id }}<br>
                <span style="font-size: 8.5pt; color: #64748b;">{{ plan.created_at }}</span>
            </td>
        </tr>
    </table>
</div>

<div class="meta-box">
    <table class="meta-table">
        <tr>
            <td><span class="meta-label">Eixo Rodoviário:</span> {{ plan.axis_name }}</td>
            <td><span class="meta-label">Veículo:</span> {{ plan.vehicle_name }} (Placa: {{ plan.vehicle_plate }})</td>
            <td><span class="meta-label">Perfil Utilizado:</span> {{ plan.profile_name }}</td>
        </tr>
        <tr>
            <td><span class="meta-label">Qtd. Pedidos:</span> {{ plan.total_orders }}</td>
            <td><span class="meta-label">Valor Total:</span> R$ {{ "%.2f"|format(plan.total_value) }}</td>
            <td><span class="meta-label">Limitante:</span> <strong>{{ plan.limiting_resource }}</strong></td>
        </tr>
        <tr>
            <td><span class="meta-label">Ocupação Peso:</span> {{ "%.2f"|format(plan.total_weight_kg) }} kg ({{ "%.1f"|format(plan.weight_occupancy) }}%)</td>
            <td><span class="meta-label">Ocupação Volume:</span> {{ "%.4f"|format(plan.total_volume_m3) }} m³ ({{ "%.1f"|format(plan.volume_occupancy) }}%)</td>
            <td><span class="meta-label">Cubagem Estimada:</span> {{ "%.1f"|format(plan.estimated_cubing_pct) }}% do total</td>
        </tr>
    </table>
</div>

<h3 style="font-size: 11pt; color: #1e3a8a; margin: 10px 0 5px 0;">Sequência de Entregas e Estivagem na Doca (LIFO)</h3>
<p style="font-size: 8pt; color: #64748b; margin: 0 0 8px 0;">
    * <strong>Ordem Doca (LIFO):</strong> A primeira mercadoria carregada (fundo do caminhão) é a última a ser descarregada.
</p>

<table class="orders-table">
    <thead>
        <tr>
            <th style="width: 8%; text-align: center;">Descarga</th>
            <th style="width: 8%; text-align: center;">Doca (LIFO)</th>
            <th style="width: 14%;">Pedido</th>
            <th style="width: 18%;">Cidade / Distrito</th>
            <th style="width: 26%;">Endereço de Entrega</th>
            <th style="width: 10%; text-align: right;">Peso (kg)</th>
            <th style="width: 10%; text-align: right;">Volume (m³)</th>
            <th style="width: 12%; text-align: right;">Valor (R$)</th>
            <th style="width: 12%; text-align: center;">Cobrança</th>
        </tr>
    </thead>
    <tbody>
        {% for it in plan['items'] %}
        <tr>
            <td style="text-align: center; font-weight: bold;">{{ it.delivery_order }}º</td>
            <td style="text-align: center;"><span class="badge-lifo">{{ it.loading_order }}º</span></td>
            <td><strong>{{ it.order_id }}</strong></td>
            <td>{{ it.city_name }}</td>
            <td>{{ it.address_line or it.city_name }}</td>
            <td style="text-align: right;">{{ "%.1f"|format(it.weight_kg) }}</td>
            <td style="text-align: right;">{{ "%.3f"|format(it.volume_m3) }}</td>
            <td style="text-align: right;">{{ "%.2f"|format(it.value) }}</td>
            <td style="text-align: center;">
                {% if it.payment_on_delivery == "A RECEBER" %}
                <span class="badge-receber">A RECEBER</span>
                {% else %}
                <span style="font-size: 7.5pt; color: #15803d; font-weight: bold;">FATURADO</span>
                {% endif %}
            </td>
        </tr>
        {% endfor %}
    </tbody>
</table>

<table class="signatures">
    <tr>
        <td class="signature-box">
            <strong>Conferente / Expedidor Responsável</strong><br>
            Nobre Lar CD Crateús
        </td>
        <td style="width: 10%;"></td>
        <td class="signature-box">
            <strong>Motorista Responsável</strong><br>
            Recebi a carga conferida e lacrada
        </td>
    </tr>
</table>

<div class="footer">
    Plano gerado pelo motor de otimização combinatória NobreLOG IA — Versão {{ plan.algorithm_version }} | Solver: {{ plan.solver_status }} ({{ plan.solve_duration_ms }} ms)
</div>

</body>
</html>
"""


class ReportService:
    """Serviço de geração e renderização de romaneios e relatórios."""

    @staticmethod
    def render_manifest_html(plan_data: Dict[str, Any]) -> str:
        """Gera o HTML final do romaneio a partir dos dados do plano de carga."""
        template = Template(ROMANEIO_HTML_TEMPLATE)
        return template.render(plan=plan_data)

    @staticmethod
    def generate_manifest_pdf(plan_data: Dict[str, Any]) -> bytes:
        """Renderiza o romaneio em arquivo PDF binário utilizando xhtml2pdf."""
        html_content = ReportService.render_manifest_html(plan_data)
        pdf_buffer = io.BytesIO()
        pisa_status = pisa.CreatePDF(html_content, dest=pdf_buffer)

        if pisa_status.err:
            logger.error("Erro ao gerar PDF com xhtml2pdf.")
            raise RuntimeError("Falha na geração do PDF do romaneio.")

        return pdf_buffer.getvalue()
