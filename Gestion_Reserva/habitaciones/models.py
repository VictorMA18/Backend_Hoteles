from django.db import models

class TipoHabitacion(models.Model):
    id_tipo = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.TextField(blank=True, null=True)
    capacidad_maxima = models.IntegerField()
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'tipo_habitacion'

class EstadoHabitacion(models.Model):
    id_estado = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=100, blank=True, null=True)
    permite_reserva = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'estado_habitacion'

class Habitacion(models.Model):
    codigo = models.CharField(primary_key=True, max_length=10)
    numero_habitacion = models.CharField(max_length=10, unique=True)
    piso = models.IntegerField()
    id_tipo = models.ForeignKey(TipoHabitacion, on_delete=models.PROTECT)
    id_estado = models.ForeignKey(EstadoHabitacion, on_delete=models.PROTECT, default=1)
    precio_actual = models.DecimalField(max_digits=10, decimal_places=2)
    observaciones = models.TextField(blank=True, null=True)
    fecha_ultima_limpieza = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.numero_habitacion

    class Meta:
        db_table = 'habitacion'
        indexes = [
            models.Index(fields=['id_tipo'], name='idx_habitacion_tipo'),
            models.Index(fields=['id_estado'], name='idx_habitacion_estado'),
            models.Index(fields=['piso'], name='idx_habitacion_piso'),
        ]
