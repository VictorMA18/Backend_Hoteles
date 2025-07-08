from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import authenticate
from .models import Usuario
from .serializers import UsuarioSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from reservas.models import Reserva

@api_view(['POST'])
@permission_classes([AllowAny])
def register_usuario(request):
    # Forzar el rol a HUESPED para cualquier registro público
    data = request.data.copy()
    data['rol'] = 'HUESPED'
    serializer = UsuarioSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UsuarioSerializer(user).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login_usuario(request):
    dni = request.data.get('dni')
    password = request.data.get('password')
    user = authenticate(request, dni=dni, password=password)
    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UsuarioSerializer(user).data
        }, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def perfil_usuario(request):
    return Response(UsuarioSerializer(request.user).data, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def visitas_hospedadas_usuario(request, dni):
    """
    Devuelve el total de visitas (atributo total_visitas) por un usuario (por DNI).
    Solo accesible para usuarios autenticados.
    """
    try:
        usuario = Usuario.objects.get(dni=dni)
    except Usuario.DoesNotExist:
        return Response({'error': 'Usuario no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

    return Response({'dni': dni, 'total_visitas_hospedadas': usuario.total_visitas}, status=status.HTTP_200_OK)
