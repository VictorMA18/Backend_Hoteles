from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.core.exceptions import ValidationError
from .models import Reserva, HistorialReserva
from .serializers import ReservaSerializer, HistorialReservaSerializer, ReservaDetalleSerializer
from usuarios.models import Usuario
from usuarios.serializers import UsuarioSerializer
from django.utils import timezone
from datetime import timedelta
from habitaciones.models import Habitacion, EstadoHabitacion
from .models import Reserva, HistorialReserva, TipoReserva, EstadoReserva
from django.db.models import Q

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

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_hospedaje_presencial(request):
    """
    Registro de hospedaje presencial: crea usuario huésped si no existe,
    asocia reserva a un administrador y realiza check-in inmediato.
    """
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para registrar hospedaje presencial"}, status=status.HTTP_403_FORBIDDEN)

    dni = request.data.get('dni')
    nombres = request.data.get('nombres')
    apellidos = request.data.get('apellidos')
    habitacion_id = request.data.get('habitacion_id')
    numero_huespedes = request.data.get('numero_huespedes', 1)
    dias = int(request.data.get('dias', 3))
    dni_admin = request.data.get('dni_admin')  # opcional

    # Buscar o crear usuario huésped
    try:
        usuario = Usuario.objects.get(dni=dni)
    except Usuario.DoesNotExist:
        data = {
            'dni': dni,
            'nombres': nombres,
            'apellidos': apellidos,
            'password': dni,
            'rol': 'HUESPED'
        }
        serializer = UsuarioSerializer(data=data)
        if serializer.is_valid():
            usuario = serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Buscar usuario administrador
    if dni_admin:
        try:
            usuario_admin = Usuario.objects.get(dni=dni_admin, rol='ADMIN')
        except Usuario.DoesNotExist:
            return Response({'error': 'Administrador no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        usuario_admin = request.user

    # Buscar habitación
    try:
        habitacion = Habitacion.objects.get(pk=habitacion_id)
    except Habitacion.DoesNotExist:
        return Response({'error': 'Habitación no encontrada.'}, status=status.HTTP_400_BAD_REQUEST)

    # Fechas
    fecha_checkin = timezone.now()
    fecha_checkout = fecha_checkin + timedelta(days=dias)

    # Tipo y estado de reserva
    tipo_reserva = TipoReserva.objects.get(nombre='Presencial')
    estado_reserva = EstadoReserva.objects.get(nombre='Confirmada')

    # Calcular descuento según total_visitas
    if hasattr(usuario, 'total_visitas') and usuario.total_visitas >= 5:
        descuento = float(habitacion.precio_actual) * int(dias) * 0.10  # 10% de descuento
    else:
        descuento = 0.00

    # Validar y crear reserva usando el serializer
    reserva_data = {
        "usuario": usuario.pk,
        "usuario_admin": usuario_admin.pk if usuario_admin else None,
        "codigo_habitacion": habitacion.pk,
        "id_tipo_reserva": tipo_reserva.pk,
        "id_estado_reserva": estado_reserva.pk,
        "fecha_checkin_programado": fecha_checkin,
        "fecha_checkout_programado": fecha_checkout,
        "numero_huespedes": numero_huespedes,
        "precio_noche": habitacion.precio_actual,
        "descuento": descuento,
    }
    serializer = ReservaSerializer(data=reserva_data)
    if serializer.is_valid():
        reserva = serializer.save()
        reserva.check_in()
        if hasattr(usuario, 'rol') and usuario.rol == 'HUESPED':
            usuario.total_visitas = getattr(usuario, 'total_visitas', 0) + 1
            usuario.save()
        return Response({
            "message": "Registro y check-in exitoso",
            "usuario": UsuarioSerializer(usuario).data,
            "reserva": ReservaSerializer(reserva).data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def registrar_hospedaje_presencial_pendiente(request):
    """
    Registro de hospedaje presencial: crea usuario huésped si no existe,
    asocia reserva a un administrador y deja la reserva en estado pendiente (sin check-in inmediato).
    """
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para registrar hospedaje presencial"}, status=status.HTTP_403_FORBIDDEN)

    dni = request.data.get('dni')
    nombres = request.data.get('nombres')
    apellidos = request.data.get('apellidos')
    habitacion_id = request.data.get('habitacion_id')
    numero_huespedes = request.data.get('numero_huespedes', 1)
    dias = int(request.data.get('dias', 3))
    dni_admin = request.data.get('dni_admin')  # opcional

    # Buscar o crear usuario huésped
    try:
        usuario = Usuario.objects.get(dni=dni)
    except Usuario.DoesNotExist:
        data = {
            'dni': dni,
            'nombres': nombres,
            'apellidos': apellidos,
            'password': dni,
            'rol': 'HUESPED'
        }
        serializer = UsuarioSerializer(data=data)
        if serializer.is_valid():
            usuario = serializer.save()
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Buscar usuario administrador
    if dni_admin:
        try:
            usuario_admin = Usuario.objects.get(dni=dni_admin, rol='ADMIN')
        except Usuario.DoesNotExist:
            return Response({'error': 'Administrador no encontrado.'}, status=status.HTTP_400_BAD_REQUEST)
    else:
        usuario_admin = request.user

    # Buscar habitación
    try:
        habitacion = Habitacion.objects.get(pk=habitacion_id)
    except Habitacion.DoesNotExist:
        return Response({'error': 'Habitación no encontrada.'}, status=status.HTTP_400_BAD_REQUEST)

    # Fechas: usar las del request si existen, si no calcularlas
    fecha_checkin = request.data.get('fecha_checkin_programado')
    fecha_checkout = request.data.get('fecha_checkout_programado')
    if not fecha_checkin or not fecha_checkout:
        fecha_checkin = timezone.now()
        fecha_checkout = fecha_checkin + timedelta(days=dias)

    # Tipo y estado de reserva
    tipo_reserva = TipoReserva.objects.get(nombre='Presencial')
    estado_reserva = EstadoReserva.objects.get(nombre='Pendiente')

    # Calcular descuento según total_visitas
    if hasattr(usuario, 'total_visitas') and usuario.total_visitas >= 5:
        descuento = float(habitacion.precio_actual) * int(dias) * 0.10  # 10% de descuento
    else:
        descuento = 0.00

    # Validar y crear reserva usando el serializer
    reserva_data = {
        "usuario": usuario.pk,
        "usuario_admin": usuario_admin.pk if usuario_admin else None,
        "codigo_habitacion": habitacion.pk,
        "id_tipo_reserva": tipo_reserva.pk,
        "id_estado_reserva": estado_reserva.pk,
        "fecha_checkin_programado": fecha_checkin,
        "fecha_checkout_programado": fecha_checkout,
        "numero_huespedes": numero_huespedes,
        "precio_noche": habitacion.precio_actual,
        "descuento": descuento,
    }
    serializer = ReservaSerializer(data=reserva_data)
    if serializer.is_valid():
        reserva = serializer.save()
        # No se hace check_in ni se cambia el estado de la habitación
        return Response({
            "message": "Reserva presencial registrada en estado pendiente",
            "usuario": UsuarioSerializer(usuario).data,
            "reserva": ReservaSerializer(reserva).data
        }, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def listar_reservas_confirmadas_ocupadas_limpieza(request):
    """
    Lista reservas con estado 'Confirmada' o 'Finalizada' y habitación en estado 'Ocupada' o 'Limpieza',
    y además todas las reservas con estado 'Finalizada' (sin importar el estado de la habitación).
    Solo para ADMIN, RECEPCIONISTA o SUPERVISOR.
    """
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para ver reservas confirmadas"}, status=status.HTTP_403_FORBIDDEN)

    estado_confirmada = EstadoReserva.objects.get(nombre='Confirmada')
    estado_finalizada = EstadoReserva.objects.get(nombre='Finalizada')
    estado_ocupada = EstadoHabitacion.objects.get(nombre='Ocupada')
    estado_limpieza = EstadoHabitacion.objects.get(nombre='Limpieza')

    reservas = Reserva.objects.filter(
        Q(
            id_estado_reserva__in=[estado_confirmada, estado_finalizada],
            codigo_habitacion__id_estado__in=[estado_ocupada, estado_limpieza]
        ) |
        Q(id_estado_reserva=estado_finalizada)
    ).distinct().order_by('-fecha_checkin_programado')

    serializer = ReservaDetalleSerializer(reservas, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)