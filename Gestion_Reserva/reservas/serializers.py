from rest_framework import serializers
from .models import Reserva, HistorialReserva

class ReservaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reserva
        fields = [
            'id', 'codigo_habitacion', 'dni_huesped', 'dni_administrador',
            'id_tipo_reserva', 'id_estado_reserva', 'fecha_checkin_programado',
            'fecha_checkout_programado', 'numero_huespedes', 'precio_noche',
            'descuento', 'impuestos', 'observaciones'
        ]

    def validate(self, data):
        # Validar que si el tipo de reserva es presencial (id_tipo_reserva=1), se requiera administrador
        tipo_reserva = data.get('id_tipo_reserva')
        if tipo_reserva and getattr(tipo_reserva, 'id_tipo_reserva', None) == 1 and not data.get('dni_administrador'):
            raise serializers.ValidationError("Las reservas presenciales deben tener un administrador asignado.")
        return data

class HistorialReservaSerializer(serializers.ModelSerializer):
    reserva = ReservaSerializer(read_only=True)
    fecha = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = HistorialReserva
        fields = ['reserva', 'fecha']