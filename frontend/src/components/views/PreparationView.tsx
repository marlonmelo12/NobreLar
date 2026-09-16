import React, { useState } from 'react';
import {
  DecoupledOrderInput,
  DecoupledDispatchResponse,
} from '../../types/dispatch';
import {
  Upload,
  Download,
  Play,
  Loader2,
  Trash2,
  CheckCircle2,
  Package,
  Layers,
  Compass,
  FileSpreadsheet,
} from 'lucide-react';
import {
  parseCsvOrders,
  DEMO_CSV_CONTENT,
  DEMO_ORDERS,
} from '../../utils/csvParser';

interface PreparationViewProps {
  orders: DecoupledOrderInput[];
  dispatchResult: DecoupledDispatchResponse | null;
  isProcessing: boolean;
  onUploadCustomOrders: (orders: DecoupledOrderInput[]) => void;
  onExecuteDispatch: () => void;
  onClear?: () => void;
  onNavigateToOrders?: () => void;
  onNavigateToLoads?: () => void;
  onNavigateToRoutes?: () => void;
}

export const PreparationView: React.FC<PreparationViewProps> = ({
  orders,
  dispatchResult,
  isProcessing,
  onUploadCustomOrders,
  onExecuteDispatch,
  onClear,
  onNavigateToOrders,
  onNavigateToLoads,
  onNavigateToRoutes,
}) => {
  const [feedbackMsg, setFeedbackMsg] = useState<string | null>(null);

  // Cálculos rápidos de pré-visualização
  const totalPedidos = orders.length;
  const allItens = orders.flatMap((o) => o.itens || []);
  const totalProdutos = allItens.length;
  const totalValor = orders.reduce((acc, o) => acc + (o.valor || 0), 0);
  
  // Estimativa aproximada de peso e volume pré-otimização
  const totalPesoEstimado = allItens.reduce((acc, it) => {
    const unit = it.unidade.toUpperCase();
    const qtd = it.quantidade || 1;
    if (unit === 'SC') return acc + qtd * 50.0;
    if (unit === 'CX') return acc + qtd * 28.0;
    return acc + qtd * 15.0;
  }, 0);

  const totalVolumeEstimado = allItens.reduce((acc, it) => {
    const desc = (it.descricao || '').toUpperCase();
    const qtd = it.quantidade || 1;
    if (desc.includes('DAGUA') || desc.includes('BAKOF')) return acc + qtd * 1.2;
    return acc + qtd * 0.025;
  }, 0);

  const hasTrips = (dispatchResult?.cargas_caminhao?.length || 0) > 0;

  // Upload de arquivo (CSV ou JSON)
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const content = event.target?.result as string;
        if (file.name.endsWith('.json')) {
          const parsed = JSON.parse(content);
          const list: DecoupledOrderInput[] = Array.isArray(parsed)
            ? parsed
            : parsed.pedidos
            ? parsed.pedidos
            : [parsed];
          onUploadCustomOrders(list);
          setFeedbackMsg(`Arquivo JSON '${file.name}' carregado: ${list.length} pedidos.`);
        } else {
          // Processamento nativo de CSV
          const parsedOrders = parseCsvOrders(content);
          if (parsedOrders.length === 0) {
            alert('Não foi possível identificar pedidos no arquivo CSV. Verifique o delimitador (; ou ,) e as colunas.');
            return;
          }
          onUploadCustomOrders(parsedOrders);
          setFeedbackMsg(`Arquivo CSV '${file.name}' importado com sucesso: ${parsedOrders.length} pedidos.`);
        }
      } catch {
        alert('Erro ao processar o arquivo. Certifique-se de selecionar um CSV ou JSON válido.');
      }
    };
    reader.readAsText(file, 'utf-8');
  };

  // Baixar Modelo CSV Oficial
  const handleDownloadTemplate = () => {
    const blob = new Blob([DEMO_CSV_CONTENT], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', 'pedidos_demonstracao_nobre_lar.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    setFeedbackMsg('Modelo CSV baixado com sucesso!');
  };

  // Carregar dados de demonstração com 1 clique
  const handleLoadDemoData = () => {
    onUploadCustomOrders(DEMO_ORDERS);
    setFeedbackMsg('Lote oficial de demonstração (10 pedidos maximizados) carregado com sucesso!');
  };

  const fmtMoney = (val: number) =>
    new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val);

  return (
    <div className="max-w-6xl mx-auto py-8 px-6 space-y-7 animate-fadeIn">
      {/* Cabeçalho da Aba */}
      <div className="text-center space-y-1.5">
        <h1 className="text-2xl md:text-3xl font-extrabold text-slate-900 tracking-tight">
          Preparação & Importação de Pedidos
        </h1>
        <p className="text-xs md:text-sm text-slate-500 max-w-xl mx-auto">
          Importe o arquivo CSV de faturamento ou carregue o lote de demonstração para planejar a montagem das cargas e roteiros.
        </p>
      </div>

      {/* Caixa de Ações de Importação */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs space-y-4">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-amber-500" />
              <span>Arquivo de Pedidos Faturados</span>
            </h3>
            <p className="text-xs text-slate-500">
              Formatos aceitos: <strong>.CSV</strong> (separador ponto e vírgula ou vírgula) ou <strong>.JSON</strong>.
            </p>
          </div>

          {/* Botões de Ação */}
          <div className="flex items-center gap-2.5 flex-wrap">
            {/* Input de Arquivo */}
            <label className="inline-flex items-center gap-2 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl shadow-xs transition cursor-pointer">
              <Upload className="w-3.5 h-3.5 text-amber-400" />
              <span>Escolher Arquivo CSV</span>
              <input
                type="file"
                accept=".csv,.txt,.json"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            {/* Botão Baixar Modelo */}
            <button
              type="button"
              onClick={handleDownloadTemplate}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl border border-slate-200 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Baixar Modelo CSV</span>
            </button>

            {/* Botão Carregar Demonstração Instantâneo */}
            <button
              type="button"
              onClick={handleLoadDemoData}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 bg-amber-400 hover:bg-amber-500 active:bg-amber-600 text-slate-950 text-xs font-extrabold rounded-xl shadow-xs transition cursor-pointer"
            >
              <FileSpreadsheet className="w-3.5 h-3.5" />
              <span>Carregar Demonstração (CSV Otimizado)</span>
            </button>

            {/* Botão Limpar */}
            {totalPedidos > 0 && (
              <button
                type="button"
                onClick={() => {
                  if (onClear) {
                    onClear();
                  } else {
                    onUploadCustomOrders([]);
                  }
                  setFeedbackMsg(null);
                }}
                className="p-2 text-rose-600 hover:text-rose-800 hover:bg-rose-50 rounded-xl border border-rose-200 transition cursor-pointer"
                title="Limpar pedidos carregados"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* Mensagem de Feedback */}
        {feedbackMsg && (
          <div className="text-xs bg-emerald-50 text-emerald-800 border border-emerald-200 px-3.5 py-2 rounded-xl flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>{feedbackMsg}</span>
          </div>
        )}
      </div>

      {/* Se houver pedidos carregados */}
      {totalPedidos > 0 ? (
        <div className="space-y-6">
          {/* Métricas Compactas do Lote Carregado */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="bg-white rounded-xl border border-slate-200 p-4 text-center shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Total de Pedidos
              </span>
              <div className="text-2xl font-extrabold text-slate-900 font-mono mt-1">
                {totalPedidos}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 text-center shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Itens / Materiais
              </span>
              <div className="text-2xl font-extrabold text-slate-900 font-mono mt-1">
                {totalProdutos}
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 text-center shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Peso Estimado
              </span>
              <div className="text-xl font-extrabold text-slate-900 font-mono mt-1">
                {Math.round(totalPesoEstimado).toLocaleString('pt-BR')} kg
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 text-center shadow-xs">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Volume Estimado
              </span>
              <div className="text-xl font-extrabold text-slate-900 font-mono mt-1">
                {totalVolumeEstimado.toFixed(2)} m³
              </div>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4 text-center shadow-xs col-span-2 md:col-span-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block">
                Faturamento
              </span>
              <div className="text-lg font-extrabold text-emerald-700 font-mono mt-1">
                {fmtMoney(totalValor)}
              </div>
            </div>
          </div>

          {/* Banner de Ação Principal: Otimizar e Gerar Cargas */}
          <div className="bg-slate-900 text-white rounded-2xl p-6 shadow-sm flex flex-col md:flex-row items-center justify-between gap-4 border border-slate-800">
            <div className="space-y-1 text-center md:text-left">
              <div className="flex items-center gap-2 justify-center md:justify-start">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse" />
                <h3 className="text-base font-extrabold text-white">
                  Lote Pronto para Alocação Multi-Viagens
                </h3>
              </div>
              <p className="text-xs text-slate-400">
                Dispare o algoritmo CP-SAT e TSP para respeitar limites de peso, volume e gerar a rota com menor quilometragem.
              </p>
            </div>

            <button
              type="button"
              onClick={onExecuteDispatch}
              disabled={isProcessing}
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 bg-amber-400 hover:bg-amber-500 active:bg-amber-600 disabled:opacity-50 text-slate-950 font-black text-sm rounded-xl shadow transition cursor-pointer shrink-0"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Calculando Cargas & Rotas...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-slate-950" />
                  <span>Otimizar e Gerar Cargas</span>
                </>
              )}
            </button>
          </div>

          {/* Banner de Viagens Concluídas (se houver) */}
          {hasTrips && (
            <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-xs">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-emerald-500 text-white font-bold flex items-center justify-center shrink-0">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-sm font-bold text-emerald-950">
                    {dispatchResult?.cargas_caminhao.length} viagens geradas e otimizadas com sucesso!
                  </h4>
                  <p className="text-xs text-emerald-800">
                    Os materiais foram estivados e as rotas TSP calculadas a partir do CD Crateús.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                {onNavigateToLoads && (
                  <button
                    type="button"
                    onClick={onNavigateToLoads}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl transition cursor-pointer shadow-xs"
                  >
                    <Layers className="w-3.5 h-3.5" />
                    <span>Ver Cargas no Caminhão</span>
                  </button>
                )}
                {onNavigateToRoutes && (
                  <button
                    type="button"
                    onClick={onNavigateToRoutes}
                    className="inline-flex items-center gap-1.5 px-4 py-2 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl transition cursor-pointer shadow-xs"
                  >
                    <Compass className="w-3.5 h-3.5 text-emerald-400" />
                    <span>Ver Ordem de Entregas</span>
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Tabela de Pré-visualização dos Pedidos Importados */}
          <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs">
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-2">
                <Package className="w-4 h-4 text-amber-500" />
                <span>Pedidos do Lote ({totalPedidos})</span>
              </h3>
              {onNavigateToOrders && (
                <button
                  type="button"
                  onClick={onNavigateToOrders}
                  className="text-xs text-slate-600 hover:text-slate-900 font-semibold"
                >
                  Abrir Listagem Completa &rarr;
                </button>
              )}
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 text-slate-600 font-bold border-b border-slate-100">
                  <tr>
                    <th className="py-3 px-4">Pedido</th>
                    <th className="py-3 px-4">Cliente / Cidade</th>
                    <th className="py-3 px-4">Endereço</th>
                    <th className="py-3 px-4">Materiais do Pedido</th>
                    <th className="py-3 px-4 text-right">Valor</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {orders.map((ped, idx) => (
                    <tr key={ped.id || idx} className="hover:bg-slate-50/70 transition">
                      <td className="py-3 px-4 font-mono font-bold text-slate-900">
                        {ped.id}
                        {ped.urgente && (
                          <span className="block text-[10px] font-bold text-rose-600">
                            (Urgente)
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-bold text-slate-900 block">{ped.cliente}</span>
                        <span className="text-[11px] text-slate-500">{ped.cidade}</span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 max-w-xs truncate">
                        {ped.endereco}
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-col gap-0.5 max-w-md">
                          {ped.itens.slice(0, 3).map((it, i) => (
                            <span key={i} className="text-[11px] text-slate-700 truncate">
                              • <strong>{it.quantidade} {it.unidade}</strong> {it.descricao}
                            </span>
                          ))}
                          {ped.itens.length > 3 && (
                            <span className="text-[10px] text-slate-400">
                              + {ped.itens.length - 3} outros materiais...
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4 text-right font-mono font-bold text-emerald-700">
                        {fmtMoney(ped.valor)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : (
        /* Estado Vazio Quando Nenhum Pedido Foi Importado */
        <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs space-y-4">
          <div className="w-14 h-14 mx-auto rounded-2xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-600">
            <FileSpreadsheet className="w-7 h-7" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-bold text-slate-900">
              Nenhum Pedido Carregado
            </h3>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              Clique em <strong>Escolher Arquivo CSV</strong> para importar seus pedidos ou em <strong>Carregar Demonstração</strong> para iniciar uma simulação imediata de alta capacidade.
            </p>
          </div>
          <button
            type="button"
            onClick={handleLoadDemoData}
            className="inline-flex items-center gap-2 px-5 py-2.5 bg-amber-400 hover:bg-amber-500 active:bg-amber-600 text-slate-950 text-xs font-black rounded-xl shadow-xs transition cursor-pointer"
          >
            <Play className="w-3.5 h-3.5 fill-slate-950" />
            <span>Carregar Lote de Demonstração com 1 Clique</span>
          </button>
        </div>
      )}
    </div>
  );
};
