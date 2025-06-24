from django.db import models

from reservas.models import Reserva  # Importar desde reservas
from huespedes.models import Huesped  # Importar desde huespedes

class CuentaCobrar(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'),
        ('PAGADO', 'Pagado'),
        ('VENCIDO', 'Vencido'),
        ('CANCELADO', 'Cancelado'),
    ]
    
    id_cuenta = models.AutoField(primary_key=True)
    codigo_reserva = models.ForeignKey(Reserva, on_delete=models.PROTECT)
    dni_huesped = models.ForeignKey(Huesped, on_delete=models.PROTECT)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2)
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Campo calculado
    @property
    def saldo_pendiente(self):
        return self.monto_total - self.monto_pagado
    
    fecha_vencimiento = models.DateField()
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cuenta #{self.id_cuenta} - {self.estado}"

    class Meta:
        db_table = 'cuenta_cobrar'
        indexes = [
            models.Index(fields=['codigo_reserva'], name='idx_cuenta_reserva'),
            models.Index(fields=['dni_huesped'], name='idx_cuenta_huesped'),
            models.Index(fields=['estado'], name='idx_cuenta_estado'),
            models.Index(fields=['fecha_vencimiento'], name='idx_cuenta_vencimiento'),
        ]
