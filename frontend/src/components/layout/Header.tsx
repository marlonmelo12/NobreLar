import React from 'react';
import { Truck, Play, RefreshCw, FileJson, Sparkles } from 'lucide-react';

interface HeaderProps {
  onLoadMock: () => void;
  onOpenImportModal: () => void;
  onProcessDispatch: () => void;
  isProcessing: boolean;
  ordersCount: number;
  selectedProfile: 'Equilibrado' | 'Priorizar Urgentes' | 'Minimizar Veículos';
  onSelectProfile: (profile: 'Equilibrado' | 'Priorizar Urgentes' | 'Minimizar Veículos') => void;
  backendOnline: boolean | null;
}

export const Header: React.FC<HeaderProps> = ({
  onLoadMock,
  onOpenImportModal,
  onProcessDispatch,
  isProcessing,
  ordersCount,
  selectedProfile,
  onSelectProfile,
  backendOnline,
}) => {
  return (
    <header className="bg-slate-900 text-white border-b border-slate-800 sticky top-0 z-40 shadow-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-18 py-3">
          
          {/* Logo & Marca Nobre Lar */}
          <div className="flex items-center gap-3.5">
            <div className="w-11 h-11 rounded-xl bg-nobre-500 text-slate-950 flex items-center justify-center font-black text-xl shadow-lg border-2 border-nobre-400">
              <Truck className="w-6 h-6 stroke-[2.5]" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-extrabold tracking-tight text-white">
                  Nobre<span className="text-nobre-500">LOG</span>
                </span>
                <span className="px-2 py-0.5 text-[10px] font-black uppercase tracking-wider bg-nobre-500/20 text-nobre-400 border border-nobre-500/40 rounded-md">
                  IA v2.0
                </span>
                <span className="hidden sm:inline-block px-2 py-0.5 text-[10px] font-bold text-slate-400 bg-slate-800 rounded-md">
                  Nobre Lar Materiais
                </span>
              </div>
              <p className="text-[11px] text-slate-400">
                Centro de Distribuição Regional Crateús — CE
              </p>
            </div>
          </div>

          {/* Seletor de Perfil e Ações Rápidas */}
          <div className="flex items-center gap-3">
            
            {/* Status Backend */}
            <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-800 text-[11px] font-medium text-slate-300 border border-slate-700">
              <span className={`w-2 h-2 rounded-full ${backendOnline === true ? 'bg-emerald-400 animate-pulse' : backendOnline === false ? 'bg-red-400' : 'bg-slate-500'}`} />
              <span>{backendOnline === true ? 'API Online' : backendOnline === false ? 'API Offline' : 'Checando...'}</span>
            </div>

            {/* Perfil de Otimização */}
            <div className="hidden md:flex items-center gap-1.5 bg-slate-800 px-3 py-1.5 rounded-xl border border-slate-700">
              <Sparkles className="w-3.5 h-3.5 text-nobre-400" />
              <label htmlFor="perfilSelect" className="text-xs text-slate-400 font-medium">Perfil:</label>
              <select
                id="perfilSelect"
                value={selectedProfile}
                onChange={(e) => onSelectProfile(e.target.value as 'Equilibrado' | 'Priorizar Urgentes' | 'Minimizar Veículos')}
                className="bg-transparent text-xs font-semibold text-white focus:outline-none cursor-pointer"
              >
                <option value="Equilibrado" className="bg-slate-800 text-white">Equilibrado (Padrão)</option>
                <option value="Priorizar Urgentes" className="bg-slate-800 text-white">Priorizar Urgentes</option>
                <option value="Minimizar Veículos" className="bg-slate-800 text-white">Minimizar Veículos</option>
              </select>
            </div>

            {/* Botão Carregar Mock */}
            <button
              type="button"
              onClick={onLoadMock}
              disabled={isProcessing}
              title="Carrega 30 pedidos estruturados do mock oficial da Nobre Lar"
              className="hidden sm:inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 rounded-xl border border-slate-700 transition disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 text-nobre-400 ${isProcessing ? 'animate-spin' : ''}`} />
              <span>Carregar Mock</span>
            </button>

            {/* Botão Importar JSON */}
            <button
              type="button"
              onClick={onOpenImportModal}
              disabled={isProcessing}
              title="Colar ou subir arquivo JSON customizado"
              className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 rounded-xl border border-slate-700 transition disabled:opacity-50"
            >
              <FileJson className="w-3.5 h-3.5 text-nobre-400" />
              <span className="hidden md:inline">Importar JSON</span>
              <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-700 text-slate-300 font-mono">
                {ordersCount}
              </span>
            </button>

            {/* Botão Principal: Executar Despacho (Amarelo Nobre #fdc700) */}
            <button
              type="button"
              onClick={onProcessDispatch}
              disabled={isProcessing || ordersCount === 0}
              className="inline-flex items-center gap-2 px-4.5 py-2.5 text-xs font-extrabold text-slate-950 bg-nobre-500 hover:bg-nobre-400 active:bg-nobre-600 rounded-xl shadow-nobre border border-nobre-400 transition transform hover:-translate-y-0.5 active:translate-y-0 disabled:opacity-40 disabled:cursor-not-allowed disabled:transform-none"
            >
              {isProcessing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin text-slate-950" />
                  <span>Otimizando...</span>
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-slate-950 text-slate-950" />
                  <span>Processar Lote</span>
                </>
              )}
            </button>

          </div>
        </div>
      </div>
    </header>
  );
};
