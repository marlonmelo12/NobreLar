import React, { useEffect, useState } from 'react';
import { api } from '../../services/api';
import { Radio, MapPin, Scale, Box, Loader2 } from 'lucide-react';

interface AxisInfo {
  id: string;
  name: string;
  cities: string[];
  description: string;
}

const AXES_DATA: AxisInfo[] = [
  {
    id: 'eixo-0-crateus-urbano',
    name: 'Eixo 0: Crateús Urbano',
    cities: ['Crateús (Sede e bairros urbanos)'],
    description: 'Entregas locais urbanas atendidas prioritariamente por caminhões médios (Bongo/HR).',
  },
  {
    id: 'eixo-1-fronteira-pi',
    name: 'Eixo 1: Fronteira Piauí',
    cities: ['Buriti dos Montes (PI)', 'Barro Vermelho', 'Tucuns', 'Queimadas', 'Filomena'],
    description: 'Conexão interestadual Piauí/Ceará pela BR-226 com estradas vicinais e distritos.',
  },
  {
    id: 'eixo-2-sertao-central',
    name: 'Eixo 2: Sertão Central',
    cities: ['Tamboril', 'Nova Russas', 'Sucesso', 'Fazenda', 'Ibiapaba'],
    description: 'Rota polo comercial ao longo da CE-187 e CE-265, alta densidade de cerâmicas e cimento.',
  },
  {
    id: 'eixo-3-sul',
    name: 'Eixo 3: Eixo Sul',
    cities: ['Independência', 'São José', 'Adão', 'Vila Graça', 'Jatobá dos Umbelinos', 'São Gonçalo'],
    description: 'Acesso pela BR-226 Sul até Independência e malha vicinal dos distritos rurais.',
  },
  {
    id: 'eixo-4-norte-serra',
    name: 'Eixo 4: Norte e Serra',
    cities: ['Ipaporanga', 'Poranga', 'Ararendá', 'Vaca Morta', 'Curral Velho', 'Rosário'],
    description: 'Eixo montanhoso na Serra da Ibiapaba, alta declividade e curvas acentuadas.',
  },
  {
    id: 'eixo-5-inhamuns',
    name: 'Eixo 5: Inhamuns',
    cities: ['Novo Oriente', 'Quiterianópolis', 'Realejo', 'Santana', 'Monte Nebo', 'Santa Rosa'],
    description: 'Região dos Sertões dos Inhamuns, percursos longos ao longo da CE-187 Sul.',
  },
];

export const AxesView: React.FC = () => {
  const [profiles, setProfiles] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const loadProfiles = async () => {
      setLoading(true);
      try {
        const data = await api.fetchAxisProfiles();
        setProfiles(data);
      } catch {
        // Fallback silencioso
      } finally {
        setLoading(false);
      }
    };
    loadProfiles();
  }, []);

  return (
    <div className="max-w-5xl mx-auto py-8 px-6 space-y-8 animate-fadeIn">
      <div className="text-center space-y-1">
        <h1 className="text-2xl md:text-3xl font-bold text-slate-900 tracking-tight">
          Eixos Rodoviários Canônicos
        </h1>
        <p className="text-sm text-slate-500">
          Mapeamento dos 6 eixos logísticos da macrorregião atendida pelo CD Nobre Lar Crateús.
        </p>
      </div>

      {loading && (
        <div className="flex justify-center p-8">
          <Loader2 className="w-8 h-8 animate-spin text-amber-500" />
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {AXES_DATA.map((axis) => {
          const profile = profiles.find((p) => p.axis_id === axis.id);
          const limitante = profile?.predominant_limiting_resource || 'PESO';

          return (
            <div
              key={axis.id}
              className="border border-amber-400 bg-white rounded-2xl p-6 shadow-sm hover:shadow transition space-y-4"
            >
              <div className="flex items-center justify-between border-b border-amber-100 pb-3">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-lg bg-amber-100 text-amber-900 flex items-center justify-center font-bold">
                    <Radio className="w-4 h-4" />
                  </div>
                  <h3 className="font-bold text-slate-900 text-base">{axis.name}</h3>
                </div>

                <span
                  className={`text-[11px] font-bold px-2.5 py-0.5 rounded-full border ${
                    limitante === 'PESO'
                      ? 'bg-blue-50 text-blue-700 border-blue-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}
                >
                  Limitante: {limitante}
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed">
                {axis.description}
              </p>

              <div>
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-1.5 flex items-center gap-1">
                  <MapPin className="w-3 h-3 text-amber-600" />
                  Localidades Atendidas:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {axis.cities.map((city, idx) => (
                    <span
                      key={idx}
                      className="bg-slate-100 text-slate-700 text-[11px] px-2.5 py-1 rounded-md font-medium"
                    >
                      {city}
                    </span>
                  ))}
                </div>
              </div>

              {profile && profile.total_orders > 0 && (
                <div className="bg-slate-50 rounded-xl p-3 text-xs text-slate-600 flex items-center justify-between font-mono">
                  <div className="flex items-center gap-1">
                    <Scale className="w-3.5 h-3.5 text-slate-400" />
                    <span>{Math.round(profile.total_weight_kg)} kg</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Box className="w-3.5 h-3.5 text-slate-400" />
                    <span>{profile.total_volume_m3.toFixed(2)} m³</span>
                  </div>
                  <span className="text-slate-400">
                    Densidade: {profile.density_kg_m3} kg/m³
                  </span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
