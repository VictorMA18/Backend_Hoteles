from django.db import models
from django.core.exceptions import ValidationError

class TipoDocumento(models.Model):
    id_tipo_doc = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=30, unique=True)
    codigo = models.CharField(max_length=10, unique=True)
    longitud_minima = models.IntegerField(default=8)
    longitud_maxima = models.IntegerField(default=12)

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'tipo_documento'

class Huesped(models.Model):
    dni = models.CharField(primary_key=True, max_length=20, unique=True)
    id_tipo_doc = models.ForeignKey(
        TipoDocumento,
        on_delete=models.PROTECT,
        related_name='huespedes',
        verbose_name='Tipo de Documento'
    )
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    celular = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(max_length=100, blank=True, null=True, unique=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    nacionalidad = models.CharField(max_length=50, default='Peruana')
    direccion = models.TextField(blank=True, null=True)
    contacto_emergencia = models.CharField(max_length=100, blank=True, null=True)
    telefono_emergencia = models.CharField(max_length=15, blank=True, null=True)
    observaciones = models.TextField(blank=True, null=True)
    visitas_totales = models.IntegerField(default=0)
    change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.dni})"
    
    def clean(self):
        if self.id_tipo_doc and self.dni:
            min_length = self.id_tipo_doc.longitud_minima
            max_length = self.id_tipo_doc.longitud_maxima
            if not (min_length <= len(self.dni) <= max_length):
                raise ValidationError(
                    f'El documento debe tener entre {min_length} y {max_length} caracteres para {self.id_tipo_doc.nombre}'
                )

    class Meta:
        db_table = 'huesped'
        indexes = [
            models.Index(fields=['nombres'], name='idx_huesped_nombres'),
            models.Index(fields=['apellidos'], name='idx_huesped_apellidos'),
            models.Index(fields=['email'], name='idx_huesped_email'),
        ]
