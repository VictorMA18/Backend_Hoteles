from django.urls import path
from .views import (
    listar_habitaciones,
    habitaciones_disponibles,
    cambiar_estado_habitacion,
    estados_habitacion,
    tipos_habitacion,
    habitaciones_dashboard_sse
)
from habitaciones import views

urlpatterns = [
    # Gestión de habitaciones
    path('listar/', listar_habitaciones, name='listar_habitaciones'),
    path('disponibles/', habitaciones_disponibles, name='habitaciones_disponibles'),
    path('<str:codigo_habitacion>/cambiar-estado/', cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    
    # Información de referencia
    path('estados/', estados_habitacion, name='estados_habitacion'),
    path('tipos/', tipos_habitacion, name='tipos_habitacion'),
    path('sse/habitaciones-dashboard/', habitaciones_dashboard_sse, name='habitaciones_dashboard_sse'),
    path('listar/', listar_habitaciones, name='listar_habitaciones'),
]
