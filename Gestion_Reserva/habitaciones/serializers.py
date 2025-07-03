from rest_framework import serializers
from .models import Habitacion, TipoHabitacion, EstadoHabitacion


class TipoHabitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoHabitacion
        fields = ['id_tipo', 'nombre', 'descripcion', 'capacidad_maxima', 'precio_base']


class EstadoHabitacionSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoHabitacion
        fields = ['id_estado', 'nombre', 'descripcion', 'permite_reserva']


class HabitacionSerializer(serializers.ModelSerializer):
    tipo_info = TipoHabitacionSerializer(source='id_tipo', read_only=True)
    estado_info = EstadoHabitacionSerializer(source='id_estado', read_only=True)
    
    class Meta:
        model = Habitacion
        fields = [
            'codigo', 
            'numero_habitacion', 
            'piso', 
            'id_tipo', 
            'tipo_info',
            'id_estado', 
            'estado_info',
            'precio_actual', 
            'observaciones', 
            'fecha_ultima_limpieza',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Incluir información legible del estado y tipo
        representation['estado_nombre'] = instance.id_estado.nombre
        representation['tipo_nombre'] = instance.id_tipo.nombre
        representation['permite_reserva'] = instance.id_estado.permite_reserva
        return representation
