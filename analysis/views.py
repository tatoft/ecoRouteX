from django.shortcuts import render
from django.db.models import Avg, Count
import matplotlib.pyplot as plt
import io
import base64
import networkx as nx
from home.models import Delivery

plt.switch_backend('Agg')  # Backend para gráficos sin interacción

def generate_chart(fig):
    """Convierte un gráfico Matplotlib en una imagen base64."""
    buffer = io.BytesIO()
    fig.savefig(buffer, format='png', dpi=80, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
    plt.close(fig)
    return image_base64

def build_graph(deliveries):
    """Construye un grafo dirigido con NetworkX a partir de las entregas."""
    graph = nx.DiGraph()
    for delivery in deliveries:
        store = (delivery.store_latitude, delivery.store_longitude)
        drop = (delivery.drop_latitude, delivery.drop_longitude)
        if store and drop and store != drop:  # Verificar nodos válidos
            distance = ((store[0] - drop[0])**2 + (store[1] - drop[1])**2)**0.5
            graph.add_edge(store, drop, weight=distance)
    return graph

def analytics_view(request):
    deliveries = Delivery.objects.only(
        'store_latitude', 'store_longitude', 'drop_latitude', 'drop_longitude', 'vehicle', 'traffic', 'delivery_time'
    )[:100]

    # 1. Distribución de Vehículos
    vehicle_distribution = deliveries.values('vehicle').annotate(count=Count('vehicle'))
    vehicles = [entry['vehicle'] for entry in vehicle_distribution]
    vehicle_counts = [entry['count'] for entry in vehicle_distribution]

    fig1 = plt.figure(figsize=(6, 4))
    plt.pie(vehicle_counts, labels=vehicles, autopct='%1.1f%%', startangle=90, textprops={'fontsize': 8})
    plt.title('Distribución de Tipos de Vehículos', fontsize=10)
    chart1 = generate_chart(fig1)

    # 2. Tráfico del Día
    traffic_distribution = deliveries.values('traffic').annotate(count=Count('traffic'))
    traffic_labels = [entry['traffic'] for entry in traffic_distribution]
    traffic_counts = [entry['count'] for entry in traffic_distribution]

    fig2 = plt.figure(figsize=(6, 4))
    plt.bar(traffic_labels, traffic_counts, color='red', edgecolor='black')
    plt.title('Tráfico del Día', fontsize=10)
    plt.xlabel('Estado de Tráfico', fontsize=8)
    plt.ylabel('Cantidad', fontsize=8)
    plt.xticks(rotation=45, fontsize=8)
    chart2 = generate_chart(fig2)

    # 3. Dijkstra para rutas más cortas
    graph = build_graph(deliveries)
    source = list(graph.nodes)[0] if graph.nodes else None
    shortest_paths = {}
    shortest_lengths = {}
    if source:
        shortest_paths = nx.single_source_dijkstra_path(graph, source, weight='weight')
        shortest_lengths = nx.single_source_dijkstra_path_length(graph, source, weight='weight')

    fig3 = plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(graph, seed=42)
    nx.draw(graph, pos, node_size=10, node_color="lightblue", edge_color="lightgray", alpha=0.7)
    for path in shortest_paths.values():
        edges = [(path[i], path[i + 1]) for i in range(len(path) - 1)]
        nx.draw_networkx_edges(graph, pos, edgelist=edges, edge_color='red', width=0.5)
    plt.title('Rutas Más Cortas con Dijkstra', fontsize=10)
    chart3 = generate_chart(fig3)

    peak_hour = "4 PM"  # Simulado para este ejemplo

    context = {
        'chart1': chart1,
        'chart2': chart2,
        'chart3': chart3,
        'peak_hour': peak_hour,
    }
    return render(request, 'analysis.html', context)
