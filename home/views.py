from django.shortcuts import render,HttpResponse
import csv
from datetime import datetime
from django.core.exceptions import ValidationError
from .models import Delivery
from django.db.models import Avg
from geopy.distance import geodesic
import networkx as nx

def home(request):
    # Crear una lista para almacenar solo las conexiones de cada entrega
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

    # Calcular estadísticas clave
    total_deliveries = deliveries_qs.count()
    punctuality_rate = (deliveries_qs.filter(delivery_time__lte=30).count() / total_deliveries * 100) if total_deliveries > 0 else 0
    general_delays = (deliveries_qs.filter(delivery_time__gt=30).count() / total_deliveries * 100) if total_deliveries > 0 else 0
    performance_score = deliveries_qs.aggregate(Avg('agent_rating'))['agent_rating__avg']

    context = {
        'map_center': {'lat': map_center['avg_lat'], 'lng': map_center['avg_lng']},
        'deliveries': deliveries_data,
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
