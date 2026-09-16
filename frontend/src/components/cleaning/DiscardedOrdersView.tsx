import React from 'react';
import { DiscardedCleaningLog } from '../../types/dispatch';
import { ShieldAlert, CheckCircle } from 'lucide-react';

interface DiscardedOrdersViewProps {
  descartes: DiscardedCleaningLog[];
}

export const DiscardedOrdersView: React.FC<DiscardedOrdersViewProps> = ({ descartes }) => {
  if (!descartes || descartes.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-xs">
        <div className="w-14 h-14 mx-auto rounded-2xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4 border border-emerald-200">
          <CheckCircle className="w-7 h-7" />
        </div>
        <h3 className="text-base font-bold text-slate-800">Nenhum Pedido Descartado</h3>
        <p className="text-xs text-slate-500 max-w-sm mx-auto mt-1">
          Todos os pedidos processados foram validados com sucesso e estavam aptos para expedição rodoviária.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Banner Informativo */}
      <div className="bg-amber-50 rounded-2xl border border-amber-200 p-5 shadow-xs flex items-start gap-3.5">
        <div className="w-9 h-9 rounded-xl bg-amber-500 text-slate-950 font-bold flex items-center justify-center shrink-0 shadow-sm mt-0.5">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <h3 className="text-sm font-extrabold text-amber-900">
            Auditoria de Limpeza e Higienização de Faturamento ({descartes.length} pedidos expurgados)
          </h3>
          <p className="text-xs text-amber-800 mt-1 leading-relaxed">
            O algoritmo expurga automaticamente pedidos com <strong>retirada no balcão da loja</strong> ou <strong>cancelados</strong> para que não ocupem peso nem volume útil na carroceria aberta dos caminhões.
          </p>
        </div>
      </div>

      {/* Tabela de Descartes */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="p-5 border-b border-slate-100 flex items-center justify-between">
          <h4 className="text-sm font-extrabold text-slate-900">
            Registro Auditado de Descartes
          </h4>
          <span className="text-xs text-slate-500">
            Total: <strong>{descartes.length} registros</strong>
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 text-slate-700 font-semibold border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Pedido</th>
                <th className="py-3 px-4">Regra Acionada</th>
                <th className="py-3 px-4">Justificativa da Auditoria Logística</th>
                <th className="py-3 px-4 text-center">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {descartes.map((d, idx) => (
                <tr key={`${d.pedido}-${idx}`} className="hover:bg-slate-50 transition">
                  <td className="py-3 px-4 font-mono font-bold text-slate-900">
                    {d.pedido}
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2.5 py-1 rounded-full text-[11px] font-mono font-bold bg-slate-100 text-slate-800 border border-slate-300">
                      {d.regra}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-700 font-medium max-w-md">
                    {d.motivo}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300 uppercase">
                      Expurgado
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
};
