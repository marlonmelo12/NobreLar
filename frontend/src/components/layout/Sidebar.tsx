import React from 'react';
import {
  LayoutDashboard,
  Search,
  Layers,
  Route,
  Package,
  Radio,
  Truck,
  History,
  CheckCircle2,
  XCircle,
} from 'lucide-react';

export type NavItemKey =
  | 'dashboard'
  | 'preparar'
  | 'cargas'
  | 'rotas'
  | 'pedidos'
  | 'eixos'
  | 'veiculos'
  | 'historico';

interface SidebarProps {
  activeItem: NavItemKey;
  onSelect: (item: NavItemKey) => void;
  backendOnline: boolean | null;
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeItem,
  onSelect,
  backendOnline,
}) => {
  const menuItems = [
    { key: 'dashboard' as NavItemKey, label: 'Dashboard', icon: LayoutDashboard },
    { key: 'preparar' as NavItemKey, label: 'Preparar', icon: Search },
    { key: 'cargas' as NavItemKey, label: 'Cargas no Caminhão', icon: Layers },
    { key: 'rotas' as NavItemKey, label: 'Ordem de Entregas', icon: Route },
    { key: 'pedidos' as NavItemKey, label: 'Todos os Pedidos', icon: Package },
    { key: 'eixos' as NavItemKey, label: 'Eixos', icon: Radio },
    { key: 'veiculos' as NavItemKey, label: 'Veículos', icon: Truck },
    { key: 'historico' as NavItemKey, label: 'Histórico', icon: History },
  ];

  return (
    <aside className="w-64 bg-white border-r border-slate-200 flex flex-col justify-between h-screen sticky top-0 select-none shadow-sm z-20">
      <div>
        {/* Logo Nobre Lar (conforme protótipo Figma) */}
        <div className="p-6 flex items-center gap-3 border-b border-slate-100">
          <div className="w-10 h-10 rounded-lg bg-amber-400 flex items-center justify-center font-black text-slate-900 text-lg shadow-sm">
            NL
          </div>
          <div>
            <span className="font-extrabold text-lg text-slate-900 tracking-tight block">
              Nobre Lar
            </span>
            <span className="text-[10px] text-amber-600 font-bold uppercase tracking-wider block">
              NobreLOG IA
            </span>
          </div>
        </div>

        {/* Menu Items */}
        <nav className="p-4 space-y-1.5">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeItem === item.key;
            return (
              <button
                key={item.key}
                onClick={() => onSelect(item.key)}
                className={`w-full flex items-center gap-3.5 px-4 py-2.5 rounded-xl font-medium text-sm transition-all duration-150 ${
                  isActive
                    ? 'bg-[#FEE580] text-slate-950 font-bold shadow-sm'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
                }`}
              >
                <Icon
                  className={`w-5 h-5 ${
                    isActive ? 'text-slate-950' : 'text-slate-500'
                  }`}
                />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Rodapé da Sidebar com Status da Conexão */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/70">
        <div className="flex items-center justify-between text-xs text-slate-600">
          <span className="font-medium">API Desacoplada</span>
          <div className="flex items-center gap-1.5 font-semibold">
            {backendOnline === true ? (
              <>
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span className="text-emerald-700">Online</span>
              </>
            ) : backendOnline === false ? (
              <>
                <XCircle className="w-3.5 h-3.5 text-rose-600" />
                <span className="text-rose-700">Offline</span>
              </>
            ) : (
              <span className="text-slate-400">Verificando...</span>
            )}
          </div>
        </div>
        <div className="text-[11px] text-slate-400 mt-1 text-center">
          CD Crateús - CE • Frota Aberta
        </div>
      </div>
    </aside>
  );
};
