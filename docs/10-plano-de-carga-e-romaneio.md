# 10. Plano de Carga, Romaneio e Gestão de Recebíveis

---

## 1. O Romaneio Operacional de Carga

O Romaneio de Carga é o documento físico e digital de fé pública operacional que acompanha o motorista durante toda a rota de entrega. Ele sintetiza os pedidos selecionados pelo otimizador e estabelece a conferência de embarque e descarga.

### Elementos Estruturais Obrigatórios do Romaneio:
1. **Cabeçalho Institucional:** Logo do Grupo Nobre Lar, ID de execução, Eixo Rodoviário, Placa do Veículo e Nome do Motorista.
2. **Painel de Ocupação:** Percentual de Peso (\(98,3\%\)), Percentual de Volume (\(76,8\%\)) e Indicador de Confiança de Cubagem (\(95,9\%\) de dados auditados).
3. **Alerta de Cobrança no Destino (`A RECEBER`):**
   - Tarja vermelha destacada: **ATENÇÃO: RECEBIMENTO NO DESTINO**.
   - Lista explícita de clientes que pagarão na entrega (dinheiro/PIX), com campo para o motorista anotar o código de autenticação do comprovante.
4. **Sequência LIFO de Descarregamento:** Pedidos dispostos em tabelas ordenadas por cidade conforme a rota.
5. **Assinaturas Formais:** Campos para assinatura do Conferente de Pátio, Motorista e Recebedor em cada entrega.

---

## 2. Geração do Documento PDF via WeasyPrint

O backend utiliza **WeasyPrint** renderizando uma página HTML com estilização CSS `@page` otimizada para folhas A4:

```html
<div class="header">
  <h2>NOBRE LAR HOME CENTER — ROMANEIO DE EXPEDIÇÃO</h2>
  <p>Eixo: <strong>Ipaporanga / Poranga</strong> | Veículo: <strong>Accelo 815</strong></p>
</div>

<!-- Tarja de Recebíveis -->
{% if has_cash_collection %}
<div class="alert-box">
  ⚠️ ATENÇÃO MOTORISTA: ESTA CARGA CONTÉM PEDIDOS COM PAGAMENTO NO DESTINO (TOTAL A COBRAR: R$ {{ total_cash }})
</div>
{% endif %}
```
