import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Truck, AlertTriangle, ShieldCheck, Loader2 } from 'lucide-react';

interface VehicleCard {
  id: string;
  name: string;
  plate: string;
  capacity_kg: number;
  useful_volume_m3: number;
  useful_length_m: number;
  allows_long_items: boolean;
  restricted_to_crateus: boolean;
  tipo_carroceria: string;
}

const DEFAULT_FLEET: VehicleCard[] = [
  {
    id: 'accelo-815-01',
    name: 'Mercedes-Benz Accelo 815 (Caminhão Grande 01)',
    plate: 'NBL-8151',
    capacity_kg: 4800.0,
    useful_volume_m3: 18.5,
    useful_length_m: 6.2,
    allows_long_items: true,
    restricted_to_crateus: false,
    tipo_carroceria: 'Carroceria Aberta (Grade Baixa)',
  },
  {
    id: 'accelo-815-02',
    name: 'Mercedes-Benz Accelo 815 (Caminhão Grande 02)',
    plate: 'NBL-8152',
    capacity_kg: 4800.0,
    useful_volume_m3: 18.5,
    useful_length_m: 6.2,
    allows_long_items: true,
    restricted_to_crateus: false,
    tipo_carroceria: 'Carroceria Aberta (Grade Baixa)',
  },
  {
    id: 'kia-bongo-01',
    name: 'Kia Bongo K2500 (Caminhão Médio 01)',
    plate: 'NBL-2500',
    capacity_kg: 1700.0,
    useful_volume_m3: 6.5,
    useful_length_m: 3.1,
    allows_long_items: false,
    restricted_to_crateus: true,
    tipo_carroceria: 'Carroceria Aberta (Grade Baixa)',
  },
  {
    id: 'hyundai-hr-01',
    name: 'Hyundai HR (Caminhão Médio 02)',
    plate: 'NBL-2600',
    capacity_kg: 1700.0,
    useful_volume_m3: 6.5,
    useful_length_m: 3.1,
    allows_long_items: false,
    restricted_to_crateus: true,
    tipo_carroceria: 'Carroceria Aberta (Grade Baixa)',
  },
];

export const VehiclesView: React.FC = () => {
  const [vehicles, setVehicles] = useState<VehicleCard[]>(DEFAULT_FLEET);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadVehicles = async () => {
      setLoading(true);
      try {
        const data = await api.fetchVehicles();
        if (data && data.length > 0) {
          setVehicles(
            data.map((v) => ({
              ...v,
              tipo_carroceria: 'Carroceria Aberta (Grade Baixa)',
            }))
          );
        }
      } catch {
        // Fallback silencioso para DEFAULT_FLEET
      } finally {
        setLoading(false);
      }
    };
    loadVehicles();
  }, []);

  return (
    <div className="max-w-5xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      <div className="text-center space-y-1">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Frota Operacional de Expedição
        </h1>
        <p className="text-sm text-slate-500">
          Frota oficial Nobre Lar composta por 4 veículos de carroceria aberta (grade baixa).
        </p>
      </div>

      {loading && (
        <div className="flex justify-center p-8">
          <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {vehicles.map((v) => (
          <div
            key={v.id}
            className="border border-amber-400 bg-white rounded-2xl p-6 shadow-sm hover:shadow transition space-y-4"
          >
            <div className="flex items-center justify-between border-b border-amber-100 pb-3">
              <div className="flex items-center gap-2.5">
                <div className="w-9 h-9 rounded-xl bg-amber-100 text-amber-900 flex items-center justify-center font-bold">
                  <Truck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="font-bold text-slate-900 text-base">{v.name}</h3>
                  <span className="text-xs font-mono text-amber-700 font-semibold">
                    Placa: {v.plate}
                  </span>
                </div>
              </div>

              <span className="bg-slate-100 text-slate-800 text-[11px] font-bold px-2.5 py-1 rounded-md">
                {v.tipo_carroceria}
              </span>
            </div>

            {/* Capacidades Técnicas */}
            <div className="grid grid-cols-3 gap-2 bg-slate-50 p-3 rounded-xl text-center">
              <div>
                <span className="text-[10px] text-slate-400 block">Capacidade Carga</span>
                <span className="text-sm font-bold text-slate-800 font-mono">
                  {v.capacity_kg.toLocaleString('pt-BR')} kg
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Volume Útil</span>
                <span className="text-sm font-bold text-slate-800 font-mono">
                  {v.useful_volume_m3.toFixed(1)} m³
                </span>
              </div>
              <div>
                <span className="text-[10px] text-slate-400 block">Comprimento Útil</span>
                <span className="text-sm font-bold text-slate-800 font-mono">
                  {v.useful_length_m.toFixed(1)} m
                </span>
              </div>
            </div>

            {/* Regras Operacionais e Restrições */}
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                {v.allows_long_items ? (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span className="text-slate-700">
                      Permite transporte de <strong>peças lineares de 6m</strong> (tubulações/ferros).
                    </span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span className="text-slate-500">
                      Não comporta itens lineares de 6 metros.
                    </span>
                  </>
                )}
              </div>

              <div className="flex items-center gap-2">
                {v.restricted_to_crateus ? (
                  <>
                    <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                    <span className="text-slate-700">
                      Operação <strong>restrita ao perímetro urbano de Crateús</strong> e distritos.
                    </span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span className="text-slate-700">
                      <strong>Intermunicipal livre</strong>: opera em todos os eixos rodoviários.
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
