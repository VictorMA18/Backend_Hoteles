from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Habitacion
from django.core.cache import cache

@receiver(post_save, sender=Habitacion)
def actualizar_cache_habitaciones(sender, instance, **kwargs):
    disponibles = list(
        Habitacion.objects.filter(id_estado__permite_reserva=True)
        .values('codigo', 'numero_habitacion', 'piso', 'precio_actual')
    )
    cache.set("habitaciones_disponibles", disponibles)
