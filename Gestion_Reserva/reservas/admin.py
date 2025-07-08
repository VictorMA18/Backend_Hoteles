from django.contrib import admin
from .models import Reserva, TipoReserva , EstadoReserva, HistorialReserva

admin.site.register(Reserva)
admin.site.register(TipoReserva)
admin.site.register(EstadoReserva)
admin.site.register(HistorialReserva)

