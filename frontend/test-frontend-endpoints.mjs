/**
 * Teste Automatizado dos Endpoints Integrados ao Frontend — NobreLOG IA
 * Executa todas as chamadas que o frontend consome e valida os contratos e payloads.
 */

const API_BASE = process.env.VITE_API_URL || 'http://localhost:8000';

async function runTests() {
  console.log(`\n============================================================`);
  console.log(` INICIANDO TESTES DOS ENDPOINTS DO FRONTEND (${API_BASE})`);
  console.log(`============================================================\n`);

  let passed = 0;
  let failed = 0;

  async function test(name, fn) {
    try {
      process.stdout.write(`• ${name}... `);
      await fn();
      console.log(`\x1b[32m[PASS]\x1b[0m`);
      passed++;
    } catch (err) {
      console.log(`\x1b[31m[FAIL]\x1b[0m`);
      console.error(`  Erro: ${err.message}`);
      failed++;
    }
  }

  // 1. Health Check
  await test('1. GET /api/v1/health (Saúde da API)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/health`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (data.status.toLowerCase() !== 'healthy') throw new Error(`Status inesperado: ${data.status}`);
  });

  // 2. Pedidos Estruturados
  const testOrders = [
    {
      id: "L12608361",
      data: "16/09/2026",
      cliente: "Cliente Teste Nobre Lar 1",
      cidade: "CRATEUS",
      endereco: "Rua Dom Pedro II, 450, Centro",
      valor: 810.00,
      urgente: false,
      situacao: "NORMAL",
      itens: [
        { codigo: "23717", descricao: "TUBO PVC ESGOTO 100MM", quantidade: 5.0, unidade: "MT", preco_unitario: 35.0 },
        { codigo: "21243", descricao: "PISO CERBRAS IPANEMA BEGE 46 X 46 A", quantidade: 25.30, unidade: "MT", preco_unitario: 20.0 },
        { codigo: "1001", descricao: "CIMENTO POTY TODAS AS OBRAS 50KG", quantidade: 10.0, unidade: "SC", preco_unitario: 36.0 }
      ]
    },
    {
      id: "L12608362",
      data: "16/09/2026",
      cliente: "Cliente Urgente Norte",
      cidade: "IPAPORANGA",
      endereco: "Av. Central, 120",
      valor: 1200.00,
      urgente: true,
      situacao: "URGENTE",
      itens: [
        { codigo: "1001", descricao: "CIMENTO POTY TODAS AS OBRAS 50KG", quantidade: 20.0, unidade: "SC", preco_unitario: 36.0 }
      ]
    },
    {
      id: "L12608998",
      data: "16/09/2026",
      cliente: "Cliente Balcao",
      cidade: "CRATEUS",
      endereco: "Balcão Loja",
      valor: 150.00,
      urgente: false,
      situacao: "RETIRADA",
      itens: [
        { codigo: "500", descricao: "FITA ISOLANTE 20M", quantidade: 2.0, unidade: "UN", preco_unitario: 10.0 }
      ]
    },
    {
      id: "L12608999",
      data: "16/09/2026",
      cliente: "Cliente Desistente",
      cidade: "CRATEUS",
      endereco: "Rua B, 20",
      valor: 300.00,
      urgente: false,
      situacao: "CANCELADO",
      itens: [
        { codigo: "600", descricao: "TINTA ACRILICA 18L", quantidade: 1.0, unidade: "LT", preco_unitario: 300.0 }
      ]
    }
  ];

  // 3. Submissão POST Único de Pedidos
  let dispatchResult = null;
  await test('2. POST /api/v1/dispatch/orders (Processamento Desacoplado)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/dispatch/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pedidos: testOrders,
        perfil_otimizacao: 'Equilibrado',
        tempo_limite_segundos: 20.0
      })
    });
    if (!res.ok) throw new Error(`Status ${res.status}`);
    dispatchResult = await res.json();
    if (dispatchResult.status !== 'SUCESSO') throw new Error(`Status ${dispatchResult.status}`);
    if (!dispatchResult.resumo || !dispatchResult.cargas_caminhao || !dispatchResult.roteiros_entrega) {
      throw new Error(`Campos obrigatórios ausentes na resposta`);
    }
  });

  // 4. GET Cargas no Caminhão
  await test('3. GET /api/v1/dispatch/truck-load (Tela 1: Carroceria Aberta + Drilldown)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/dispatch/truck-load`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (data.status !== 'SUCESSO') throw new Error(`Status ${data.status}`);
    if (!Array.isArray(data.viagens) || data.viagens.length === 0) {
      throw new Error(`Nenhuma viagem retornada`);
    }
    const viagem1 = data.viagens[0];
    if (viagem1.veiculo.tipo_carroceria !== 'Carroceria Aberta (Grade Baixa)') {
      throw new Error(`Tipo de carroceria incorreto: ${viagem1.veiculo.tipo_carroceria}`);
    }
    if (!Array.isArray(viagem1.pedidos_carroceria) || viagem1.pedidos_carroceria.length === 0) {
      throw new Error(`Sem pedidos na carroceria`);
    }
    const primeiroPedido = viagem1.pedidos_carroceria[0];
    if (!Array.isArray(primeiroPedido.itens) || primeiroPedido.itens.length === 0) {
      throw new Error(`Drilldown de itens ausente no pedido`);
    }
  });

  // 5. GET Roteiros de Entrega TSP
  await test('4. GET /api/v1/dispatch/delivery-route (Tela 2: Roteiros TSP + Cobrança)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/dispatch/delivery-route`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (data.status !== 'SUCESSO') throw new Error(`Status ${data.status}`);
    if (!Array.isArray(data.viagens) || data.viagens.length === 0) {
      throw new Error(`Nenhuma rota retornada`);
    }
    const rota1 = data.viagens[0];
    if (!Array.isArray(rota1.paradas) || rota1.paradas.length === 0) {
      throw new Error(`Sem paradas na rota`);
    }
    const parada1 = rota1.paradas[0];
    if (!parada1.endereco_completo || !parada1.status_pagamento || !Array.isArray(parada1.itens)) {
      throw new Error(`Dados de parada incompletos: ${JSON.stringify(parada1)}`);
    }
  });

  // 5. GET PDF Mapa de Carregamento
  await test('5. GET /api/v1/dispatch/trips/{id}/pdf/loading-sheet (Download Romaneio LIFO)', async () => {
    const tripId = dispatchResult.cargas_caminhao[0].viagem_id;
    const res = await fetch(`${API_BASE}/api/v1/dispatch/trips/${encodeURIComponent(tripId)}/pdf/loading-sheet`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const buf = await res.arrayBuffer();
    const header = new TextDecoder().decode(new Uint8Array(buf.slice(0, 4)));
    if (header !== '%PDF') throw new Error(`Arquivo retornado não é um PDF válido: ${header}`);
  });

  // 6. GET PDF Roteiro de Entregas
  await test('6. GET /api/v1/dispatch/trips/{id}/pdf/delivery-route (Download Roteiro TSP)', async () => {
    const tripId = dispatchResult.roteiros_entrega[0].viagem_id;
    const res = await fetch(`${API_BASE}/api/v1/dispatch/trips/${encodeURIComponent(tripId)}/pdf/delivery-route`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const buf = await res.arrayBuffer();
    const header = new TextDecoder().decode(new Uint8Array(buf.slice(0, 4)));
    if (header !== '%PDF') throw new Error(`Arquivo retornado não é um PDF válido: ${header}`);
  });

  // 7. GET Veículos
  await test('7. GET /api/v1/vehicles (Aba Veículos da Frota)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/vehicles`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length < 4) {
      throw new Error(`Esperado frota com 4 veículos, retornado ${data.length}`);
    }
  });

  // 8. GET Perfil Analítico de Eixos
  await test('8. GET /api/v1/analytics/axis-profile (Aba Eixos & Densidade)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/analytics/axis-profile`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error(`Nenhum perfil de eixo retornado`);
    }
  });

  // 9. POST Limpeza de Estado
  await test('9. POST /api/v1/dispatch/clear (Limpeza do Estado de Teste)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/dispatch/clear`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (data.status !== 'SUCESSO') throw new Error(`Status inesperado: ${data.status}`);
  });

  console.log(`\n------------------------------------------------------------`);
  console.log(` RESULTADO FINAL: ${passed} PASSOU / ${failed} FALHOU`);
  console.log(`------------------------------------------------------------\n`);

  if (failed > 0) {
    process.exit(1);
  }
}

runTests().catch((err) => {
  console.error('Erro fatal ao rodar testes:', err);
  process.exit(1);
});
