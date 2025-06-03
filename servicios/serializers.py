from rest_framework import serializers
from .models import (
    Huesped, Habitacion, Administrador, Reserva, 
    LibroEstancia, AccionIngreso, LibroCuenta, AccionRetiro, Duenio
)
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal

class HuespedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Huesped
        fields = '__all__'
        extra_kwargs = {
            'contrasenia': {'write_only': True}
        }
    
    def create(self, validated_data):
        # Hash de la contraseña
        if 'contrasenia' in validated_data:
            validated_data['contrasenia'] = make_password(validated_data['contrasenia'])
        return super().create(validated_data)
    
    def calculate_discount(self, instance):
        """Calcular descuento basado en visitas"""
        if instance.visitas >= 10:
            return Decimal('15.00')
        elif instance.visitas >= 5:
            return Decimal('10.00')
        elif instance.visitas >= 3:
            return Decimal('5.00')
        return Decimal('0.00')

class HuespedCreateSerializer(serializers.ModelSerializer):
    """Serializer para crear huéspedes con validaciones"""
    class Meta:
        model = Huesped
        fields = ['dni', 'nombre', 'contrasenia', 'celular']
        extra_kwargs = {
            'contrasenia': {'write_only': True, 'required': False}
        }

class HabitacionSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source='get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_display', read_only=True)
    
    class Meta:
        model = Habitacion
        fields = '__all__'

class AdministradorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Administrador
        fields = '__all__'
        extra_kwargs = {
            'contrasenia': {'write_only': True}
        }
    
    def create(self, validated_data):
        if 'contrasenia' in validated_data:
            validated_data['contrasenia'] = make_password(validated_data['contrasenia'])
        return super().create(validated_data)

class ReservaSerializer(serializers.ModelSerializer):
    huesped_nombre = serializers.CharField(source='huesped.nombre', read_only=True)
    habitacion_codigo = serializers.CharField(source='habitacion.codigo', read_only=True)
    habitacion_tipo = serializers.CharField(source='habitacion.get_tipo_display', read_only=True)
    estado_display = serializers.CharField(source='get_estado_reserva_display', read_only=True)
    
    class Meta:
        model = Reserva
        fields = '__all__'

class LibroEstanciaSerializer(serializers.ModelSerializer):
    huesped_nombre = serializers.CharField(source='huesped.nombre', read_only=True)
    habitacion_codigo = serializers.CharField(source='habitacion.codigo', read_only=True)
    administrador_nombre = serializers.CharField(source='administrador.nombre', read_only=True)
    
    class Meta:
        model = LibroEstancia
        fields = '__all__'

# Serializer para autenticación personalizada
class LoginSerializer(serializers.Serializer):
    dni = serializers.CharField(max_length=20)
    contrasenia = serializers.CharField(max_length=128, write_only=True)
    tipo_usuario = serializers.ChoiceField(choices=['huesped', 'administrador'])

# ========== servicios/authentication.py ==========
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.hashers import check_password
from .models import Huesped, Administrador

class CustomAuthentication(BaseAuthentication):
    """Autenticación personalizada para Huéspedes y Administradores"""
    
    def authenticate(self, request):
        dni = request.META.get('HTTP_DNI')
        password = request.META.get('HTTP_PASSWORD')
        user_type = request.META.get('HTTP_USER_TYPE')
        
        if not dni or not password or not user_type:
            return None
        
        try:
            if user_type == 'administrador':
                user = Administrador.objects.get(dni=dni)
            elif user_type == 'huesped':
                user = Huesped.objects.get(dni=dni)
            else:
                raise AuthenticationFailed('Tipo de usuario inválido')
            
            if not check_password(password, user.contrasenia):
                raise AuthenticationFailed('Credenciales inválidas')
            
            return (user, None)
        
        except (Huesped.DoesNotExist, Administrador.DoesNotExist):
            raise AuthenticationFailed('Usuario no encontrado')

