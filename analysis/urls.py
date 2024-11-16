from django.urls import path
from . import views

urlpatterns = [
    path('analysis/', views.analytics_view, name='analysis'),
]