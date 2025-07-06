from rest_framework import serializers
from .models import Reserva, HistorialReserva
from usuarios.models import Usuario

class ReservaSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    usuario_admin = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), required=False, allow_null=True)

    total_noches = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    total_pagar = serializers.ReadOnlyField()

    class Meta:
        model = Reserva
        fields = [
            'id', 'codigo_habitacion', 'usuario', 'usuario_admin',
            'id_tipo_reserva', 'id_estado_reserva', 'fecha_checkin_programado',
            'fecha_checkout_programado', 'numero_huespedes', 'precio_noche',
            'descuento', 'impuestos', 'observaciones',
            # Campos calculados
            'total_noches', 'subtotal', 'total_pagar'
        ]

    def validate(self, data):
        usuario = data.get('usuario')
        usuario_admin = data.get('usuario_admin')
        tipo_reserva = data.get('id_tipo_reserva')
        codigo_habitacion = data.get('codigo_habitacion')
        numero_huespedes = data.get('numero_huespedes')
        fecha_checkin = data.get('fecha_checkin_programado')
        fecha_checkout = data.get('fecha_checkout_programado')
        # Validar rol de usuario
        if usuario and usuario.rol != 'HUESPED':
            raise serializers.ValidationError('El usuario debe tener rol HUESPED.')
        if usuario_admin and usuario_admin.rol != 'ADMIN':
            raise serializers.ValidationError('El usuario_admin debe tener rol ADMIN.')
        # Validar que si el tipo de reserva es presencial (id_tipo_reserva=1), se requiera administrador
        if tipo_reserva and getattr(tipo_reserva, 'id_tipo_reserva', None) == 1 and not usuario_admin:
            raise serializers.ValidationError('Las reservas presenciales deben tener un administrador asignado.')
        # Validar que el número de huéspedes no supere la capacidad máxima de la habitación
        if codigo_habitacion and numero_huespedes:
            capacidad_maxima = codigo_habitacion.id_tipo.capacidad_maxima
            if numero_huespedes > capacidad_maxima:
                raise serializers.ValidationError(f'El número de huéspedes ({numero_huespedes}) supera la capacidad máxima de la habitación ({capacidad_maxima}).')
        # Validar que el usuario no tenga ya una reserva para la misma habitación y fechas solapadas
        if usuario and codigo_habitacion and fecha_checkin and fecha_checkout:
            existe = Reserva.objects.filter(
                usuario=usuario,
                codigo_habitacion=codigo_habitacion,
                id_estado_reserva__nombre__in=['Pendiente', 'Confirmada', 'Ocupada'],
                fecha_checkin_programado__lt=fecha_checkout,
                fecha_checkout_programado__gt=fecha_checkin
            ).exists()
            if existe:
                raise serializers.ValidationError(
                    "Ya tienes una reserva para esta habitación en el rango de fechas seleccionado."
                )
        return data

class HistorialReservaSerializer(serializers.ModelSerializer):
    reserva = ReservaSerializer(read_only=True)
    fecha = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = HistorialReserva
        fields = ['reserva', 'fecha']