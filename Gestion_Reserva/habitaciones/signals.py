from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Habitacion
from django.core.cache import cache

@receiver(post_save, sender=Habitacion)
def actualizar_cache_habitaciones(sender, instance, **kwargs):
    habitaciones = list(
        Habitacion.objects.select_related('id_estado', 'id_tipo')
        .values(
            'codigo',
            'numero_habitacion',
            'piso',
            'precio_actual',
            'id_estado__nombre',
            'id_estado__permite_reserva',
            'id_tipo__nombre'
        )
    )
    cache.set("habitaciones_dashboard", habitaciones)

