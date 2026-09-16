"""Esquemas Pydantic v2 para a frota de veículos."""

from pydantic import BaseModel, Field, ConfigDict


class VehicleResponse(BaseModel):
    """Contrato de representação do veículo e suas restrições operacionais."""
    id: str = Field(..., description="Identificador único do veículo (ex: accelo-815-01)")
    name: str = Field(..., description="Nome comercial ou modelo do veículo")
    plate: str = Field(..., description="Placa oficial do veículo")
    capacity_kg: float = Field(..., description="Capacidade máxima útil em kg")
    useful_volume_m3: float = Field(..., description="Capacidade cúbica útil em m³ (com estivagem)")
    useful_length_m: float = Field(..., description="Comprimento útil da caçamba em metros")
    allows_long_items: bool = Field(..., description="Se comporta peças lineares de 6 metros")
    restricted_to_crateus: bool = Field(..., description="Se a atuação é restrita a Crateús e seus distritos")
    operates_intermunicipal: bool = Field(..., description="Se está autorizado para viagens a outras cidades")
    active: bool = Field(True, description="Se o veículo está ativo na frota operacional")

    model_config = ConfigDict(from_attributes=True)
