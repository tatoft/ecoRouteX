from django.urls import path
from . import views

urlpatterns = [
    path('reports/', views.reports_view, name='reports'),
]