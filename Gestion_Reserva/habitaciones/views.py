from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Habitacion, EstadoHabitacion, TipoHabitacion
from .serializers import HabitacionSerializer

@api_view(['GET'])
def listar_habitaciones(request):
    """Lista todas las habitaciones con filtros opcionales - Acceso público"""
    habitaciones = Habitacion.objects.all()
    
    # Filtros opcionales
    estado = request.GET.get('estado')
    tipo = request.GET.get('tipo')
    piso = request.GET.get('piso')
    disponible = request.GET.get('disponible')
    
    if estado:
        habitaciones = habitaciones.filter(id_estado__nombre__icontains=estado)
    
    if tipo:
        habitaciones = habitaciones.filter(id_tipo__nombre__icontains=tipo)
    
    if piso:
        habitaciones = habitaciones.filter(piso=piso)
    
    if disponible == 'true':
        habitaciones = habitaciones.filter(id_estado__permite_reserva=True)
    
    serializer = HabitacionSerializer(habitaciones, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['GET'])
def habitaciones_disponibles(request):
    """Lista solo las habitaciones disponibles para reservar - Acceso público"""
    habitaciones = Habitacion.objects.filter(id_estado__permite_reserva=True)
    serializer = HabitacionSerializer(habitaciones, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cambiar_estado_habitacion(request, codigo_habitacion):
    """Cambia el estado de una habitación (solo administradores)"""
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para cambiar estado de habitaciones"}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    habitacion = get_object_or_404(Habitacion, codigo=codigo_habitacion)
    nuevo_estado_id = request.data.get('estado_id')
    
    if not nuevo_estado_id:
        return Response({"error": "Debe proporcionar el ID del nuevo estado"}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        nuevo_estado = EstadoHabitacion.objects.get(pk=nuevo_estado_id)
        habitacion.id_estado = nuevo_estado
        
        # Si se marca como disponible después de limpieza, actualizar fecha
        if nuevo_estado.pk == 1:  # Disponible
            from django.utils import timezone
            habitacion.fecha_ultima_limpieza = timezone.now()
        
        habitacion.save()
        
        return Response({
            "message": f"Estado de habitación {habitacion.numero_habitacion} cambiado a {nuevo_estado.nombre}",
            "habitacion": HabitacionSerializer(habitacion).data
        }, status=status.HTTP_200_OK)
        
    except EstadoHabitacion.DoesNotExist:
        return Response({"error": "Estado no válido"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def estados_habitacion(request):
    """Lista todos los estados de habitación disponibles - Acceso público"""
    estados = EstadoHabitacion.objects.all()
    return Response([{
        "id": estado.id_estado,
        "nombre": estado.nombre,
        "descripcion": estado.descripcion,
        "permite_reserva": estado.permite_reserva
    } for estado in estados], status=status.HTTP_200_OK)

@api_view(['GET'])
def tipos_habitacion(request):
    """Lista todos los tipos de habitación disponibles - Acceso público"""
    tipos = TipoHabitacion.objects.all()
    return Response([{
        "id": tipo.id_tipo,
        "nombre": tipo.nombre,
        "descripcion": tipo.descripcion,
        "capacidad_maxima": tipo.capacidad_maxima,
        "precio_base": tipo.precio_base
    } for tipo in tipos], status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def buscar_disponibilidad(request):
    """Busca habitaciones disponibles para un rango de fechas, tipo y capacidad (requiere autenticación)"""
    data = request.data
    fecha_checkin = data.get('fecha_checkin')
    fecha_checkout = data.get('fecha_checkout')
    tipo_habitacion = data.get('tipo_habitacion')
    numero_huespedes = data.get('numero_huespedes')

    if not (fecha_checkin and fecha_checkout and tipo_habitacion and numero_huespedes):
        return Response({'detail': 'Faltan datos.'}, status=status.HTTP_400_BAD_REQUEST)

    habitaciones = Habitacion.objects.filter(
        id_tipo__nombre__iexact=tipo_habitacion,
        id_tipo__capacidad_maxima__gte=numero_huespedes
    )

    habitaciones_disponibles = habitaciones.exclude(
        reserva__fecha_checkin_programado__lt=fecha_checkout,
        reserva__fecha_checkout_programado__gt=fecha_checkin,
        reserva__id_estado_reserva__nombre__in=['Pendiente', 'Confirmada', 'Ocupada']
    ).distinct()

    serializer = HabitacionSerializer(habitaciones_disponibles, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finalizar_limpieza(request, codigo_habitacion):
    if request.user.rol not in ['ADMIN', 'RECEPCIONISTA', 'SUPERVISOR']:
        return Response({"error": "Sin permisos para finalizar limpieza"}, status=403)
    try:
        habitacion = Habitacion.objects.get(codigo=codigo_habitacion)
        estado_limpieza = EstadoHabitacion.objects.get(nombre='Limpieza')
        estado_disponible = EstadoHabitacion.objects.get(nombre='Disponible')
        # Verificar que la habitación esté en estado "Limpieza"
        if habitacion.id_estado != estado_limpieza:
            return Response(
                {"error": "La habitación no está en estado de Limpieza."},
                status=status.HTTP_400_BAD_REQUEST
            )
        habitacion.id_estado = estado_disponible
        habitacion.save()
        return Response({
            "message": "Limpieza finalizada, habitación disponible",
            "habitacion": {
                "codigo": habitacion.codigo,
                "numero": habitacion.numero_habitacion,
                "estado": habitacion.id_estado.nombre
            }
        }, status=200)
    except Habitacion.DoesNotExist:
        return Response({"error": "Habitación no encontrada"}, status=404)
