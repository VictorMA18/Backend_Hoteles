from django.urls import path
from .views import (
    listar_habitaciones,
    habitaciones_disponibles,
    cambiar_estado_habitacion,
    estados_habitacion,
    tipos_habitacion,
    buscar_disponibilidad,
    finalizar_limpieza,
    habitaciones_dashboard_sse
)

urlpatterns = [
    # Gestión de habitaciones
    path('listar/', listar_habitaciones, name='listar_habitaciones'),
    path('disponibles/', habitaciones_disponibles, name='habitaciones_disponibles'),
    path('buscar-disponibilidad/', buscar_disponibilidad, name='buscar_disponibilidad'),
    path('<str:codigo_habitacion>/cambiar-estado/', cambiar_estado_habitacion, name='cambiar_estado_habitacion'),
    path('<str:codigo_habitacion>/finalizar-limpieza/', finalizar_limpieza, name='finalizar_limpieza_habitacion'),
    
    # Información de referencia
    path('estados/', estados_habitacion, name='estados_habitacion'),
    path('tipos/', tipos_habitacion, name='tipos_habitacion'),
    path('sse/habitaciones-dashboard/', habitaciones_dashboard_sse, name='habitaciones_dashboard_sse'),
]
