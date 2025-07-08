from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from decimal import Decimal

from habitaciones.models import Habitacion  # Importar desde habitaciones
from usuarios.models import Usuario  # Importar desde usuarios
from personal.models import Administrador  # Importar desde personal

class TipoReserva(models.Model):
    id_tipo_reserva = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    requiere_presencia = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'tipo_reserva'

class EstadoReserva(models.Model):
    id_estado_reserva = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    es_final = models.BooleanField(default=False)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'estado_reserva'

class Reserva(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    codigo_habitacion = models.ForeignKey(Habitacion, on_delete=models.PROTECT)
    usuario_admin = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='reservas_administradas')
    id_tipo_reserva = models.ForeignKey(TipoReserva, on_delete=models.PROTECT)
    id_estado_reserva = models.ForeignKey(EstadoReserva, on_delete=models.PROTECT, default=1)
    
    # Fechas y tiempos
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    fecha_checkin_programado = models.DateTimeField()
    fecha_checkout_programado = models.DateTimeField()
    fecha_checkin_real = models.DateTimeField(blank=True, null=True)
    fecha_checkout_real = models.DateTimeField(blank=True, null=True)
    
    # Información comercial
    numero_huespedes = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    precio_noche = models.DecimalField(max_digits=10, decimal_places=2)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    descuento_aplicado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Nuevo campo
    TIPO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('yape', 'Yape'),
        ('plin', 'Plin'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
    ]
    pago = models.CharField(max_length=20, choices=TIPO_PAGO_CHOICES, default='efectivo')

    # Campos calculados (se gestionarán a nivel de aplicación)

    @property
    def descuento(self):
        # Ahora retorna el descuento fijo guardado
        return self.descuento_aplicado
    
    @property
    def total_noches(self):
        noches = (self.fecha_checkout_programado.date() - self.fecha_checkin_programado.date()).days
        return max(noches, 1)
    
    @property
    def subtotal(self):
        return Decimal(self.precio_noche) * self.total_noches

    @property
    def total_pagar(self):
        return self.subtotal - Decimal(self.descuento_aplicado) + Decimal(self.impuestos)
    
    # Información adicional
    observaciones = models.TextField(blank=True, null=True)
    motivo_cancelacion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.id_tipo_reserva.requiere_presencia and not self.usuario_admin:
            from django.core.exceptions import ValidationError
            raise ValidationError('Las reservas presenciales deben tener un administrador asignado.')

    def __str__(self):
        return f"Reserva #{self.id}"

    def cancelar(self, motivo=None):
        from reservas.models import EstadoReserva
        from habitaciones.models import EstadoHabitacion
        from django.utils import timezone

        if self.id_estado_reserva.pk == 1:  # Pendiente
            pass  # Se puede cancelar
        elif self.id_estado_reserva.pk == 2 and self.codigo_habitacion.id_estado.pk == 3:  # Confirmada y Reservada
            pass  # Se puede cancelar
        else:
            raise ValueError("Solo se pueden cancelar reservas pendientes o confirmadas con habitación reservada.")

        estado_cancelada = EstadoReserva.objects.get(pk=3)  # Cancelada
        self.id_estado_reserva = estado_cancelada
        if motivo:
            self.motivo_cancelacion = motivo

        # Si la habitación estaba reservada, la marcamos como disponible
        if self.codigo_habitacion.id_estado.pk == 3:  # Reservada
            estado_disponible = EstadoHabitacion.objects.get(pk=1)  # Disponible
            self.codigo_habitacion.id_estado = estado_disponible
            self.codigo_habitacion.save()

        self.save()

    def check_in(self):
        """Realiza el check-in: cambia habitación a Ocupada y registra fecha real"""
        from habitaciones.models import EstadoHabitacion
        from django.utils import timezone
        
        # Solo permitir check-in si la reserva está confirmada
        if self.id_estado_reserva.pk != 2:  # No está confirmada
            raise ValueError("Solo se puede hacer check-in de reservas confirmadas")
        
        estado_ocupada = EstadoHabitacion.objects.get(pk=2)  # Ocupada
        self.codigo_habitacion.id_estado = estado_ocupada
        self.codigo_habitacion.save()
        
        self.fecha_checkin_real = timezone.now()
        self.save()

    def check_out(self):
        """Realiza el check-out: cambia habitación a Limpieza y reserva a Finalizada"""
        from habitaciones.models import EstadoHabitacion
        from reservas.models import EstadoReserva
        from django.utils import timezone
        
        # Solo permitir check-out si hay check-in registrado
        if not self.fecha_checkin_real:
            raise ValueError("No se puede hacer check-out sin check-in previo")
        
        estado_limpieza = EstadoHabitacion.objects.get(pk=5)  # Limpieza
        estado_finalizada = EstadoReserva.objects.get(pk=4)  # Finalizada
        
        self.codigo_habitacion.id_estado = estado_limpieza
        self.codigo_habitacion.save()
        
        self.id_estado_reserva = estado_finalizada
        self.fecha_checkout_real = timezone.now()
        self.save()

    def confirmar(self):
        from reservas.models import EstadoReserva
        from habitaciones.models import EstadoHabitacion
        from django.db.models import Q

        if self.id_estado_reserva.pk != 1:  # No está pendiente
            raise ValueError("Solo se pueden confirmar reservas pendientes")

        # Validar solapamiento de reservas confirmadas u ocupadas
        solapada = Reserva.objects.filter(
            codigo_habitacion=self.codigo_habitacion,
            id_estado_reserva__nombre__in=['Confirmada', 'Ocupada'],
            fecha_checkin_programado__lt=self.fecha_checkout_programado,
            fecha_checkout_programado__gt=self.fecha_checkin_programado
        ).exclude(pk=self.pk).exists()
        if solapada:
            raise ValueError("Ya existe una reserva confirmada u ocupada para esta habitación en el rango de fechas seleccionado.")

        estado_confirmada = EstadoReserva.objects.get(pk=2)  # Confirmada
        estado_reservada = EstadoHabitacion.objects.get(pk=3)  # Reservada

        self.id_estado_reserva = estado_confirmada
        self.codigo_habitacion.id_estado = estado_reservada
        self.codigo_habitacion.save()
        self.save()

        if hasattr(self.usuario, 'rol') and self.usuario.rol == 'HUESPED':
            self.usuario.total_visitas = getattr(self.usuario, 'total_visitas', 0) + 1
            self.usuario.save()

    def finalizar_limpieza(self):
        """Marca la habitación como disponible después de la limpieza"""
        from habitaciones.models import EstadoHabitacion
        from django.utils import timezone
        
        if self.codigo_habitacion.id_estado.pk == 5:  # En limpieza
            estado_disponible = EstadoHabitacion.objects.get(pk=1)  # Disponible
            self.codigo_habitacion.id_estado = estado_disponible
            self.codigo_habitacion.fecha_ultima_limpieza = timezone.now()
            self.codigo_habitacion.save()

    class Meta:
        db_table = 'reserva'
        indexes = [
            models.Index(fields=['codigo_habitacion'], name='idx_reserva_habitacion'),
            models.Index(fields=['usuario'], name='idx_reserva_huesped'),
            models.Index(fields=['usuario_admin'], name='idx_reserva_admin'),
            models.Index(fields=['fecha_checkin_programado', 'fecha_checkout_programado'], name='idx_reserva_fechas'),
            models.Index(fields=['id_estado_reserva'], name='idx_reserva_estado'),
            models.Index(fields=['id_tipo_reserva'], name='idx_reserva_tipo'),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(fecha_checkout_programado__gt=models.F('fecha_checkin_programado')),
                name='chk_fechas_validas'
            ),
            models.CheckConstraint(
                check=models.Q(precio_noche__gt=0),
                name='chk_precio_positivo'
            ),
        ]

class HistorialReserva(models.Model):
    huesped = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='historial_reservas')  # Solo usuarios con rol HUESPED
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='historiales')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_reserva'
        verbose_name = 'Historial de Reserva'
        verbose_name_plural = 'Historiales de Reserva'

    def __str__(self):
        return f"Historial de {self.huesped} - Reserva {self.reserva.id}"
