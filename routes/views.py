from django.shortcuts import render, get_object_or_404
import requests
from home.models import Delivery
from django.core.paginator import Paginator
from home.views import build_graph, find_optimal_route

# Diccionario de clases CSS para los estados de tráfico
TRAFFIC_CLASSES = {
    'high': 'bg-red-500 text-white',
    'jam': 'bg-orange-600 text-white',
    'low': 'bg-lightMint text-primaryGreen',
    'medium': 'bg-yellow-400 text-white',
    'default': 'bg-gray-500 text-white',
}

# Diccionario de etiquetas y colores para el detalle de tráfico
TRAFFIC_LEVELS = {
    'high': {'label': 'Atascado', 'color': 'bg-red-500'},
    'jam': {'label': 'Congestión severa', 'color': 'bg-orange-600'},
    'medium': {'label': 'Moderado', 'color': 'bg-yellow-400'},
    'low': {'label': 'Libre', 'color': 'bg-lightMint'},
    'default': {'label': 'Sin datos', 'color': 'bg-gray-500'},
}


def get_random_users():
    """
    Obtiene múltiples usuarios aleatorios desde la API RandomUser.me.
    """
    try:
        response = requests.get('https://randomuser.me/api/?results=30')  # 30 usuarios aleatorios
        response.raise_for_status()
        data = response.json()
        return data['results']
    except requests.RequestException as e:
        print(f"Error al obtener usuarios aleatorios: {e}")
        return [{'name': {'first': 'Desconocido', 'last': 'Repartidor'}}]  # Fallback


def routes(request):
    """
    Renderiza la lista de rutas activas con colores dinámicos en función del tráfico.
    """
    active_routes = Delivery.objects.all()
    random_users = get_random_users()  # Obtener usuarios aleatorios

    for idx, route in enumerate(active_routes):
        traffic_key = (route.traffic or '').strip().lower()
        route.traffic_class = TRAFFIC_CLASSES.get(traffic_key, TRAFFIC_CLASSES['default'])
        user = random_users[idx % len(random_users)]  # Asignar usuario cíclicamente
        route.driver_name = f"{user['name']['first']} {user['name']['last']}"

    paginator = Paginator(active_routes, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'routes.html', {'page_obj': page_obj})

def detail_route(request, order_id):
    """
    Renderiza el detalle de una ruta específica.
    """
    # Obtener la ruta específica
    route = get_object_or_404(Delivery, order_id=order_id)
    store = (route.store_latitude, route.store_longitude)
    drop = (route.drop_latitude, route.drop_longitude)

    if not store or not drop:
        return render(request, 'error.html', {'message': 'Coordenadas faltantes para esta entrega.'})

    # Obtener nivel de tráfico
    traffic_key = (route.traffic or '').strip().lower()
    traffic_level = TRAFFIC_LEVELS.get(traffic_key, TRAFFIC_LEVELS['default'])

    # Crear una lista de barras basada en el nivel de tráfico
    traffic_bars_count = {
        'low': 5,
        'medium': 10,
        'high': 15,
        'jam': 20,
        'default': 0
    }.get(traffic_key, 0)
    traffic_bars = list(range(traffic_bars_count))  # Generar lista de barras

    # Obtener datos de Google Directions API
    google_api_key = "AIzaSyA3x4I-dCjkwhEshAQlH5BOhQS1YY7ds5I"
    directions_url = f"https://maps.googleapis.com/maps/api/directions/json?origin={store[0]},{store[1]}&destination={drop[0]},{drop[1]}&mode=driving&key={google_api_key}"
    response = requests.get(directions_url)
    directions_data = response.json()

    # Extraer el tiempo estimado de la respuesta de la API
    if directions_data['status'] == 'OK':
        route_info = directions_data['routes'][0]['legs'][0]  # Primer segmento de la ruta
        estimated_time = route_info['duration']['text']  # Ejemplo: "2 horas 15 minutos"
        distance = route_info['distance']['text']  # Ejemplo: "10.5 km"
    else:
        estimated_time = "No disponible"
        distance = "No disponible"

    # Obtener usuarios aleatorios y asignar el nombre del conductor
    random_users = get_random_users()
    random_user_index = abs(hash(order_id)) % len(random_users)  # Usar hash absoluto para generar un índice válido
    driver = random_users[random_user_index]
    driver_full_name = f"{driver['name']['first']} {driver['name']['last']}"

    context = {
        'route': route,
        'traffic_level': traffic_level,
        'traffic_bars': traffic_bars,
        'store': {'lat': store[0], 'lng': store[1]},
        'drop': {'lat': drop[0], 'lng': drop[1]},
        'driver_name': driver_full_name,
        'estimated_time': estimated_time,  # Tiempo directamente desde la API
        'distance': distance,  # Distancia directamente desde la API
    }
    return render(request, 'detail_route.html', context)








