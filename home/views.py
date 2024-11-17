from django.shortcuts import render, HttpResponse
import csv
from datetime import datetime
from django.core.exceptions import ValidationError
from .models import Delivery
from django.db.models import Avg
from geopy.distance import geodesic

def calculate_haversine(coord1, coord2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la fórmula de Haversine.
    """
    return geodesic(coord1, coord2).kilometers

def astar(graph, start, end, heuristic_func):
    """
    Implementación del algoritmo A* para encontrar la ruta más corta.

    :param graph: Un diccionario que representa el grafo, donde las claves son nodos y los valores son diccionarios
                  de vecinos con sus pesos (ejemplo: {node: {neighbor: weight}}).
    :param start: Nodo inicial.
    :param end: Nodo destino.
    :param heuristic_func: Función heurística para estimar la distancia desde un nodo al destino.
    :return: Una lista con los nodos en la ruta más corta o None si no hay ruta.
    """
    from heapq import heappop, heappush

    open_set = []  # Usaremos una cola de prioridad para los nodos abiertos
    heappush(open_set, (0, start))  # (prioridad, nodo)

    came_from = {}  # Para reconstruir la ruta más corta
    g_score = {node: float('inf') for node in graph}  # Costo del inicio al nodo
    g_score[start] = 0

    f_score = {node: float('inf') for node in graph}  # Costo estimado (g + h)
    f_score[start] = heuristic_func(start, end)

    while open_set:
        current = heappop(open_set)[1]

        if current == end:
            # Reconstruir la ruta más corta
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            return path[::-1]  # Invertir el camino

        for neighbor, weight in graph[current].items():
            tentative_g_score = g_score[current] + weight

            if tentative_g_score < g_score[neighbor]:
                # Este camino al vecino es mejor que el anterior
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic_func(neighbor, end)

                if not any(neighbor == item[1] for item in open_set):
                    heappush(open_set, (f_score[neighbor], neighbor))

    return None  # No se encontró ruta

def build_graph(deliveries):
    """
    Construye un grafo basado en un diccionario para usar en el algoritmo A*.
    """
    graph = {}
    for delivery in deliveries:
        store = (delivery.store_latitude, delivery.store_longitude)
        drop = (delivery.drop_latitude, delivery.drop_longitude)

        if store not in graph:
            graph[store] = {}
        if drop not in graph:
            graph[drop] = {}

        distance = calculate_haversine(store, drop)
        graph[store][drop] = distance
        graph[drop][store] = distance  # Asumimos que es bidireccional

    return graph

def find_optimal_route(deliveries, start, end):
    """
    Encuentra la ruta más corta usando el algoritmo A*.
    """
    graph = build_graph(deliveries)
    return astar(graph, start, end, heuristic_func=calculate_haversine)

def home(request):
    deliveries_qs = Delivery.objects.filter(store_latitude__isnull=False, drop_latitude__isnull=False)

    # Calcular el centro del mapa basado en el promedio de las coordenadas de todas las entregas seleccionadas
    map_center = deliveries_qs.aggregate(
        avg_lat=Avg('store_latitude'),
        avg_lng=Avg('store_longitude')
    )

    # Preparar las conexiones (solo tienda -> destino para cada entrega)
    deliveries_data = []
    for delivery in deliveries_qs:
        deliveries_data.append({
            'store_latitude': delivery.store_latitude,
            'store_longitude': delivery.store_longitude,
            'drop_latitude': delivery.drop_latitude,
            'drop_longitude': delivery.drop_longitude
        })

    # Construir el grafo de rutas (una vez y reutilizable)
    graph = build_graph(deliveries_qs)

    # Optimización: no calcular rutas a menos que el usuario haga clic
    optimized_routes = []

    # Calcular estadísticas clave
    total_deliveries = deliveries_qs.count()
    punctuality_rate = (deliveries_qs.filter(delivery_time__lte=30).count() / total_deliveries * 100) if total_deliveries > 0 else 0
    general_delays = (deliveries_qs.filter(delivery_time__gt=30).count() / total_deliveries * 100) if total_deliveries > 0 else 0
    performance_score = deliveries_qs.aggregate(Avg('agent_rating'))['agent_rating__avg']

    context = {
        'map_center': {'lat': map_center['avg_lat'], 'lng': map_center['avg_lng']},
        'deliveries': deliveries_data,
        'optimized_routes': optimized_routes,  # Las rutas no se calculan hasta que se necesiten
        'punctuality_rate': round(punctuality_rate, 2),
        'general_delays': round(general_delays, 2),
        'performance_score': round(performance_score, 2) if performance_score is not None else 'N/A',
    }
    return render(request, 'home.html', context)
