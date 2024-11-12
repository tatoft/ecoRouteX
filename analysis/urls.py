from django.urls import path
from . import views

urlpatterns = [
    path('analysis/', views.routes, name='analysis'),
]