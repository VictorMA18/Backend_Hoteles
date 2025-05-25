from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Huesped(models.Model):
  dni = models.CharField(max_length=20, primary_key=True, verbose_name="DNI")
  nombre = models.CharField(max_length=100, verbose_name="Nombre")
  contrasenia = models.CharField(max_length=128, verbose_name="Contraseña")  # Hash de contraseña
  celular = models.CharField(max_length=15, blank=True, null=True, verbose_name="Celular")
  visitas = models.PositiveIntegerField(default=0, verbose_name="Visitas")
  descuento = models.DecimalField(
    max_digits=5, 
    decimal_places=2, 
    default=Decimal('0.00'),
    validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('100.00'))],
    verbose_name="Descuento (%)"
  )
  
  class Meta:
    db_table = 'huesped'
    verbose_name = "Huésped"
    verbose_name_plural = "Huéspedes"

  def __str__(self):
      return f"{self.nombre} ({self.dni})"

class Habitacion(models.Model):
  TIPOS_HABITACION = [
    ('SIMPLE', 'Simple'),
    ('DOBLE', 'Doble'),
    ('MATRIMONIAL', 'Matrimonial'),
    ('SUITE', 'Suite'),
  ]
  
  ESTADOS_HABITACION = [
    ('DISPONIBLE', 'Disponible'),
    ('OCUPADA', 'Ocupada'),
    ('MANTENIMIENTO', 'Mantenimiento'),
    ('LIMPIEZA', 'Limpieza'),
  ]
  
  codigo = models.CharField(max_length=10, primary_key=True, verbose_name="Código")
  tipo = models.CharField(max_length=20, choices=TIPOS_HABITACION, verbose_name="Tipo")
  estado = models.CharField(max_length=20, choices=ESTADOS_HABITACION, default='DISPONIBLE', verbose_name="Estado")
  precio = models.DecimalField(
    max_digits=10, 
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0.01'))],
    verbose_name="Precio por noche"
  )
  
  class Meta:
    db_table = 'habitacion'
    verbose_name = "Habitación"
    verbose_name_plural = "Habitaciones"

  def __str__(self):
    return f"Habitación {self.codigo} - {self.get_tipo_display()}"

class Administrador(models.Model):
  dni = models.CharField(max_length=20, primary_key=True, verbose_name="DNI")
  nombre = models.CharField(max_length=100, verbose_name="Nombre")
  contrasenia = models.CharField(max_length=128, verbose_name="Contraseña") 
  celular = models.CharField(max_length=15, blank=True, null=True, verbose_name="Celular")
  
  class Meta:
    db_table = 'administrador'
    verbose_name = "Administrador"
    verbose_name_plural = "Administradores"
  
  def __str__(self):
    return f"{self.nombre} ({self.dni})"

class Reserva(models.Model):
  ESTADOS_RESERVA = [
    ('PENDIENTE', 'Pendiente'),
    ('CONFIRMADA', 'Confirmada'),
    ('CANCELADA', 'Cancelada'),
    ('COMPLETADA', 'Completada'),
  ]
  
  codigo = models.AutoField(primary_key=True, verbose_name="Código")
  huesped = models.ForeignKey(
    Huesped, 
    on_delete=models.CASCADE, 
    db_column='fk_dni_hue',
    verbose_name="Huésped"
  )
  habitacion = models.ForeignKey(
    Habitacion,
    on_delete=models.CASCADE,
    db_column='fk_hab_cod',
    verbose_name="Habitación"
  )
  fecha_reserva = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Reserva")
  fecha_ingreso = models.DateTimeField(verbose_name="Fecha de Ingreso")
  hora_ingreso = models.TimeField(verbose_name="Hora de Ingreso")
  estado_reserva = models.CharField(
    max_length=20, 
    choices=ESTADOS_RESERVA, 
    default='PENDIENTE',
    verbose_name="Estado de Reserva"
  )
  
  class Meta:
    db_table = 'reserva'
    verbose_name = "Reserva"
    verbose_name_plural = "Reservas"
    
  def __str__(self):
    return f"Reserva {self.codigo} - {self.huesped.nombre}"

