from django.db import models

from huespedes.models import TipoDocumento  # Importar desde la app huespedes

class Administrador(models.Model):
    ROL_CHOICES = [
        ('ADMIN', 'Administrador'),
        ('RECEPCIONISTA', 'Recepcionista'),
        ('SUPERVISOR', 'Supervisor'),
    ]
    
    dni = models.CharField(primary_key=True, max_length=20)
    id_tipo_doc = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, default=1)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    celular = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, unique=True)
    username = models.CharField(max_length=50, unique=True)
    password_hash = models.CharField(max_length=255)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='RECEPCIONISTA')
    activo = models.BooleanField(default=True)
    ultimo_acceso = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username

    class Meta:
        db_table = 'administrador'
        indexes = [
            models.Index(fields=['username'], name='idx_admin_username'),
            models.Index(fields=['email'], name='idx_admin_email'),
            models.Index(fields=['rol'], name='idx_admin_rol'),
        ]
