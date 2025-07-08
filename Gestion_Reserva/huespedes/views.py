from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response
from rest_framework import status
from .serializers import HuespedSerializer
from .models import Huesped
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication

@api_view(['POST'])
def register_huesped(request):
    serializer = HuespedSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)
    
    user = serializer.save() 

    token, created = Token.objects.get_or_create(user=user)

    return Response({'token': token.key, 'user': HuespedSerializer(user).data}, status=status.HTTP_201_CREATED)

@api_view(['DELETE'])
def delete_huesped(request, dni):
    try:
        huesped = Huesped.objects.get(dni=dni)
        huesped.delete()
        return Response({'detail': 'Huésped eliminado correctamente.'}, status=status.HTTP_204_NO_CONTENT)
    except Huesped.DoesNotExist:
        return Response({'detail': 'Huésped no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def login_huesped(request):
    dni = request.data.get('dni')
    password = request.data.get('password')
    if not dni or not password:
        return Response({'detail': 'DNI y contraseña son requeridos.'}, status=status.HTTP_400_BAD_REQUEST)
    user = authenticate(request, dni=dni, password=password)
    if user is not None:
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'user': HuespedSerializer(user).data}, status=status.HTTP_200_OK)
    else:
        return Response({'detail': 'Credenciales inválidas.'}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['GET'])
@authentication_classes([TokenAuthentication]) 
@permission_classes([IsAuthenticated])
def get_huesped(request):
    return Response(HuespedSerializer(request.user).data, status=status.HTTP_200_OK)