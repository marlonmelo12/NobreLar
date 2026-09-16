/**
 * Parser de CSV de Pedidos da Nobre Lar e Dados de Demonstração
 */
import { DecoupledOrderInput } from '../types/dispatch';

export const DEMO_CSV_CONTENT = `Pedido;Data;Vendedor;Cliente;Cidade;Endereco;Valor_Pedido;Situacao_CSV_Entrega;Itens_Resumo
L1260901;16/09/2026;Vendedor CD;Construtora Vale do Poty;CRATEUS;Rua Dom Pedro II, 450, Centro, Crateús - CE;R$ 3.850,00;URGENTE;21503 - CIMENTO POTY TODAS OBRAS 50KG (18,00 SC) | 21246 - PISO CERBRAS IPANEMA CINZA 46 X 46 (15,00 CX) | 14900 - ARGAMASSA VARANDAS E QUINTAIS 15KG (10,00 SC)
L1260902;16/09/2026;Vendedor CD;Marcenaria e Artefatos São José;CRATEUS;Rua José Coriolano, 890, São José, Crateús - CE;R$ 2.950,00;NORMAL;12185 - CX. DAGUA BAKOF 1000L C/TMP (2,00 UN) | 21243 - PISO CERBRAS IPANEMA BEGE 46 X 46 (12,00 CX) | 17170 - LATEX FORTEX BRANCO GELO 15L (4,00 UN)
L1260903;16/09/2026;Vendedor CD;Comercial Sertão da Construção;TAMBORIL;Rua Cel. Oliveira, 350, Centro, Tamboril - CE;R$ 7.850,00;URGENTE;21503 - CIMENTO POTY TODAS OBRAS 50KG (45,00 SC) | 24606 - PISO POINTER GIOIA ORO 60 X 60 (25,00 CX) | 14900 - ARGAMASSA VARANDAS E QUINTAIS 15KG (25,00 SC)
L1260904;16/09/2026;Vendedor CD;Depósito Nova Russas Cimentos;NOVA RUSSAS;Av. Leonardo Araújo, 1120, Centro, Nova Russas - CE;R$ 6.400,00;NORMAL;12185 - CX. DAGUA BAKOF 1000L C/TMP (3,00 UN) | 21503 - CIMENTO POTY TODAS OBRAS 50KG (20,00 SC) | 21246 - PISO CERBRAS IPANEMA CINZA 46 X 46 (15,00 CX)
L1260905;16/09/2026;Vendedor CD;Casa & Construção Ipaporanga;IPAPORANGA;Rua Franklin José Vieira, 140, Centro, Ipaporanga - CE;R$ 6.800,00;URGENTE;21503 - CIMENTO POTY TODAS OBRAS 50KG (40,00 SC) | 21246 - PISO CERBRAS IPANEMA CINZA 46 X 46 (30,00 CX) | 14900 - ARGAMASSA VARANDAS E QUINTAIS 15KG (20,00 SC)
L1260906;16/09/2026;Vendedor CD;Depósito Poranga Materiais;PORANGA;Av. Epitácio Pinho, 510, Centro, Poranga - CE;R$ 5.900,00;NORMAL;21503 - CIMENTO POTY TODAS OBRAS 50KG (30,00 SC) | 24606 - PISO POINTER GIOIA ORO 60 X 60 (20,00 CX) | 12185 - CX. DAGUA BAKOF 1000L C/TMP (2,00 UN)
L1260907;16/09/2026;Vendedor CD;Mega Construtora Independência;INDEPENDENCIA;Rua Cel. Raimundo de Oliveira, 205, Centro, Independência - CE;R$ 8.200,00;URGENTE;21503 - CIMENTO POTY TODAS OBRAS 50KG (50,00 SC) | 21243 - PISO CERBRAS IPANEMA BEGE 46 X 46 (35,00 CX) | 8608 - ARGAMASSA VOTOMASSA ACII 15KG (25,00 SC)
L1260908;16/09/2026;Vendedor CD;Comercial Ferreira & Filhos;INDEPENDENCIA;Av. 7 de Setembro, 880, Independência - CE;R$ 4.500,00;NORMAL;12185 - CX. DAGUA BAKOF 1000L C/TMP (3,00 UN) | 17170 - LATEX FORTEX BRANCO GELO 15L (10,00 UN) | 14900 - ARGAMASSA VARANDAS E QUINTAIS 15KG (15,00 SC)
L1260909;16/09/2026;Vendedor CD;Engenharia e Reformas Rio Poty;CRATEUS;Rua Cel. Zezé, 610, São Vicente, Crateús - CE;R$ 3.200,00;NORMAL;21503 - CIMENTO POTY TODAS OBRAS 50KG (20,00 SC) | 21246 - PISO CERBRAS IPANEMA CINZA 46 X 46 (15,00 CX) | 12532 - ARGAMASSA ACIII QUARTZOLIT-15KG (15,00 SC)
L1260910;16/09/2026;Vendedor CD;Comércio e Construção Buriti;BURITI DOS MONTES;Av. Principal, 100, Centro, Buriti dos Montes - CE;R$ 7.100,00;URGENTE;21503 - CIMENTO POTY TODAS OBRAS 50KG (40,00 SC) | 24606 - PISO POINTER GIOIA ORO 60 X 60 (25,00 CX) | 12185 - CX. DAGUA BAKOF 1000L C/TMP (2,00 UN)`;

