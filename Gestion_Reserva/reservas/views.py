from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Reserva, HistorialReserva
from .serializers import ReservaSerializer, HistorialReservaSerializer
from usuarios.models import Usuario

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def crear_reserva(request):
    data = request.data.copy()
    # Asigna el usuario (huésped) autenticado
    data['usuario'] = request.user.pk
    serializer = ReservaSerializer(data=data)
    if serializer.is_valid():
        reserva = serializer.save()
        # Guardar en el historial del huésped (si el modelo existe)
        try:
            HistorialReserva.objects.create(huesped=reserva.usuario, reserva=reserva)
        except:
            pass  # Por ahora ignoramos si el historial falla
        return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_reservas(request):
    """Lista las reservas del usuario autenticado"""
    user = request.user
    
    if user.rol == 'HUESPED':
        # Los huéspedes solo ven sus propias reservas
        reservas = Reserva.objects.filter(usuario=user).order_by('-fecha_reserva')
    elif user.rol in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        # Los administradores ven todas las reservas
        reservas = Reserva.objects.all().order_by('-fecha_reserva')
    else:
        return Response({"error": "Sin permisos para ver reservas"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    serializer = ReservaSerializer(reservas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirmar_reserva(request, reserva_id):
    """Confirma una reserva pendiente (solo administradores)"""
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para confirmar reservas"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    try:
        reserva.confirmar()
        return Response({
            "message": "Reserva confirmada exitosamente",
            "reserva": ReservaSerializer(reserva).data
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cancelar_reserva(request, reserva_id):
    """Cancela una reserva"""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Solo el huésped propietario o un administrador pueden cancelar
    if request.user != reserva.usuario and request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para cancelar esta reserva"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    motivo = request.data.get('motivo', None)
    
    try:
        reserva.cancelar(motivo=motivo)
        return Response({
            "message": "Reserva cancelada exitosamente",
            "reserva": ReservaSerializer(reserva).data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_in_reserva(request, reserva_id):
    """Realiza el check-in de una reserva (solo administradores)"""
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para realizar check-in"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    try:
        reserva.check_in()
        return Response({
            "message": "Check-in realizado exitosamente",
            "reserva": ReservaSerializer(reserva).data
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_out_reserva(request, reserva_id):
    """Realiza el check-out de una reserva (solo administradores)"""
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para realizar check-out"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    try:
        reserva.check_out()
        return Response({
            "message": "Check-out realizado exitosamente",
            "reserva": ReservaSerializer(reserva).data
        }, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_limpieza_habitacion(request, reserva_id):
    """Marca la habitación como disponible después de la limpieza (solo administradores)"""
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para gestionar limpieza"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    try:
        reserva.finalizar_limpieza()
        return Response({
            "message": "Limpieza finalizada, habitación disponible",
            "habitacion": {
                "codigo": reserva.codigo_habitacion.codigo,
                "numero": reserva.codigo_habitacion.numero_habitacion,
                "estado": reserva.codigo_habitacion.id_estado.nombre
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def historial_reservas_usuario(request, dni):
    """Historial de reservas de un usuario específico (por dni) - Solo para ADMIN y derivados"""
    if request.user.rol == 'HUESPED':
        return Response({"error": "No tiene permisos para acceder al historial de otros usuarios."}, status=status.HTTP_403_FORBIDDEN)
    try:
        usuario = Usuario.objects.get(dni=dni)
    except Usuario.DoesNotExist:
        return Response({"error": "Usuario no encontrado"}, status=status.HTTP_404_NOT_FOUND)
    try:
        historial = HistorialReserva.objects.filter(huesped=usuario).order_by('-fecha')
        serializer = HistorialReservaSerializer(historial, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except:
        reservas = Reserva.objects.filter(usuario=usuario).order_by('-fecha_reserva')
        serializer = ReservaSerializer(reservas, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)