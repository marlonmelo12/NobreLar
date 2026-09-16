"""Módulo de roteirização do Caixeiro Viajante (TSP) com Google OR-Tools Routing API.

Resolve a sequência ótima de paradas de entrega e gera o ordenamento LIFO
(Last In, First Out) de estivagem na doca do caminhão.
"""

from typing import List, Tuple, Dict, Any
import structlog
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
from app.services.distance_matrix import build_distance_matrix

logger = structlog.get_logger()


def solve_tsp(
    locations: List[Tuple[float, float]],
    depot_index: int = 0,
    roundtrip: bool = True,
    time_limit_sec: int = 5
) -> Dict[str, Any]:
    """Resolve o problema do caixeiro viajante a partir das coordenadas geográficas.

    locations: Lista de coordenadas (lat, lon). O índice 0 representa o CD Matriz em Crateús.
    roundtrip: Se True, o veículo retorna ao depósito; se False, encerra na última entrega.
    """
    n = len(locations)
    if n <= 1:
        return {
            "route": [0],
            "delivery_order": [],
            "lifo_loading_order": [],
            "total_distance_km": 0.0,
            "status": "TRIVIAL"
        }

    matrix = build_distance_matrix(locations)
    manager = pywrapcp.RoutingIndexManager(n, 1, depot_index)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_idx: int, to_idx: int) -> int:
        from_node = manager.IndexToNode(from_idx)
        to_node = manager.IndexToNode(to_idx)
        return matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    )
    search_params.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    )
    search_params.time_limit.seconds = time_limit_sec

    solution = routing.SolveWithParameters(search_params)

    if not solution:
        logger.warning("Solver TSP não convergiu a tempo. Utilizando sequência sequencial de paradas.")
        delivery_seq = list(range(1, n))
        return {
            "route": [0] + delivery_seq + ([0] if roundtrip else []),
            "delivery_order": delivery_seq,
            "lifo_loading_order": list(reversed(delivery_seq)),
            "total_distance_km": 0.0,
            "status": "FALLBACK"
        }

    index = routing.Start(0)
    route = []
    total_distance_meters = 0

    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)
        prev_idx = index
        index = solution.Value(routing.NextVar(index))
        total_distance_meters += routing.GetArcCostForVehicle(prev_idx, index, 0)

    if roundtrip:
        route.append(manager.IndexToNode(index))

    # Extrai a sequência de entregas (nós 1..n-1, excluindo o CD)
    delivery_stops = [node for node in route if node != 0]

    # Ordem LIFO (inversa da entrega para carregamento na doca)
    lifo_stops = list(reversed(delivery_stops))

    return {
        "route": route,
        "delivery_order": delivery_stops,
        "lifo_loading_order": lifo_stops,
        "total_distance_km": round(total_distance_meters / 1000.0, 2),
        "status": "OPTIMAL"
    }
