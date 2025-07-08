from django.contrib import admin
from .models import Habitacion, EstadoHabitacion, TipoHabitacion

# Register your models here.

admin.site.register(Habitacion)
admin.site.register(EstadoHabitacion)
admin.site.register(TipoHabitacion)
