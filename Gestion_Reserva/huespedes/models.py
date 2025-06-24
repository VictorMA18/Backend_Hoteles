from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
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

class HuespedManager(UserManager):
    use_in_migrations = True

    def _create_user(self, dni, password, **extra_fields):
        if not dni:
            raise ValueError('El DNI es obligatorio')
        if 'id_tipo_doc' not in extra_fields or extra_fields['id_tipo_doc'] is None:
            from huespedes.models import TipoDocumento
            extra_fields['id_tipo_doc'] = TipoDocumento.objects.first()  # O filtra por nombre/código si quieres uno específico
        user = self.model(dni=dni, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, dni, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self._create_user(dni, password, **extra_fields)
        return user

    def create_superuser(self, dni, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superusuario debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superusuario debe tener is_superuser=True.')

        return self._create_user(dni, password, **extra_fields)

class Huesped(AbstractUser):
    username = None 
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
    password_change_required = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user_permissions = None
    
    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['nombres', 'apellidos']

    objects = HuespedManager()

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"
    
    def clean(self):
    # Validar longitud del documento según tipo
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
