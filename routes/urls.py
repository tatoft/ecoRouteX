from django.urls import path
from . import views

urlpatterns = [
    path('routes/', views.routes, name='routes'),
    path('routes/<str:order_id>/', views.detail_route, name='detail'),
]