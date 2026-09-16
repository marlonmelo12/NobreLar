import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavItemKey } from './components/layout/Sidebar';
import { DashboardView } from './components/views/DashboardView';
import { PreparationView } from './components/views/PreparationView';
import { AxesView } from './components/views/AxesView';
import { VehiclesView } from './components/views/VehiclesView';
import { HistoryView } from './components/views/HistoryView';
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

  // 1. Checa a saúde da API backend
  const checkHealth = useCallback(async () => {
    try {
      await api.checkHealth();
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
    }
  }, []);

  // 2. Executa a otimização de despacho (CP-SAT multi-viagens + TSP)
  const handleExecuteDispatch = useCallback(async () => {
    if (!orders || orders.length === 0) {
      alert('Nenhum pedido carregado. Por favor, selecione um arquivo JSON ou CSV na tela de Preparação antes de executar.');
      return;
    }

    setIsProcessing(true);
    try {
      const result = await api.processOrders(orders, 'Equilibrado', 20.0);
      setDispatchResult(result);
      const timeStr = getFormattedNow();
      setLastExecutionTime(timeStr);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha ao processar despacho de pedidos.';
      alert(msg);
      console.error(msg);
    } finally {
      setIsProcessing(false);
    }
  }, [orders]);

  // 3. Inicialização no Mount (Verifica saúde e recupera despacho anterior se houver)
  useEffect(() => {
    checkHealth();
    api
      .fetchConsolidatedSummary()
      .then((res) => {
        if (res && res.status === 'SUCESSO' && res.cargas_caminhao && res.cargas_caminhao.length > 0) {
          setDispatchResult(res);
          setLastExecutionTime(getFormattedNow());
        }
      })
      .catch(() => {
        // Sem despacho anterior em memória
      });
  }, [checkHealth]);

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
            />
          )}

          {activeNav === 'preparar' && (
            <PreparationView
              orders={orders}
              dispatchResult={dispatchResult}
              isProcessing={isProcessing}
              onUploadCustomOrders={(newOrders) => setOrders(newOrders)}
              onExecuteDispatch={handleExecuteDispatch}
            />
          )}

          {activeNav === 'eixos' && <AxesView />}

          {activeNav === 'veiculos' && <VehiclesView />}

          {activeNav === 'historico' && (
            <HistoryView
              dispatchResult={dispatchResult}
              lastExecutionTime={lastExecutionTime}
            />
          )}
        </div>
      </main>
    </div>
  );
};
