from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from habitaciones.models import Habitacion  # Importar desde habitaciones
from huespedes.models import Huesped  # Importar desde huespedes
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
    codigo_habitacion = models.ForeignKey(Habitacion, on_delete=models.PROTECT)
    dni_huesped = models.ForeignKey(Huesped, on_delete=models.PROTECT)
    dni_administrador = models.ForeignKey(Administrador, on_delete=models.PROTECT, null=True, blank=True)
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
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    impuestos = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Campos calculados (se gestionarán a nivel de aplicación)
    @property
    def total_noches(self):
        return (self.fecha_checkout_programado - self.fecha_checkin_programado).days
    
    @property
    def subtotal(self):
        return self.precio_noche * self.total_noches
    
    @property
    def total_pagar(self):
        return self.subtotal - self.descuento + self.impuestos
    
    # Información adicional
    observaciones = models.TextField(blank=True, null=True)
    motivo_cancelacion = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        super().clean()
        if self.id_tipo_reserva.requiere_presencia and not self.dni_administrador:
            from django.core.exceptions import ValidationError
            raise ValidationError('Las reservas presenciales deben tener un administrador asignado.')

    def __str__(self):
        return f"Reserva #{self.id}"

    class Meta:
        db_table = 'reserva'
        indexes = [
            models.Index(fields=['codigo_habitacion'], name='idx_reserva_habitacion'),
            models.Index(fields=['dni_huesped'], name='idx_reserva_huesped'),
            models.Index(fields=['dni_administrador'], name='idx_reserva_admin'),
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
    huesped = models.ForeignKey(Huesped, on_delete=models.CASCADE, related_name='historial_reservas')
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='historiales')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'historial_reserva'
        verbose_name = 'Historial de Reserva'
        verbose_name_plural = 'Historiales de Reserva'

    def __str__(self):
        return f"Historial de {self.huesped} - Reserva {self.reserva.id}"
