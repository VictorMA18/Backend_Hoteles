from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from huespedes.models import TipoDocumento

class UsuarioManager(BaseUserManager):
    def create_user(self, dni, nombres, apellidos, password=None, rol='HUESPED', id_tipo_doc=None, **extra_fields):
        if not dni:
            raise ValueError('El DNI es obligatorio')
        # Validar que la contraseña no sea nula, vacía ni solo espacios
        if not password or not password.strip():
            raise ValueError('La contraseña no puede estar vacía ni ser solo espacios')
        # Asegurar permisos mínimos para HUESPED
        if rol == 'HUESPED':
            extra_fields['is_staff'] = False
            extra_fields['is_superuser'] = False
        # Asignar tipo de documento por defecto si no se provee
        if not id_tipo_doc:
            id_tipo_doc = TipoDocumento.objects.first()
        # Determinar si debe cambiar contraseña
        change_password = (dni == password)
        user = self.model(
            dni=dni,
            nombres=nombres,
            apellidos=apellidos,
            rol=rol,
            id_tipo_doc=id_tipo_doc,
            change_password=change_password,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, dni, nombres, apellidos, password=None, **extra_fields):
        extra_fields.setdefault('rol', 'ADMIN')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(dni, nombres, apellidos, password, **extra_fields)

class Usuario(AbstractBaseUser, PermissionsMixin):
    ROL_CHOICES = [
        ('HUESPED', 'Huésped'),
        ('ADMIN', 'Administrador'),
        ('RECEPCIONISTA', 'Recepcionista'),
        ('SUPERVISOR', 'Supervisor'),
    ]
    dni = models.CharField(primary_key=True, max_length=20, unique=True)
    id_tipo_doc = models.ForeignKey(TipoDocumento, on_delete=models.PROTECT, related_name='usuarios', default=1)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True, null=True, blank=True)
    celular = models.CharField(max_length=15, blank=True, null=True)
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='HUESPED')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    change_password = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'dni'
    REQUIRED_FIELDS = ['nombres', 'apellidos']

    objects = UsuarioManager()

    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.dni}) - {self.rol}"
