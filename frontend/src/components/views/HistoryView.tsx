import React from 'react';
import { DecoupledDispatchResponse } from '../../types/dispatch';
import { History, FileText, CheckCircle2, AlertCircle, Ban } from 'lucide-react';
import { api } from '../../services/api';

interface HistoryViewProps {
  dispatchResult: DecoupledDispatchResponse | null;
  lastExecutionTime: string | null;
}

export const HistoryView: React.FC<HistoryViewProps> = ({
  dispatchResult,
  lastExecutionTime,
}) => {
  const descartes = dispatchResult?.descartes_limpeza || [];
  const trips = dispatchResult?.cargas_caminhao || [];

  return (
    <div className="max-w-5xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      <div className="text-center space-y-1">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Histórico e Auditoria de Expedição
        </h1>
        <p className="text-sm text-slate-500">
          Registro das últimas execuções de alocação, auditoria de descartes e emissão de romaneios.
        </p>
      </div>

      {/* Card da Última Execução */}
      {dispatchResult ? (
        <div className="border border-amber-400 bg-white rounded-2xl p-6 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-amber-100 pb-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-amber-100 text-amber-900 flex items-center justify-center font-bold">
                <History className="w-5 h-5" />
              </div>
              <div>
                <h3 className="font-bold text-slate-900 text-lg">
                  Lote Faturado — Execução Ativa
                </h3>
                <span className="text-xs text-slate-400 font-mono">
                  Timestamp: {lastExecutionTime || 'Hoje'} • Status: {dispatchResult.status}
                </span>
              </div>
            </div>

            <span className="bg-emerald-100 text-emerald-800 text-xs font-bold px-3 py-1 rounded-full flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Alocação Concluída
            </span>
          </div>

          {/* Resumo em Números */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-center">
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-xs text-slate-500 block">Lidos</span>
              <span className="text-xl font-bold text-slate-900 font-mono">
                {dispatchResult.resumo.total_records_read}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-xs text-slate-500 block">Alocados</span>
              <span className="text-xl font-bold text-slate-900 font-mono">
                {dispatchResult.resumo.total_allocated_orders}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-xs text-slate-500 block">Descartados</span>
              <span className="text-xl font-bold text-rose-700 font-mono">
                {dispatchResult.resumo.total_discarded_cleaning}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-xl">
              <span className="text-xs text-slate-500 block">Viagens</span>
              <span className="text-xl font-bold text-amber-700 font-mono">
                {dispatchResult.resumo.total_trips_generated}
              </span>
            </div>
          </div>

          {/* Romaneios em PDF */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Documentos Oficiais Gerados (PDFs para Download)
            </h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {trips.slice(0, 6).map((viagem) => (
                <div
                  key={viagem.viagem_id}
                  className="border border-slate-200 rounded-xl p-3 flex items-center justify-between bg-slate-50/50 hover:bg-amber-50/40 transition text-xs"
                >
                  <div>
                    <span className="font-bold text-slate-800 block">
                      {viagem.titulo} ({viagem.eixo_nome})
                    </span>
                    <span className="text-[11px] text-slate-500 font-mono">
                      {viagem.veiculo.nome}
                    </span>
                  </div>

                  <div className="flex items-center gap-1.5">
                    <a
                      href={api.getLoadingSheetPdfUrl(viagem.viagem_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-amber-400 hover:bg-amber-500 text-slate-950 font-bold px-2.5 py-1.5 rounded-lg flex items-center gap-1 text-[11px] shadow-sm transition"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Carga</span>
                    </a>
                    <a
                      href={api.getDeliveryRoutePdfUrl(viagem.viagem_id)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="bg-slate-800 hover:bg-slate-900 text-white font-bold px-2.5 py-1.5 rounded-lg flex items-center gap-1 text-[11px] shadow-sm transition"
                    >
                      <FileText className="w-3.5 h-3.5" />
                      <span>Rota</span>
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Log de Descartes de Limpeza */}
          {descartes.length > 0 && (
            <div className="space-y-3 pt-2">
              <h4 className="text-xs font-bold text-rose-700 uppercase tracking-wider flex items-center gap-1.5">
                <Ban className="w-4 h-4" />
                Auditoria de Descartes de Limpeza ({descartes.length})
              </h4>
              <div className="border border-rose-200 rounded-xl overflow-hidden text-xs">
                <table className="w-full text-left">
                  <thead className="bg-rose-50 text-rose-900 font-bold border-b border-rose-200">
                    <tr>
                      <th className="py-2.5 px-4">Pedido</th>
                      <th className="py-2.5 px-4">Regra</th>
                      <th className="py-2.5 px-4">Motivo do Descarte</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-rose-100 bg-white">
                    {descartes.map((d, idx) => (
                      <tr key={idx}>
                        <td className="py-2 px-4 font-mono font-bold text-rose-950">
                          {d.pedido}
                        </td>
                        <td className="py-2 px-4 font-mono text-slate-600">
                          {d.regra}
                        </td>
                        <td className="py-2 px-4 text-slate-700">
                          {d.motivo}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="border border-dashed border-amber-300 rounded-2xl p-12 text-center text-slate-500 bg-white space-y-2">
          <AlertCircle className="w-10 h-10 text-amber-500 mx-auto" />
          <h3 className="font-bold text-slate-800 text-base">Nenhuma execução recente</h3>
          <p className="text-xs text-slate-500">
            Acesse a aba <strong>Dashboard</strong> ou <strong>Preparar</strong> e execute a otimização de um lote.
          </p>
        </div>
      )}
    </div>
  );
};
