from django.shortcuts import render
from home.models import Delivery
from django.core.paginator import Paginator
import requests

# Diccionario de colores para los estados
TRAFFIC_CLASSES = {
    'high': 'bg-red-500 text-white',
    'jam': 'bg-orange-600 text-white',
    'low': 'bg-lightMint text-primaryGreen',
    'medium': 'bg-yellow-400 text-white',
    'default': 'bg-gray-500 text-white',
}

def get_random_users():
    """Función para obtener múltiples usuarios aleatorios desde la API de RandomUser.me"""
    try:
        response = requests.get('https://randomuser.me/api/?results=30')  # Obtener 30 usuarios aleatorios
        response.raise_for_status()  # Lanza una excepción si hay errores en la solicitud
        data = response.json()
        users = data['results']  # Extraer los usuarios generados
        return users
    except requests.RequestException as e:
        print(f"Error al obtener usuarios aleatorios: {e}")
        return None

def routes(request):
    # Obtener todas las entregas activas
    active_routes = Delivery.objects.all()

    # Obtener usuarios aleatorios para asignarlos a las rutas
    random_users = get_random_users()
    if random_users is None:
        random_users = [{'name': {'first': 'Desconocido', 'last': 'Repartidor'}}] * len(active_routes)  # Default si hay error

    # Asignar un repartidor aleatorio a cada ruta
    for idx, route in enumerate(active_routes):
        traffic_key = (route.traffic or '').strip().lower()  # Normalizamos el valor
        route.traffic_class = TRAFFIC_CLASSES.get(traffic_key, TRAFFIC_CLASSES['default'])

        # Asignar un nombre aleatorio
        user = random_users[idx % len(random_users)]  # Ciclar sobre los usuarios si son menos que las rutas
        route.driver_name = f"{user['name']['first']} {user['name']['last']}"

    # Paginación de las entregas activas
    paginator = Paginator(active_routes, 30)  # Mostramos 30 por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Pasar los datos a la plantilla
    return render(request, 'routes.html', {'page_obj': page_obj})
