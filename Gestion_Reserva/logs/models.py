from django.db import models

from reservas.models import Reserva  # Importar desde reservas
from personal.models import Administrador  # Importar desde personal

class AccionLog(models.Model):
    ACCION_CHOICES = [
        ('CREATE', 'Crear'),
        ('UPDATE', 'Actualizar'),
        ('DELETE', 'Eliminar'),
        ('CHECKIN', 'Check-in'),
        ('CHECKOUT', 'Check-out'),
        ('CANCEL', 'Cancelar'),
    ]
    
    id_accion = models.AutoField(primary_key=True)
    codigo_reserva = models.ForeignKey(Reserva, on_delete=models.SET_NULL, blank=True, null=True)
    dni_administrador = models.ForeignKey(Administrador, on_delete=models.PROTECT)
    accion = models.CharField(max_length=10, choices=ACCION_CHOICES)
    descripcion = models.TextField(blank=True, null=True)
    valores_anteriores = models.JSONField(blank=True, null=True)
    valores_nuevos = models.JSONField(blank=True, null=True)
    ip_address = models.CharField(max_length=45, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.accion} - {self.created_at}"

    class Meta:
        db_table = 'accion_log'
        indexes = [
            models.Index(fields=['codigo_reserva'], name='idx_log_reserva'),
            models.Index(fields=['dni_administrador'], name='idx_log_admin'),
            models.Index(fields=['created_at'], name='idx_log_fecha'),
            models.Index(fields=['accion'], name='idx_log_accion'),
        ]
