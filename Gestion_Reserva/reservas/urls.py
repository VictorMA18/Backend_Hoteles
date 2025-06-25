from django.urls import path
from .views import crear_reserva, historial_reservas_huesped

urlpatterns = [
    path('registrar/', crear_reserva, name='registrar_reserva'),
    path('historial/', historial_reservas_huesped, name='historial_reservas_huesped'),
]