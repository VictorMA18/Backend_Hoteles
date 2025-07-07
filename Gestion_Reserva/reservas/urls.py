from django.urls import path
from .views import (
    crear_reserva, 
    listar_reservas,
    confirmar_reserva,
    cancelar_reserva,
    check_in_reserva,
    check_out_reserva,
    finalizar_limpieza_habitacion,
    historial_reservas_usuario,
    registrar_hospedaje_presencial,
    registrar_hospedaje_presencial_pendiente
)

urlpatterns = [
    # Gestión básica de reservas
    path('crear/', crear_reserva, name='crear_reserva'),
    path('listar/', listar_reservas, name='listar_reservas'),
    
    # Acciones de reserva (requieren ID)
    path('<int:reserva_id>/confirmar/', confirmar_reserva, name='confirmar_reserva'),
    path('<int:reserva_id>/cancelar/', cancelar_reserva, name='cancelar_reserva'),
    path('<int:reserva_id>/check-in/', check_in_reserva, name='check_in_reserva'),
    path('<int:reserva_id>/check-out/', check_out_reserva, name='check_out_reserva'),
    path('<int:reserva_id>/finalizar-limpieza/', finalizar_limpieza_habitacion, name='finalizar_limpieza'),
    path('hospedaje-presencial/', registrar_hospedaje_presencial, name='registrar_hospedaje_presencial'),
    path('hospedaje-presencial-pendiente/', registrar_hospedaje_presencial_pendiente, name='hospedaje_presencial_pendiente'),

    # Historial de reservas de un usuario específico
    path('historial/<str:dni>/', historial_reservas_usuario, name='historial_reservas_usuario'),
]