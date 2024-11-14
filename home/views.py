from django.shortcuts import render, HttpResponse
import csv
from datetime import datetime
from django.core.exceptions import ValidationError
from .models import Delivery
from django.db.models import Avg
import networkx as nx
from geopy.distance import geodesic

# A* Algorithm Implementation
def astar(graph, start, end):
    from heapq import heappop, heappush

    # Priority queue
    queue = []
    heappush(queue, (0, start))
    
    # Store distances
    costs = {start: 0}
    parents = {start: None}

    while queue:
        current_cost, current_node = heappop(queue)

        if current_node == end:
            # Reconstruct path
            path = []
            while current_node is not None:
                path.append(current_node)
                current_node = parents[current_node]
            return path[::-1]  # Reverse the path

        for neighbor, weight in graph[current_node].items():
            new_cost = current_cost + weight
            if neighbor not in costs or new_cost < costs[neighbor]:
                costs[neighbor] = new_cost
                priority = new_cost + heuristic(neighbor, end)
                heappush(queue, (priority, neighbor))
                parents[neighbor] = current_node

    return []  # No path found

# Heuristic function (using geodesic distance)
def heuristic(node, goal):
    return geodesic(node, goal).meters

# Django view

def home(request):
    # Query all deliveries with valid coordinates
    deliveries_qs = Delivery.objects.filter(store_latitude__isnull=False, drop_latitude__isnull=False)

    # Create a graph with stores and drops as nodes
    graph = {}
    for delivery in deliveries_qs:
        store_coords = (delivery.store_latitude, delivery.store_longitude)
        drop_coords = (delivery.drop_latitude, delivery.drop_longitude)

        if store_coords not in graph:
            graph[store_coords] = {}
        if drop_coords not in graph:
            graph[drop_coords] = {}

        # Use geodesic distance as weight
        distance = geodesic(store_coords, drop_coords).meters
        graph[store_coords][drop_coords] = distance
        graph[drop_coords][store_coords] = distance

    # Calculate routes using A*
    astar_routes = []
    for delivery in deliveries_qs:
        store_coords = (delivery.store_latitude, delivery.store_longitude)
        drop_coords = (delivery.drop_latitude, delivery.drop_longitude)

        # Calculate A* path
        path = astar(graph, store_coords, drop_coords)
        astar_routes.append({
            'path': path,
            'store': store_coords,
            'drop': drop_coords
        })

    # Calculate map center
    map_center = deliveries_qs.aggregate(
        avg_lat=Avg('store_latitude'),
        avg_lng=Avg('store_longitude')
    )

    # Statistics
    total_deliveries = deliveries_qs.count()
    punctuality_rate = (deliveries_qs.filter(delivery_time__lte=30).count() / total_deliveries * 100) if total_deliveries > 0 else 0
    general_delays = (deliveries_qs.filter(delivery_time__gt=30).count() / total_deliveries * 100) if total_deliveries > 0 else 0
    performance_score = deliveries_qs.aggregate(Avg('agent_rating'))['agent_rating__avg']

    context = {
        'map_center': {'lat': map_center['avg_lat'], 'lng': map_center['avg_lng']},
        'astar_routes': astar_routes,
        'punctuality_rate': round(punctuality_rate, 2),
        'general_delays': round(general_delays, 2),
        'performance_score': round(performance_score, 2) if performance_score is not None else 'N/A',
    }

    return render(request, 'home.html', context)

# Template Changes in JavaScript
# Use `astar_routes` from the context to plot the A* paths on the map
