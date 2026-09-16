import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/layout/Header';
import { TabNavigation, ActiveTabType } from './components/layout/TabNavigation';
import { TruckLoadView } from './components/loads/TruckLoadView';
import { DeliveryRouteView } from './components/routes/DeliveryRouteView';
import { DiscardedOrdersView } from './components/cleaning/DiscardedOrdersView';
import { RawOrdersView } from './components/raw/RawOrdersView';
import { ModalJsonImport } from './components/common/ModalJsonImport';
import { api } from './services/api';
import {
  DecoupledOrderInput,
  DecoupledDispatchResponse,
} from './types/dispatch';
import { AlertCircle, CheckCircle, RefreshCw } from 'lucide-react';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTabType>('loads');
  const [orders, setOrders] = useState<DecoupledOrderInput[]>([]);
  const [dispatchResult, setDispatchResult] = useState<DecoupledDispatchResponse | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState<'Equilibrado' | 'Priorizar Urgentes' | 'Minimizar Veículos'>('Equilibrado');
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // 1. Checa a saúde da API backend
  const checkHealth = useCallback(async () => {
    try {
      await api.checkHealth();
      setBackendOnline(true);
    } catch {
      setBackendOnline(false);
    }
  }, []);

  // 2. Executa o processamento do lote (POST /orders)
  const handleProcessOrders = useCallback(
    async (batchOrders: DecoupledOrderInput[], profile = selectedProfile) => {
      if (!batchOrders || batchOrders.length === 0) {
        setErrorMessage('Nenhum pedido no lote para processar.');
        return;
      }

      setIsProcessing(true);
      setErrorMessage(null);
      setSuccessMessage(null);

      try {
        const result = await api.processOrders(batchOrders, profile);
        setDispatchResult(result);
        setSuccessMessage(
          `Otimização concluída com sucesso! ${result.resumo.total_trips_generated} viagens geradas com ${result.resumo.total_allocated_orders} pedidos alocados.`
        );
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Falha ao processar despacho de pedidos.';
        setErrorMessage(msg);
      } finally {
        setIsProcessing(false);
      }
    },
    [selectedProfile]
  );

  // 3. Carrega o Mock Oficial da Nobre Lar (30 pedidos) e processa automaticamente
  const handleLoadMock = useCallback(async () => {
    setIsProcessing(true);
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const mockOrders = await api.fetchMockOrders();
      setOrders(mockOrders);
      await handleProcessOrders(mockOrders);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Falha ao carregar mock oficial de pedidos.';
      setErrorMessage(msg);
      setIsProcessing(false);
    }
  }, [handleProcessOrders]);

  // Inicialização no Mount
  useEffect(() => {
    checkHealth();
    handleLoadMock();
  }, [checkHealth, handleLoadMock]);

  // Importação de lote customizado pelo usuário
  const handleCustomImport = (importedOrders: DecoupledOrderInput[]) => {
    setOrders(importedOrders);
    handleProcessOrders(importedOrders);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      
      {/* Header Superior com Identidade Nobre Lar #fdc700 */}
      <Header
        onLoadMock={handleLoadMock}
        onOpenImportModal={() => setIsImportModalOpen(true)}
        onProcessDispatch={() => handleProcessOrders(orders)}
        isProcessing={isProcessing}
        ordersCount={orders.length}
        selectedProfile={selectedProfile}
        onSelectProfile={(p) => {
          setSelectedProfile(p);
          if (orders.length > 0) {
            handleProcessOrders(orders, p);
          }
        }}
        backendOnline={backendOnline}
      />

      {/* Navegação por Abas */}
      <TabNavigation
        activeTab={activeTab}
        onChangeTab={setActiveTab}
        tripsCount={dispatchResult?.cargas_caminhao.length || 0}
        routesCount={dispatchResult?.roteiros_entrega.length || 0}
        discardedCount={dispatchResult?.descartes_limpeza.length || 0}
        rawCount={orders.length}
      />

      {/* Área Principal de Conteúdo */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Banner de Erro */}
        {errorMessage && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-2xl flex items-center justify-between text-xs text-red-800 animate-in fade-in shadow-xs">
            <div className="flex items-center gap-2.5">
              <AlertCircle className="w-5 h-5 text-red-600 shrink-0" />
              <span className="font-semibold">{errorMessage}</span>
            </div>
            <button
              onClick={() => setErrorMessage(null)}
              className="text-red-600 hover:text-red-900 font-bold ml-4"
            >
              Fechar
            </button>
          </div>
        )}

        {/* Banner de Sucesso */}
        {successMessage && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl flex items-center justify-between text-xs text-emerald-900 animate-in fade-in shadow-xs">
            <div className="flex items-center gap-2.5">
              <CheckCircle className="w-5 h-5 text-emerald-600 shrink-0" />
              <span className="font-semibold">{successMessage}</span>
            </div>
            <button
              onClick={() => setSuccessMessage(null)}
              className="text-emerald-700 hover:text-emerald-950 font-bold ml-4"
            >
              Fechar
            </button>
          </div>
        )}

        {/* Indicador de Processamento em Andamento */}
        {isProcessing && (
          <div className="p-8 bg-white rounded-2xl border border-slate-200 shadow-xs flex flex-col items-center justify-center text-center space-y-3">
            <div className="w-12 h-12 rounded-2xl bg-nobre-100 border border-nobre-400 text-nobre-900 flex items-center justify-center animate-spin">
              <RefreshCw className="w-6 h-6 text-slate-900" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">
                Otimizando Despacho com CP-SAT e TSP...
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Calculando cubagem técnica, limites de carga aberta e menor tortuosidade de entrega.
              </p>
            </div>
          </div>
        )}

        {/* Renderização Condicional das Telas */}
        {!isProcessing && (
          <>
            {activeTab === 'loads' && (
              <TruckLoadView cargas={dispatchResult?.cargas_caminhao || []} />
            )}

            {activeTab === 'routes' && (
              <DeliveryRouteView roteiros={dispatchResult?.roteiros_entrega || []} />
            )}

            {activeTab === 'cleaning' && (
              <DiscardedOrdersView descartes={dispatchResult?.descartes_limpeza || []} />
            )}

            {activeTab === 'raw' && (
              <RawOrdersView orders={orders} />
            )}
          </>
        )}

      </main>

      {/* Footer Institucional */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-nobre-500" />
            <span className="font-bold text-slate-800">NobreLOG IA</span>
            <span>— Sistema Integrado de Expedição & Roteirização</span>
          </div>
          <div className="text-[11px] text-slate-400">
            Nobre Lar Comércio de Materiais de Construção • Crateús - CE
          </div>
        </div>
      </footer>

      {/* Modal de Importação JSON */}
      <ModalJsonImport
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        onImport={handleCustomImport}
        currentOrdersCount={orders.length}
      />

    </div>
  );
};
