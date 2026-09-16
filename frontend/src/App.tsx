import React, { useState, useEffect, useCallback } from 'react';
import { Sidebar, NavItemKey } from './components/layout/Sidebar';
import { DashboardView } from './components/views/DashboardView';
import { PreparationView } from './components/views/PreparationView';
import { AxesView } from './components/views/AxesView';
import { VehiclesView } from './components/views/VehiclesView';
import { HistoryView } from './components/views/HistoryView';
import { api } from './services/api';
import { DecoupledOrderInput, DecoupledDispatchResponse } from './types/dispatch';
import { CheckCircle2, AlertCircle } from 'lucide-react';

export const App: React.FC = () => {
  const [activeNav, setActiveNav] = useState<NavItemKey>('dashboard');
  const [orders, setOrders] = useState<DecoupledOrderInput[]>([]);
  const [dispatchResult, setDispatchResult] = useState<DecoupledDispatchResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [lastExecutionTime, setLastExecutionTime] = useState<string | null>(null);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [notification, setNotification] = useState<{
    type: 'success' | 'error';
    message: string;
  } | null>(null);

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
    setIsProcessing(true);
    setNotification(null);

    try {
      let ordersToProcess = orders;
      if (!ordersToProcess || ordersToProcess.length === 0) {
        ordersToProcess = await api.fetchMockOrders();
        setOrders(ordersToProcess);
      }

      const result = await api.processOrders(ordersToProcess, 'Equilibrado', 20.0);
      setDispatchResult(result);
      const timeStr = getFormattedNow();
      setLastExecutionTime(timeStr);
      setNotification({
        type: 'success',
        message: `Otimização concluída com sucesso! ${result.resumo.total_trips_generated} viagens geradas com ${result.resumo.total_allocated_orders} pedidos alocados.`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha ao processar despacho de pedidos.';
      setNotification({ type: 'error', message: msg });
    } finally {
      setIsProcessing(false);
    }
  }, [orders]);

  // 3. Carrega o mock oficial de 30 pedidos
  const handleLoadMock = useCallback(async () => {
    setIsProcessing(true);
    setNotification(null);

    try {
      const mock = await api.fetchMockOrders();
      setOrders(mock);
      setNotification({
        type: 'success',
        message: `Mock oficial carregado com sucesso (${mock.length} pedidos)!`,
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha ao carregar pedidos mock.';
      setNotification({ type: 'error', message: msg });
    } finally {
      setIsProcessing(false);
    }
  }, []);

  // 4. Inicialização no Mount
  useEffect(() => {
    checkHealth();
    // Carrega mock e tenta recuperar resultado em memória
    api
      .fetchMockOrders()
      .then((m) => {
        setOrders(m);
        return api.fetchConsolidatedSummary();
      })
      .then((res) => {
        if (res && res.status === 'SUCESSO') {
          setDispatchResult(res);
          setLastExecutionTime(getFormattedNow());
        }
      })
      .catch(() => {
        // Fallback inicial
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
        {/* Banner de Notificação Flutuante */}
        {notification && (
          <div
            className={`mx-6 mt-4 p-3.5 rounded-xl border flex items-center justify-between text-xs font-semibold shadow-sm transition-all animate-fadeIn ${
              notification.type === 'success'
                ? 'bg-emerald-50 border-emerald-300 text-emerald-900'
                : 'bg-rose-50 border-rose-300 text-rose-900'
            }`}
          >
            <div className="flex items-center gap-2">
              {notification.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
              ) : (
                <AlertCircle className="w-4 h-4 text-rose-600" />
              )}
              <span>{notification.message}</span>
            </div>

            <button
              onClick={() => setNotification(null)}
              className="text-slate-400 hover:text-slate-700 ml-4"
            >
              &times;
            </button>
          </div>
        )}

        {/* Renderização da Tela Ativa */}
        <div className="flex-1">
          {activeNav === 'dashboard' && (
            <DashboardView
              dispatchResult={dispatchResult}
              totalOrdersCount={orders.length || 30}
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
              onLoadMock={handleLoadMock}
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
