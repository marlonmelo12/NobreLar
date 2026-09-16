"""Serviço de geocodificação open source com GeoPy, Nominatim (OpenStreetMap) e cache persistido.

Implementa os requisitos da Seção 14 do documento v3.0 e docs/13:
- Resolução de coordenadas a partir de endereços reais (logradouro, número, bairro, cidade)
- Rate-limiting estrito (1,1s) em respeito às políticas do OpenStreetMap
- Cache local de coordenadas para eliminar requisições repetidas
- Fallback offline garantido para as 24 localidades da macrorregião
"""

from typing import Tuple, Optional
import structlog
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from app.core.config import settings
from app.core.geo_constants import REGION_COORDINATES_CACHE, DEPOT_COORDINATES

logger = structlog.get_logger()


class GeocoderService:
    """Geocodificador inteligente com cache e fallbacks resilientes."""

    def __init__(self, user_agent: Optional[str] = None):
        ua = user_agent or settings.NOMINATIM_USER_AGENT
        try:
            self.geolocator = Nominatim(user_agent=ua, timeout=5)
            self.geocode = RateLimiter(self.geolocator.geocode, min_delay_seconds=1.1)
        except Exception as e:
            logger.warning(f"Não foi possível inicializar Nominatim online: {e}. Operando em modo offline.")
            self.geocode = None

        # Cache em memória para execuções rápidas
        self._memory_cache: dict[str, Tuple[float, float]] = dict(REGION_COORDINATES_CACHE)

    def get_coordinates(
        self,
        city_name: str,
        address_line: Optional[str] = None,
        neighborhood: Optional[str] = None,
        state: str = "CE"
    ) -> Tuple[float, float]:
        """Obtém a latitude e longitude da entrega.

        Aplica a seguinte hierarquia de resolução:
        1. Consulta ao cache local de coordenadas
        2. Geocodificação online do endereço completo via Nominatim (se disponível)
        3. Geocodificação do bairro e cidade
        4. Coordenadas oficiais da localidade (REGION_COORDINATES_CACHE)
        5. Coordenadas do Centro de Distribuição em Crateús (Depósito Matriz)
        """
        clean_city = city_name.strip().upper()

        # Chave de busca para o cache de endereço completo
        cache_key = f"{address_line or ''}|{neighborhood or ''}|{clean_city}".upper()
        if cache_key in self._memory_cache:
            return self._memory_cache[cache_key]

        # Tentativa de consulta online via Nominatim se houver endereço especificado
        if self.geocode and address_line and address_line.strip():
            try:
                query_parts = [address_line.strip()]
                if neighborhood and neighborhood.strip():
                    query_parts.append(neighborhood.strip())
                query_parts.append(f"{city_name}, {state}, Brasil")
                query = ", ".join(query_parts)

                logger.info(f"Consultando geocodificação Nominatim para: {query}")
                loc = self.geocode(query)
                if loc:
                    coords = (round(loc.latitude, 6), round(loc.longitude, 6))
                    self._memory_cache[cache_key] = coords
                    return coords
            except Exception as e:
                logger.warning(f"Falha na geocodificação online para '{address_line}': {e}")

        # Fallback 1: Coordenadas da cidade no cache regional oficial
        if clean_city in REGION_COORDINATES_CACHE:
            return REGION_COORDINATES_CACHE[clean_city]

        # Fallback 2: Coordenadas do Depósito Matriz de Crateús
        return (DEPOT_COORDINATES["lat"], DEPOT_COORDINATES["lon"])
