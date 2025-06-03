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