class Duenio(models.Model):
  dni = models.CharField(max_length=20, primary_key=True, verbose_name="DNI")
  nombre = models.CharField(max_length=100, verbose_name="Nombre")
  
  class Meta:
    db_table = 'duenio'
    verbose_name = "Dueño"
    verbose_name_plural = "Dueños"
  
  def __str__(self):
    return f"{self.nombre} ({self.dni})"

class AccionRetiro(models.Model):
  codigo = models.AutoField(primary_key=True, verbose_name="Código")
  duenio = models.ForeignKey(
    Duenio,
    on_delete=models.CASCADE,
    db_column='fk_nom_due',
    verbose_name="Dueño"
  )
  monto = models.DecimalField(
    max_digits=12,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0.01'))],
    verbose_name="Monto"
  )
  fecha_retiro = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Retiro")
  
  class Meta:
    db_table = 'accion_retiro'
    verbose_name = "Acción de Retiro"
    verbose_name_plural = "Acciones de Retiro"
  
  def __str__(self):
    return f"Retiro {self.codigo} - ${self.monto}"

class LibroCuenta(models.Model):
  TIPOS_ACCION = [
    ('INGRESO', 'Ingreso'),
    ('RETIRO', 'Retiro'),
  ]
  
  codigo = models.AutoField(primary_key=True, verbose_name="Código")
  accion_retiro = models.ForeignKey(
    AccionRetiro,
    on_delete=models.CASCADE,
    blank=True,
    null=True,
    verbose_name="Acción de Retiro"
  )
  accion = models.CharField(max_length=20, choices=TIPOS_ACCION, verbose_name="Acción")
  saldo_actual = models.DecimalField(
    max_digits=15,
    decimal_places=2,
    default=Decimal('0.00'),
    verbose_name="Saldo Actual"
  )
  fecha_movimiento = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Movimiento")
  
  class Meta:
    db_table = 'libro_cuenta'
    verbose_name = "Libro de Cuenta"
    verbose_name_plural = "Libro de Cuentas"
    ordering = ['-fecha_movimiento']
  
  def __str__(self):
    return f"Movimiento {self.codigo} - {self.get_accion_display()}"

class LibroEstancia(models.Model):
  codigo = models.AutoField(primary_key=True, verbose_name="Código")
  huesped = models.ForeignKey(
    Huesped,
    on_delete=models.CASCADE,
    db_column='fk_dni_hue',
    verbose_name="Huésped"
  )
  administrador = models.ForeignKey(
    Administrador,
    on_delete=models.CASCADE,
    db_column='fk_dni_admin',
    verbose_name="Administrador"
  )
  habitacion = models.ForeignKey(
    Habitacion,
    on_delete=models.CASCADE,
    db_column='fk_hab_cod',
    verbose_name="Habitación"
  )
  medio_pago = models.CharField(max_length=50, verbose_name="Medio de Pago")
  monto = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    validators=[MinValueValidator(Decimal('0.01'))],
    verbose_name="Monto"
  )
  pagado = models.BooleanField(default=False, verbose_name="Pagado")
  hora_entrada = models.TimeField(verbose_name="Hora de Entrada")
  fecha_entrada = models.DateField(verbose_name="Fecha de Entrada")
  hora_salida = models.TimeField(blank=True, null=True, verbose_name="Hora de Salida")
  fecha_salida = models.DateField(blank=True, null=True, verbose_name="Fecha de Salida")
  
  class Meta:
    db_table = 'libro_estancia'
    verbose_name = "Libro de Estancia"
    verbose_name_plural = "Libro de Estancias"
    ordering = ['-fecha_entrada', '-hora_entrada']
  
  def __str__(self):
    return f"Estancia {self.codigo} - {self.huesped.nombre}"

class AccionIngreso(models.Model):
  codigo = models.AutoField(primary_key=True, verbose_name="Código")
  libro_estancia = models.ForeignKey(
    LibroEstancia,
    on_delete=models.CASCADE,
    verbose_name="Libro de Estancia"
  )
  habitacion = models.ForeignKey(
    Habitacion,
    on_delete=models.CASCADE,
    db_column='fk_hab_cod',
    verbose_name="Habitación"
  )
  fecha_ingreso = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Ingreso")
  
  class Meta:
    db_table = 'accion_ingreso'
    verbose_name = "Acción de Ingreso"
    verbose_name_plural = "Acciones de Ingreso"
  
  def __str__(self):
    return f"Ingreso {self.codigo} - Hab. {self.habitacion.codigo}"