/**
 * Limpa string de valor monetário (ex: R$ 3.850,00 -> 3850.00)
 */
function parseCurrency(valStr: string | number): number {
  if (typeof valStr === 'number') return valStr;
  if (!valStr) return 0;
  const s = valStr.replace('R$', '').trim();
  const normalized = s.replace(/\./g, '').replace(',', '.');
  const n = parseFloat(normalized);
  return isNaN(n) ? 0 : n;
}

/**
 * Faz o parse da string de itens concatenados (ex: "21503 - CIMENTO POTY 50KG (18,00 SC) | 21246 - PISO...")
 */
function parseItensResumo(rawStr: string): DecoupledOrderInput['itens'] {
  if (!rawStr) return [];
  const tokens = rawStr.split('|');
  const items: DecoupledOrderInput['itens'] = [];

  const regex = /^\s*(\d+)\s*-\s*(.*?)\s*\(([\d.,]+)\s*([A-Za-z0-9]+)\)\s*$/;

  for (const t of tokens) {
    const trimmed = t.trim();
    if (!trimmed) continue;
    const match = trimmed.match(regex);
    if (match) {
      const codigo = match[1].trim();
      const descricao = match[2].trim();
      const qtdStr = match[3].replace(/\./g, '').replace(',', '.');
      const unidade = match[4].trim().toUpperCase();
      const quantidade = parseFloat(qtdStr) || 1.0;

      items.push({
        codigo,
        descricao,
        quantidade,
        unidade,
        preco_unitario: 50.0,
      });
    } else {
      // Formato livre sem código ou unidade
      items.push({
        codigo: '00000',
        descricao: trimmed,
        quantidade: 1.0,
        unidade: 'UN',
        preco_unitario: 50.0,
      });
    }
  }

  return items;
}

/**
 * Divide uma linha CSV respeitando aspas
 */
function splitCsvLine(line: string, delimiter: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"' || char === "'") {
      inQuotes = !inQuotes;
    } else if (char === delimiter && !inQuotes) {
      result.push(current.trim().replace(/^["']|["']$/g, ''));
      current = '';
    } else {
      current += char;
    }
  }
  result.push(current.trim().replace(/^["']|["']$/g, ''));
  return result;
}

/**
 * Converte texto CSV em lista tipada de pedidos DecoupledOrderInput
 */
export function parseCsvOrders(csvContent: string): DecoupledOrderInput[] {
  const lines = csvContent
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 0);

  if (lines.length < 2) return [];

  // Detecta delimitador (';' ou ',')
  const firstLine = lines[0];
  const delimiter = firstLine.includes(';') ? ';' : ',';

  const headers = splitCsvLine(firstLine, delimiter).map((h) =>
    h.toLowerCase().trim().replace(/_/g, '')
  );

  const orders: DecoupledOrderInput[] = [];

  for (let i = 1; i < lines.length; i++) {
    const cols = splitCsvLine(lines[i], delimiter);
    if (cols.length === 0 || !cols.some((c) => c.length > 0)) continue;

    const row: Record<string, string> = {};
    headers.forEach((h, idx) => {
      row[h] = cols[idx] || '';
    });

    const id =
      row['pedido'] ||
      row['id'] ||
      row['numeropedido'] ||
      row['codigopedido'] ||
      `L${i}`;

    const data = row['data'] || row['dataemissao'] || '16/09/2026';
    const vendedor = row['vendedor'] || 'Vendedor CD';
    const cliente = row['cliente'] || row['nomecliente'] || 'Cliente Consumidor';
    const cidade = (row['cidade'] || row['municipio'] || 'CRATEUS').toUpperCase();
    const endereco =
      row['endereco'] ||
      row['enderecocompleto'] ||
      `${cidade} - CE`;

    const valorRaw = row['valorpedido'] || row['valor'] || row['total'] || '0';
    const valor = parseCurrency(valorRaw);

    const sitRaw = (
      row['situacaocsventrega'] ||
      row['situacao'] ||
      row['status'] ||
      ''
    ).toUpperCase();

    const urgenteRaw = row['urgente'] || '';
    const isUrgente =
      sitRaw.includes('URGENTE') ||
      urgenteRaw.toLowerCase() === 'true' ||
      urgenteRaw === '1' ||
      urgenteRaw.toLowerCase() === 'sim';

    const rawItens = row['itensresumo'] || row['itens'] || row['produtos'] || '';
    const itens = parseItensResumo(rawItens);

    orders.push({
      id,
      data,
      vendedor,
      cliente,
      cidade,
      endereco,
      valor,
      urgente: isUrgente,
      situacao: isUrgente ? 'URGENTE' : 'NORMAL',
      itens:
        itens.length > 0
          ? itens
          : [
              {
                codigo: '01042',
                descricao: 'Material de Construção Geral',
                quantidade: 1,
                unidade: 'UN',
                preco_unitario: valor,
              },
            ],
    });
  }

  return orders;
}

/**
 * Pedidos de Demonstração pré-parseados para carregamento instantâneo
 */
export const DEMO_ORDERS: DecoupledOrderInput[] = parseCsvOrders(DEMO_CSV_CONTENT);
