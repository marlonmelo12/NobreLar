import React from 'react';
import { Truck, MapPin, ShieldAlert, ListOrdered } from 'lucide-react';

export type ActiveTabType = 'loads' | 'routes' | 'cleaning' | 'raw';

interface TabNavigationProps {
  activeTab: ActiveTabType;
  onChangeTab: (tab: ActiveTabType) => void;
  tripsCount: number;
  routesCount: number;
  discardedCount: number;
  rawCount: number;
}

export const TabNavigation: React.FC<TabNavigationProps> = ({
  activeTab,
  onChangeTab,
  tripsCount,
  routesCount,
  discardedCount,
  rawCount,
}) => {
  const tabs = [
    {
      id: 'loads' as ActiveTabType,
      label: 'Cargas no Caminhão',
      sublabel: 'Carroceria Aberta & LIFO',
      icon: Truck,
      count: tripsCount,
    },
    {
      id: 'routes' as ActiveTabType,
      label: 'Roteiros de Entrega',
      sublabel: 'Sequência TSP & Cobrança',
      icon: MapPin,
      count: routesCount,
    },
    {
      id: 'cleaning' as ActiveTabType,
      label: 'Descartes da Limpeza',
      sublabel: 'Balcão & Cancelados',
      icon: ShieldAlert,
      count: discardedCount,
      countVariant: discardedCount > 0 ? 'bg-amber-100 text-amber-800 border-amber-300' : undefined,
    },
    {
      id: 'raw' as ActiveTabType,
      label: 'Lote de Pedidos',
      sublabel: 'Faturamento do Dia',
      icon: ListOrdered,
      count: rawCount,
    },
  ];

  return (
    <div className="border-b border-slate-200 bg-white sticky top-18 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <nav className="flex space-x-2 sm:space-x-4 overflow-x-auto py-2" aria-label="Tabs">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;

            return (
              <button
                key={tab.id}
                type="button"
                onClick={() => onChangeTab(tab.id)}
                className={`group relative flex items-center gap-3 px-4 py-3 text-left rounded-xl transition font-medium whitespace-nowrap ${
                  isActive
                    ? 'bg-slate-900 text-white shadow-sm'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                }`}
              >
                <div
                  className={`w-9 h-9 rounded-lg flex items-center justify-center transition shrink-0 ${
                    isActive
                      ? 'bg-nobre-500 text-slate-950 font-bold'
                      : 'bg-slate-100 text-slate-600 group-hover:bg-slate-200'
                  }`}
                >
                  <Icon className="w-5 h-5" />
                </div>

                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold">{tab.label}</span>
                    <span
                      className={`px-2 py-0.5 rounded-full text-[11px] font-mono font-bold border ${
                        tab.countVariant ||
                        (isActive
                          ? 'bg-nobre-500/20 text-nobre-300 border-nobre-500/40'
                          : 'bg-slate-100 text-slate-700 border-slate-300')
                      }`}
                    >
                      {tab.count}
                    </span>
                  </div>
                  <p
                    className={`text-[11px] ${
                      isActive ? 'text-slate-300' : 'text-slate-500'
                    }`}
                  >
                    {tab.sublabel}
                  </p>
                </div>

                {/* Borda inferior dourada quando ativo */}
                {isActive && (
                  <div className="absolute -bottom-2 left-4 right-4 h-1 bg-nobre-500 rounded-t-md" />
                )}
              </button>
            );
          })}
        </nav>
      </div>
    </div>
  );
};
