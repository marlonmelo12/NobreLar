/**
 * Cliente de API Desacoplado — NobreLOG IA
 * Comunicação direta com os endpoints REST da FastAPI.
 */

import {
  DecoupledDispatchResponse,
  TruckLoadResponse,
  DeliveryRouteResponse,
  DecoupledOrderInput,
} from '../types/dispatch';

const API_BASE_URL = (import.meta.env.VITE_API_URL as string) || 'http://localhost:8000';

class ApiService {
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Accept: 'application/json',
      ...(options.headers as Record<string, string>),
    };

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        let errorDetail = `Erro HTTP ${response.status}: ${response.statusText}`;
        try {
          const errorJson = await response.json();
          if (errorJson.detail) {
            errorDetail = typeof errorJson.detail === 'string' 
              ? errorJson.detail 
              : JSON.stringify(errorJson.detail);
          }
        } catch {
          // Mantém a mensagem genérica caso não seja JSON
        }
        throw new Error(errorDetail);
      }

      return (await response.json()) as T;
    } catch (err: unknown) {
      if (err instanceof Error) {
        throw err;
      }
      throw new Error('Falha de conexão com a API NobreLOG.');
    }
  }

  /**
   * Verifica a integridade e saúde do backend.
   */
  async checkHealth(): Promise<{ status: string; service: string }> {
    return this.request<{ status: string; service: string }>('/api/v1/health');
  }

  /**
   * Obtém os pedidos mock estruturados da Nobre Lar (30 pedidos).
   * Endpoint GET puro.
   */
  async fetchMockOrders(): Promise<DecoupledOrderInput[]> {
    return this.request<DecoupledOrderInput[]>('/api/v1/dispatch/mock-orders');
  }

  /**
   * Envia o lote JSON de pedidos faturados para processamento.
   * Endpoint ÚNICO POST.
   */
  async processOrders(
    pedidos: DecoupledOrderInput[],
    perfilOtimizacao = 'Equilibrado',
    tempoLimiteSegundos = 20.0
  ): Promise<DecoupledDispatchResponse> {
    return this.request<DecoupledDispatchResponse>('/api/v1/dispatch/orders', {
      method: 'POST',
      body: JSON.stringify({
        pedidos,
        perfil_otimizacao: perfilOtimizacao,
        tempo_limite_segundos: tempoLimiteSegundos,
      }),
    });
  }

  /**
   * Retorna os dados de Cargas no Caminhão (Carroceria Aberta + LIFO).
   * Endpoint GET puro.
   */
  async fetchTruckLoad(): Promise<TruckLoadResponse> {
    return this.request<TruckLoadResponse>('/api/v1/dispatch/truck-load');
  }

  /**
   * Retorna os dados do Roteiro de Entregas (TSP + Paradas + Cobrança).
   * Endpoint GET puro.
   */
  async fetchDeliveryRoute(): Promise<DeliveryRouteResponse> {
    return this.request<DeliveryRouteResponse>('/api/v1/dispatch/delivery-route');
  }

  /**
   * Retorna a visão consolidada em memória.
   * Endpoint GET puro.
   */
  async fetchConsolidatedSummary(): Promise<DecoupledDispatchResponse> {
    return this.request<DecoupledDispatchResponse>('/api/v1/dispatch/process-orders');
  }

  /**
   * Constrói a URL para download ou visualização do PDF do Mapa de Carregamento.
   */
  getLoadingSheetPdfUrl(tripId: string): string {
    return `${API_BASE_URL}/api/v1/dispatch/trips/${encodeURIComponent(tripId)}/pdf/loading-sheet`;
  }

  /**
   * Constrói a URL para download ou visualização do PDF do Roteiro de Entregas.
   */
  getDeliveryRoutePdfUrl(tripId: string): string {
    return `${API_BASE_URL}/api/v1/dispatch/trips/${encodeURIComponent(tripId)}/pdf/delivery-route`;
  }
}

export const api = new ApiService();
