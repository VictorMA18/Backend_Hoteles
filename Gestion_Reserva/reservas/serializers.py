from rest_framework import serializers
from .models import Reserva, HistorialReserva
from usuarios.models import Usuario

class ReservaSerializer(serializers.ModelSerializer):
    usuario = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all())
    usuario_admin = serializers.PrimaryKeyRelatedField(queryset=Usuario.objects.all(), required=False, allow_null=True)
    
    total_noches = serializers.ReadOnlyField()
    subtotal = serializers.ReadOnlyField()
    total_pagar = serializers.ReadOnlyField()
    descuento = serializers.ReadOnlyField()
    pago = serializers.CharField()
    class Meta:
        model = Reserva
        fields = [
            'id', 'codigo_habitacion', 'usuario', 'usuario_admin',
            'id_tipo_reserva', 'id_estado_reserva', 'fecha_checkin_programado',
            'fecha_checkout_programado', 'numero_huespedes', 'precio_noche',
            'descuento', 'impuestos', 'observaciones', 'fecha_checkin_real', 'fecha_checkout_real',
            # Campos calculados
            'total_noches', 'subtotal', 'total_pagar', 'pago'
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
        if codigo_habitacion and codigo_habitacion.id_estado.nombre in ['Ocupada', 'Reservada', 'Limpieza']:
            raise serializers.ValidationError(
                f"No puedes reservar una habitación que está actualmente en estado '{codigo_habitacion.id_estado.nombre}'."
            )
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

    def create(self, validated_data):
        # Calcular descuento_aplicado según total_visitas del usuario
        from decimal import Decimal
        usuario = validated_data['usuario']
        precio_noche = validated_data['precio_noche']
        fecha_checkin = validated_data['fecha_checkin_programado']
        fecha_checkout = validated_data['fecha_checkout_programado']
        total_noches = (fecha_checkout.date() - fecha_checkin.date()).days
        total_noches = max(total_noches, 1)
        subtotal = precio_noche * total_noches
        if hasattr(usuario, 'total_visitas') and usuario.total_visitas >= 10:
            descuento_aplicado = subtotal * Decimal('0.15')    
        elif hasattr(usuario, 'total_visitas') and usuario.total_visitas >= 5:
            descuento_aplicado = subtotal * Decimal('0.10')
        else:
            descuento_aplicado = Decimal('0.00')
        validated_data['descuento_aplicado'] = descuento_aplicado
        return super().create(validated_data)

class ReservaDetalleSerializer(serializers.ModelSerializer):
    usuario_dni = serializers.CharField(source='usuario.dni', read_only=True)
    usuario_nombres = serializers.CharField(source='usuario.nombres', read_only=True)
    usuario_apellidos = serializers.CharField(source='usuario.apellidos', read_only=True)
    total_visitas = serializers.CharField(source='usuario.total_visitas', read_only=True)
    habitacion_numero = serializers.CharField(source='codigo_habitacion.numero_habitacion', read_only=True)
    habitacion_tipo = serializers.CharField(source='codigo_habitacion.id_tipo.nombre', read_only=True)
    habitacion_estado = serializers.CharField(source='codigo_habitacion.id_estado.nombre', read_only=True)
    pago = serializers.CharField()

    class Meta:
        model = Reserva
        fields = [
            'id',
            'codigo_habitacion',
            'habitacion_numero',
            'habitacion_tipo',
            'habitacion_estado',
            'usuario',
            'usuario_dni',
            'usuario_nombres',
            'usuario_apellidos',
            'usuario_admin',
            'id_tipo_reserva',
            'id_estado_reserva',
            'fecha_checkin_programado',
            'fecha_checkout_programado',
            'numero_huespedes',
            'precio_noche',
            'descuento',
            'impuestos',
            'observaciones',
            'fecha_checkin_real',
            'fecha_checkout_real',
            'total_noches',
            'total_visitas',
            'subtotal',
            'total_pagar',
            'pago'
        ]

class HistorialReservaSerializer(serializers.ModelSerializer):
    reserva = ReservaSerializer(read_only=True)
    fecha = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S")

    class Meta:
        model = HistorialReserva
        fields = ['reserva', 'fecha']