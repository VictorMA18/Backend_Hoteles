from django.urls import path
from .views import habitaciones_disponibles_sse

urlpatterns = [
    path("sse/habitaciones-disponibles/", habitaciones_disponibles_sse),
]
