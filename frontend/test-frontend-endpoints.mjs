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

  // 2. Mock Orders
  let mockOrders = [];
  await test('2. GET /api/v1/dispatch/mock-orders (Mocks Canônicos)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/dispatch/mock-orders`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    mockOrders = await res.json();
    if (!Array.isArray(mockOrders) || mockOrders.length < 10) {
      throw new Error(`Esperado array com pedidos, recebido ${mockOrders.length}`);
    }
    const sample = mockOrders[0];
    if (!sample.id || !sample.cidade || !sample.situacao || !Array.isArray(sample.itens)) {
      throw new Error(`Estrutura de pedido inválida: ${JSON.stringify(sample)}`);
    }
  });

  // 3. Submissão POST Único de Pedidos
  let dispatchResult = null;
  await test('3. POST /api/v1/dispatch/orders (Processamento Desacoplado)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/dispatch/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pedidos: mockOrders,
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
  await test('4. GET /api/v1/dispatch/truck-load (Tela 1: Carroceria Aberta + Drilldown)', async () => {
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
    if (!primeiroPedido.posicao_carroceria || !Array.isArray(primeiroPedido.itens) || primeiroPedido.itens.length === 0) {
      throw new Error(`Drilldown de itens ausente no pedido`);
    }
  });

  // 5. GET Roteiros de Entrega TSP
  await test('5. GET /api/v1/dispatch/delivery-route (Tela 2: Roteiros TSP + Cobrança)', async () => {
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

  // 6. GET PDF Mapa de Carregamento
  await test('6. GET /api/v1/dispatch/trips/{id}/pdf/loading-sheet (Download Romaneio LIFO)', async () => {
    const tripId = dispatchResult.cargas_caminhao[0].viagem_id;
    const res = await fetch(`${API_BASE}/api/v1/dispatch/trips/${encodeURIComponent(tripId)}/pdf/loading-sheet`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const buf = await res.arrayBuffer();
    const header = new TextDecoder().decode(new Uint8Array(buf.slice(0, 4)));
    if (header !== '%PDF') throw new Error(`Arquivo retornado não é um PDF válido: ${header}`);
  });

  // 7. GET PDF Roteiro de Entregas
  await test('7. GET /api/v1/dispatch/trips/{id}/pdf/delivery-route (Download Roteiro TSP)', async () => {
    const tripId = dispatchResult.roteiros_entrega[0].viagem_id;
    const res = await fetch(`${API_BASE}/api/v1/dispatch/trips/${encodeURIComponent(tripId)}/pdf/delivery-route`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const buf = await res.arrayBuffer();
    const header = new TextDecoder().decode(new Uint8Array(buf.slice(0, 4)));
    if (header !== '%PDF') throw new Error(`Arquivo retornado não é um PDF válido: ${header}`);
  });

  // 8. GET Veículos
  await test('8. GET /api/v1/vehicles (Aba Veículos da Frota)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/vehicles`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length < 4) {
      throw new Error(`Esperado frota com 4 veículos, retornado ${data.length}`);
    }
  });

  // 9. GET Perfil Analítico de Eixos
  await test('9. GET /api/v1/analytics/axis-profile (Aba Eixos & Densidade)', async () => {
    const res = await fetch(`${API_BASE}/api/v1/analytics/axis-profile`);
    if (!res.ok) throw new Error(`Status ${res.status}`);
    const data = await res.json();
    if (!Array.isArray(data) || data.length === 0) {
      throw new Error(`Nenhum perfil de eixo retornado`);
    }
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
