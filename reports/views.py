from django.shortcuts import render
from analysis.views import generate_chart
from home.models import Delivery
import networkx as nx
import matplotlib.pyplot as plt
from django.db.models import Avg
import networkx as nx
from routes.views import get_random_users

def build_flow_network(deliveries):
    """Construye una red de flujo a partir de las entregas."""
    graph = nx.DiGraph()
    for delivery in deliveries:
        source = f"Almacén {delivery.store_latitude, delivery.store_longitude}"
        destination = f"Destino {delivery.drop_latitude, delivery.drop_longitude}"
        capacity = delivery.delivery_time  # Usamos tiempo como capacidad
        graph.add_edge(source, destination, capacity=capacity)
    return graph

def reports_view(request):
    deliveries = Delivery.objects.all()[:50] 

    # Métricas
    total_deliveries = deliveries.count()
    avg_time = deliveries.aggregate(avg_time=Avg('delivery_time'))['avg_time'] or 0
    eco_score = 85
    on_time_rate = 95

    # Red de flujo
    flow_network = build_flow_network(deliveries)
    if flow_network.nodes:
        source = list(flow_network.nodes())[0]
        sink = list(flow_network.nodes())[-1]

        # Algoritmo de Ford-Fulkerson para flujo máximo
        max_flow, flow_dict = nx.maximum_flow(flow_network, source, sink)

        # Generar gráfico de la red
        fig = plt.figure(figsize=(10, 6))
        pos = nx.spring_layout(flow_network, seed=42)
        nx.draw(flow_network, pos, with_labels=True, node_size=500, node_color="lightblue", edge_color="gray")
        nx.draw_networkx_edge_labels(
            flow_network, pos, edge_labels={(u, v): f"{d['capacity']}" for u, v, d in flow_network.edges(data=True)}
        )
        chart = generate_chart(fig)
    else:
        max_flow = 0
        flow_dict = {}
        chart = None

    # Datos de entregas
    random_users = get_random_users()
    delivery_data = []
    for idx, delivery in enumerate(deliveries):
        user = random_users[idx % len(random_users)]
        driver_name = f"{user['name']['first']} {user['name']['last']}"
        delivery_data.append({
            'driver': driver_name,
            'start': f"{delivery.store_latitude}, {delivery.store_longitude}",
            'end': f"{delivery.drop_latitude}, {delivery.drop_longitude}",
            'time': delivery.delivery_time,
            'distance': f"{round(delivery.delivery_time * 0.5, 2)} km",
            'vehicle': delivery.vehicle,
        })

    context = {
        'total_deliveries': total_deliveries,
        'avg_time': round(avg_time, 2),
        'eco_score': eco_score,
        'on_time_rate': on_time_rate,
        'chart': chart,
        'delivery_data': delivery_data,
        'max_flow': max_flow,  # Flujo máximo calculado
    }

    return render(request, 'reports.html', context)
