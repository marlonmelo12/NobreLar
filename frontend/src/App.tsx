import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavItemKey } from './components/layout/Sidebar';
import { DashboardView } from './components/views/DashboardView';
import { PreparationView } from './components/views/PreparationView';
import { AxesView } from './components/views/AxesView';
import { VehiclesView } from './components/views/VehiclesView';
import { HistoryView } from './components/views/HistoryView';
import { OrdersView } from './components/views/OrdersView';
import { TruckLoadView } from './components/loads/TruckLoadView';
import { DeliveryRouteView } from './components/routes/DeliveryRouteView';
import { api } from './services/api';
import { DecoupledOrderInput, DecoupledDispatchResponse } from './types/dispatch';

export const App: React.FC = () => {
  const [activeNav, setActiveNav] = useState<NavItemKey>('dashboard');
  const [orders, setOrders] = useState<DecoupledOrderInput[]>([]);
  const [dispatchResult, setDispatchResult] = useState<DecoupledDispatchResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastExecutionTime, setLastExecutionTime] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

  // Formata data e hora para o padrão do Figma: HH:mm DD/MM/AAAA
  const getFormattedNow = () => {
    const d = new Date();
    const pad = (n: number) => String(n).padStart(2, '0');
    return `${pad(d.getHours())}:${pad(d.getMinutes())} ${pad(d.getDate())}/${pad(d.getMonth() + 1)}/${d.getFullYear()}`;
  };

  // 1. Checa a saúde da API backend e sincroniza despacho ativo se houver
  const checkHealthAndSync = useCallback(async () => {
    try {
      await api.checkHealth();
      setBackendOnline(true);

      const summary = await api.fetchConsolidatedSummary();
      if (summary && summary.resumo && summary.resumo.total_records_read > 0) {
        setDispatchResult(summary);
        setLastExecutionTime(getFormattedNow());
      }
    } catch {
      setBackendOnline(false);
    }
  }, []);

  // 2. Simula a carga de pedidos da API (ficam inicialmente desalocados no Dashboard)
  const handleSimulateApiLoad = useCallback(async () => {
    setIsProcessing(true);
    try {
      const result = await api.simulateLoad();
      setDispatchResult(result);
      setLastExecutionTime(getFormattedNow());
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha ao simular carga da API.';
      alert(msg);
      console.error(msg);
    } finally {
      setIsProcessing(false);
    }
  }, []);

  // 3. Executa o controle dos limites e roteirização (CP-SAT multi-viagens + TSP)
  const handleExecuteDispatch = useCallback(async () => {
    const hasStagedOrders = (dispatchResult?.resumo?.total_unallocated_orders || 0) > 0 || (dispatchResult?.pedidos_nao_alocados?.length || 0) > 0;
    const hasUploadedOrders = orders && orders.length > 0;

    if (!hasStagedOrders && !hasUploadedOrders) {
      // Se nada estiver carregado, simula a carga da API automaticamente primeiro
      setIsProcessing(true);
      try {
        const staged = await api.simulateLoad();
        setDispatchResult(staged);
      } catch (err: unknown) {
        setIsProcessing(false);
        const msg = err instanceof Error ? err.message : 'Falha ao carregar pedidos.';
        alert(msg);
        return;
      }
    }

    setIsProcessing(true);
    try {
      const result = await api.executeLimits(hasUploadedOrders ? orders : undefined, 'Equilibrado', 20.0);
      setDispatchResult(result);
      const timeStr = getFormattedNow();
      setLastExecutionTime(timeStr);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha ao processar controle dos limites e rotas.';
      alert(msg);
      console.error(msg);
    } finally {
      setIsProcessing(false);
    }
  }, [orders, dispatchResult]);

  // 4. Limpa completamente pedidos e despacho
  const handleClearDispatch = useCallback(async () => {
    setOrders([]);
    setDispatchResult(null);
    setLastExecutionTime(null);
    try {
      await api.clearDispatchState();
    } catch {
      // Silencioso
    }
  }, []);

  // 5. Inicialização no Mount (Verifica saúde da API e sincroniza despacho ativo)
  useEffect(() => {
    checkHealthAndSync();
  }, [checkHealthAndSync]);

  return (
    <div className="flex h-screen bg-[#FDFDFD] font-sans overflow-hidden text-slate-800">
      {/* Menu Lateral Esquerdo conforme Protótipo Figma */}
      <Sidebar
        activeItem={activeNav}
        onSelect={setActiveNav}
        backendOnline={backendOnline}
      />

      {/* Área Principal de Conteúdo */}
      <main className="flex-1 flex flex-col h-screen overflow-y-auto relative">
        {/* Renderização da Tela Ativa */}
        <div className="flex-1">
          {activeNav === 'dashboard' && (
            <DashboardView
              dispatchResult={dispatchResult}
              totalOrdersCount={orders.length}
              lastExecutionTime={lastExecutionTime}
              isProcessing={isProcessing}
              onExecute={handleExecuteDispatch}
              onSimulateApiLoad={handleSimulateApiLoad}
              onClear={handleClearDispatch}
              onNavigateToLoads={() => setActiveNav('cargas')}
              onNavigateToRoutes={() => setActiveNav('rotas')}
            />
          )}

          {activeNav === 'preparar' && (
            <PreparationView
              orders={orders}
              dispatchResult={dispatchResult}
              isProcessing={isProcessing}
              onUploadCustomOrders={async (newOrders) => {
                setOrders(newOrders);
                try {
                  const staged = await api.stageOrders(newOrders);
                  setDispatchResult(staged);
                  setLastExecutionTime(getFormattedNow());
                } catch {
                  // Mantém as ordens locais
                }
              }}
              onExecuteDispatch={handleExecuteDispatch}
              onClear={handleClearDispatch}
              onNavigateToOrders={() => setActiveNav('pedidos')}
              onNavigateToLoads={() => setActiveNav('cargas')}
              onNavigateToRoutes={() => setActiveNav('rotas')}
            />
          )}

          {activeNav === 'cargas' && (
            <TruckLoadView cargas={dispatchResult?.cargas_caminhao || []} />
          )}

          {activeNav === 'rotas' && (
            <DeliveryRouteView roteiros={dispatchResult?.roteiros_entrega || []} />
          )}

          {activeNav === 'pedidos' && (
            <OrdersView
              dispatchResult={dispatchResult}
              uploadedOrders={orders}
              onNavigateToPrepare={() => setActiveNav('preparar')}
            />
          )}

          {activeNav === 'eixos' && <AxesView />}

          {activeNav === 'veiculos' && <VehiclesView />}

          {activeNav === 'historico' && (
            <HistoryView
              dispatchResult={dispatchResult}
              lastExecutionTime={lastExecutionTime}
              onClear={handleClearDispatch}
            />
          )}
        </div>
      </main>
    </div>
  );
};
