
from django.shortcuts import render
from .models import Delivery

def home(request):
    # Obtener todas las entregas con coordenadas de tienda y destino
    deliveries = Delivery.objects.values('store_latitude', 'store_longitude', 'drop_latitude', 'drop_longitude')

    context = {
        'deliveries': list(deliveries),  # Convertir QuerySet a lista
    }
    return render(request, 'home.html', context)
