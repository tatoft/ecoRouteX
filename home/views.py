from django.shortcuts import render, HttpResponse
import csv
from datetime import datetime
from django.core.exceptions import ValidationError
from .models import Delivery
from django.db.models import Avg
from geopy.distance import geodesic
import networkx as nx

def haversine_distance(coord1, coord2):
    """
    Calcula la distancia en kilómetros entre dos puntos geográficos usando la fórmula de Haversine.
    """
    return geodesic(coord1, coord2).kilometers

def build_graph(deliveries):
    """
    Construye un grafo utilizando NetworkX con las ubicaciones de las entregas.
    """
    graph = nx.Graph()

    # Añadir nodos y aristas para cada entrega
    for delivery in deliveries:
        store = (delivery.store_latitude, delivery.store_longitude)
        drop = (delivery.drop_latitude, delivery.drop_longitude)

        # Asegurar que cada nodo está en el grafo
        if store not in graph:
            graph.add_node(store)
        if drop not in graph:
            graph.add_node(drop)

        # Añadir una arista con el peso como la distancia entre los nodos
        distance = haversine_distance(store, drop)
        graph.add_edge(store, drop, weight=distance)

    return graph

def find_optimal_route(graph, start, end):
    """
    Calcula la ruta más óptima entre dos nodos usando el algoritmo de A*.
    """
    try:
        path = nx.astar_path(graph, start, end, heuristic=haversine_distance, weight='weight')
        return path
    except nx.NetworkXNoPath:
        return None

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

def import_csv_to_db():
    file_path = 'data/amazon_delivery.csv'  # Cambia esta ruta al archivo
    with open(file_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        deliveries = []
        for row in reader:
            try:
                delivery = Delivery(
                    order_id=row['Order_ID'],
                    agent_age=int(row['Agent_Age']),
                    agent_rating=float(row['Agent_Rating']) if row['Agent_Rating'] else None,
                    store_latitude=float(row['Store_Latitude']),
                    store_longitude=float(row['Store_Longitude']),
                    drop_latitude=float(row['Drop_Latitude']),
                    drop_longitude=float(row['Drop_Longitude']),
                    order_date=datetime.strptime(row['Order_Date'], '%Y-%m-%d').date(),
                    order_time=datetime.strptime(row['Order_Time'], '%H:%M:%S').time() if row['Order_Time'] else None,
                    pickup_time=datetime.strptime(row['Pickup_Time'], '%H:%M:%S').time() if row['Pickup_Time'] else None,
                    weather=row['Weather'] if row['Weather'] else None,
                    traffic=row['Traffic'],
                    vehicle=row['Vehicle'],
                    area=row['Area'],
                    delivery_time=int(row['Delivery_Time']),
                    category=row['Category'],
                )
                delivery.full_clean()  # Valida el objeto
                deliveries.append(delivery)
            except (ValueError, ValidationError) as e:
                print(f"Error en la fila: {row}, Error: {e}")
                continue

        # Inserta todos los registros válidos a la vez
        Delivery.objects.bulk_create(deliveries)
