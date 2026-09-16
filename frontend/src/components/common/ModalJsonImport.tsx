import React, { useState } from 'react';
import { X, Upload, CheckCircle2, AlertCircle, FileCode } from 'lucide-react';
import { DecoupledOrderInput } from '../../types/dispatch';

interface ModalJsonImportProps {
  isOpen: boolean;
  onClose: () => void;
  onImport: (orders: DecoupledOrderInput[]) => void;
  currentOrdersCount: number;
}

export const ModalJsonImport: React.FC<ModalJsonImportProps> = ({
  isOpen,
  onClose,
  onImport,
  currentOrdersCount,
}) => {
  const [jsonText, setJsonText] = useState('');
  const [parseError, setParseError] = useState<string | null>(null);
  const [parsedOrders, setParsedOrders] = useState<DecoupledOrderInput[] | null>(null);

  if (!isOpen) return null;

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const val = e.target.value;
    setJsonText(val);

    if (!val.trim()) {
      setParseError(null);
      setParsedOrders(null);
      return;
    }

    try {
      const parsed = JSON.parse(val);
      if (!Array.isArray(parsed)) {
        setParseError('O JSON deve ser um array de pedidos [ { ... }, { ... } ].');
        setParsedOrders(null);
        return;
      }
      setParseError(null);
      setParsedOrders(parsed as DecoupledOrderInput[]);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setParseError(`Sintaxe JSON inválida: ${err.message}`);
      } else {
        setParseError('Sintaxe JSON inválida.');
      }
      setParsedOrders(null);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      setJsonText(content);
      try {
        const parsed = JSON.parse(content);
        if (Array.isArray(parsed)) {
          setParseError(null);
          setParsedOrders(parsed as DecoupledOrderInput[]);
        } else {
          setParseError('O arquivo deve conter um array JSON de pedidos.');
          setParsedOrders(null);
        }
      } catch (err: unknown) {
        setParseError('Erro ao decodificar JSON do arquivo.');
        setParsedOrders(null);
      }
    };
    reader.readAsText(file);
  };

  const handleConfirm = () => {
    if (parsedOrders && parsedOrders.length > 0) {
      onImport(parsedOrders);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-in fade-in">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-2xl overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="px-6 py-4 bg-slate-900 text-white flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-nobre-500 text-slate-950 flex items-center justify-center font-bold shadow-sm">
              <FileCode className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Importar Lote de Pedidos JSON</h2>
              <p className="text-xs text-slate-400">Insira ou anexe o JSON de pedidos faturados da Nobre Lar</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Body */}
        <div className="p-6 space-y-4 overflow-y-auto flex-1">
          <div className="flex items-center justify-between">
            <label htmlFor="jsonInput" className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Cole o JSON estruturado abaixo:
            </label>
            <label className="cursor-pointer inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 px-3 py-1.5 rounded-lg border border-slate-300 transition">
              <Upload className="w-3.5 h-3.5" />
              <span>Carregar arquivo .json</span>
              <input
                type="file"
                accept=".json,application/json"
                className="hidden"
                onChange={handleFileUpload}
              />
            </label>
          </div>

          <textarea
            id="jsonInput"
            value={jsonText}
            onChange={handleTextChange}
            placeholder={`[
  {
    "id": "L12608361",
    "cliente": "CONSTRUTORA SERRA AZUL",
    "cidade": "CRATEUS",
    "endereco": "Rua Coronel Zezé, 1020",
    "valor": 1250.00,
    "situacao": "URGENTE",
    "itens": [ ... ]
  }
]`}
            className="w-full h-64 p-3.5 font-mono text-xs bg-slate-950 text-slate-100 rounded-xl border border-slate-800 focus:outline-none focus:ring-2 focus:ring-nobre-500 selection:bg-nobre-500 selection:text-slate-900"
          />

          {/* Feedback de Validação */}
          {parseError && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-xl flex items-start gap-2.5 text-xs text-red-700">
              <AlertCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
              <span>{parseError}</span>
            </div>
          )}

          {parsedOrders && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl flex items-center justify-between text-xs text-emerald-800 font-semibold">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>JSON Válido: {parsedOrders.length} pedidos detectados no lote.</span>
              </div>
              <span className="font-mono text-emerald-700">
                Total: R$ {parsedOrders.reduce((acc, p) => acc + (p.valor || 0), 0).toLocaleString('pt-BR', { minimumFractionDigits: 2 })}
              </span>
            </div>
          )}

          <div className="text-xs text-slate-500 space-y-1 bg-slate-50 p-3 rounded-xl border border-slate-200">
            <p className="font-semibold text-slate-700">Lote atual em memória: {currentOrdersCount} pedidos.</p>
            <p>Os pedidos devem conter `id`, `cidade`, `valor`, `situacao` e o array `itens` com quantidades.</p>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200 flex items-center justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-200 rounded-lg transition"
          >
            Cancelar
          </button>
          <button
            type="button"
            disabled={!parsedOrders || parsedOrders.length === 0}
            onClick={handleConfirm}
            className="px-5 py-2 text-xs font-bold text-slate-900 bg-nobre-500 hover:bg-nobre-400 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg shadow-sm border border-nobre-600 transition flex items-center gap-2"
          >
            <CheckCircle2 className="w-4 h-4" />
            <span>Aplicar Lote ({parsedOrders?.length || 0} pedidos)</span>
          </button>
        </div>
      </div>
    </div>
  );
};
