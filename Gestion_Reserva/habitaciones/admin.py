from django.contrib import admin
from .models import TipoHabitacion, EstadoHabitacion, Habitacion

@admin.register(Habitacion)
class HabitacionAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'numero_habitacion', 'piso', 'id_tipo', 'id_estado', 'precio_actual')
    list_filter = ('id_tipo', 'id_estado', 'piso')
    search_fields = ('codigo', 'numero_habitacion')

admin.site.register(TipoHabitacion)
admin.site.register(EstadoHabitacion)

