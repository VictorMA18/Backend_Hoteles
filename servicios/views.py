from django.shortcuts import render
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth.hashers import check_password
from django.db.models import Q
from .models import *
from .serializers import *

from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the Hotel Backend System!")


# ========== AUTENTICACIÓN ==========
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """Login personalizado para huéspedes y administradores"""
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        dni = serializer.validated_data['dni']
        password = serializer.validated_data['contrasenia']
        user_type = serializer.validated_data['tipo_usuario']
        
        try:
            if user_type == 'administrador':
                user = Administrador.objects.get(dni=dni)
            else:
                user = Huesped.objects.get(dni=dni)
            
            if check_password(password, user.contrasenia):
                # Crear o obtener token (simulado)
                response_data = {
                    'token': f'token_{dni}_{user_type}',
                    'user_type': user_type,
                    'dni': dni,
                    'nombre': user.nombre,
                    'message': 'Login exitoso'
                }
                return Response(response_data, status=status.HTTP_200_OK)
            else:
                return Response({'error': 'Credenciales inválidas'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
        
        except (Administrador.DoesNotExist, Huesped.DoesNotExist):
            return Response({'error': 'Usuario no encontrado'}, 
                          status=status.HTTP_404_NOT_FOUND)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ========== HUÉSPEDES ==========
class HuespedListCreateView(generics.ListCreateAPIView):
    queryset = Huesped.objects.all()
    serializer_class = HuespedSerializer
    permission_classes = [AllowAny]  # Temporal para desarrollo
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return HuespedCreateSerializer
        return HuespedSerializer

class HuespedDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Huesped.objects.all()
    serializer_class = HuespedSerializer
    lookup_field = 'dni'

@api_view(['GET'])
def huesped_search(request):
    """Búsqueda de huéspedes por DNI o nombre"""
    query = request.GET.get('q', '')
    if query:
        huespedes = Huesped.objects.filter(
            Q(dni__icontains=query) | Q(nombre__icontains=query)
        )
        serializer = HuespedSerializer(huespedes, many=True)
        return Response(serializer.data)
    return Response([])

@api_view(['GET'])
def huesped_history(request, dni):
    """Historial de estadías de un huésped (RF-05)"""
    try:
        huesped = Huesped.objects.get(dni=dni)
        estancias = LibroEstancia.objects.filter(huesped=huesped).order_by('-fecha_entrada')
        serializer = LibroEstanciaSerializer(estancias, many=True)
        
        response_data = {
            'huesped': HuespedSerializer(huesped).data,
            'historial': serializer.data,
            'total_visitas': huesped.visitas,
            'descuento_actual': huesped.descuento
        }
        return Response(response_data)
    except Huesped.DoesNotExist:
        return Response({'error': 'Huésped no encontrado'}, 
                       status=status.HTTP_404_NOT_FOUND)

# ========== HABITACIONES ==========
class HabitacionListView(generics.ListAPIView):
    queryset = Habitacion.objects.all()
    serializer_class = HabitacionSerializer

@api_view(['PUT'])
def habitacion_update_status(request, codigo):
    """Actualizar estado de habitación"""
    try:
        habitacion = Habitacion.objects.get(codigo=codigo)
        nuevo_estado = request.data.get('estado')
        
        if nuevo_estado in dict(Habitacion.ESTADOS_HABITACION):
            habitacion.estado = nuevo_estado
            habitacion.save()
            return Response(HabitacionSerializer(habitacion).data)
        else:
            return Response({'error': 'Estado inválido'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    except Habitacion.DoesNotExist:
        return Response({'error': 'Habitación no encontrada'}, 
                       status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
def habitaciones_disponibles(request):
    """Obtener habitaciones disponibles para reservas"""
    fecha_ingreso = request.GET.get('fecha_ingreso')
    fecha_salida = request.GET.get('fecha_salida')
    
    # Lógica básica - mejorar en semanas posteriores
    habitaciones = Habitacion.objects.filter(estado='DISPONIBLE')
    serializer = HabitacionSerializer(habitaciones, many=True)
    return Response(serializer.data)

# ========== RESERVAS ==========
class ReservaListCreateView(generics.ListCreateAPIView):
    queryset = Reserva.objects.all().order_by('-fecha_reserva')
    serializer_class = ReservaSerializer

class ReservaDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Reserva.objects.all()
    serializer_class = ReservaSerializer
    lookup_field = 'codigo'

@api_view(['POST'])
def confirmar_reserva(request, codigo):
    """Confirmar una reserva pendiente"""
    try:
        reserva = Reserva.objects.get(codigo=codigo)
        if reserva.estado_reserva == 'PENDIENTE':
            reserva.estado_reserva = 'CONFIRMADA'
            # Actualizar estado de habitación
            reserva.habitacion.estado = 'OCUPADA'  # o 'RESERVADA'
            reserva.habitacion.save()
            reserva.save()
            
            return Response({
                'message': 'Reserva confirmada exitosamente',
                'reserva': ReservaSerializer(reserva).data
            })
        else:
            return Response({'error': 'La reserva no está pendiente'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    except Reserva.DoesNotExist:
        return Response({'error': 'Reserva no encontrada'}, 
                       status=status.HTTP_404_NOT_FOUND)

# ========== CHECK-IN/CHECK-OUT ==========
@api_view(['POST'])
def checkin_huesped(request):
    """Proceso de check-in digital (RF-04)"""
    try:
        dni_huesped = request.data.get('dni_huesped')
        codigo_habitacion = request.data.get('codigo_habitacion')
        dni_admin = request.data.get('dni_admin')
        medio_pago = request.data.get('medio_pago', 'EFECTIVO')
        
        # Validar datos
        huesped = Huesped.objects.get(dni=dni_huesped)
        habitacion = Habitacion.objects.get(codigo=codigo_habitacion)
        administrador = Administrador.objects.get(dni=dni_admin)
        
        # Verificar disponibilidad
        if habitacion.estado != 'DISPONIBLE':
            return Response({'error': 'Habitación no disponible'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Calcular descuento automático (RF-06)
        descuento_porcentaje = calculate_discount_for_guest(huesped)
        precio_original = habitacion.precio
        descuento_monto = precio_original * (descuento_porcentaje / 100)
        precio_final = precio_original - descuento_monto
        
        # Crear registro de estancia
        from datetime import datetime, time
        ahora = datetime.now()
        
        estancia = LibroEstancia.objects.create(
            huesped=huesped,
            administrador=administrador,
            habitacion=habitacion,
            medio_pago=medio_pago,
            monto=precio_final,
            pagado=False,  # Se pagará al checkout
            hora_entrada=ahora.time(),
            fecha_entrada=ahora.date()
        )
        
        # Actualizar estado de habitación
        habitacion.estado = 'OCUPADA'
        habitacion.save()
        
        # Incrementar visitas del huésped
        huesped.visitas += 1
        huesped.descuento = descuento_porcentaje
        huesped.save()
        
        # Crear acción de ingreso
        AccionIngreso.objects.create(
            libro_estancia=estancia,
            habitacion=habitacion
        )
        
        response_data = {
            'message': 'Check-in realizado exitosamente',
            'estancia': LibroEstanciaSerializer(estancia).data,
            'descuento_aplicado': descuento_porcentaje,
            'precio_original': precio_original,
            'precio_final': precio_final
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)
        
    except (Huesped.DoesNotExist, Habitacion.DoesNotExist, Administrador.DoesNotExist) as e:
        return Response({'error': str(e)}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def checkout_huesped(request):
    """Proceso de check-out digital (RF-04)"""
    try:
        codigo_estancia = request.data.get('codigo_estancia')
        pagado = request.data.get('pagado', True)
        
        estancia = LibroEstancia.objects.get(codigo=codigo_estancia)
        
        # Verificar que no haya check-out previo
        if estancia.fecha_salida:
            return Response({'error': 'Check-out ya realizado'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar datos de salida
        from datetime import datetime
        ahora = datetime.now()
        estancia.hora_salida = ahora.time()
        estancia.fecha_salida = ahora.date()
        estancia.pagado = pagado
        estancia.save()
        
        # Liberar habitación
        estancia.habitacion.estado = 'LIMPIEZA'  # Necesita limpieza antes de estar disponible
        estancia.habitacion.save()
        
        # Si está pagado, registrar ingreso en libro de cuentas
        if pagado:
            LibroCuenta.objects.create(
                accion='INGRESO',
                saldo_actual=LibroCuenta.objects.last().saldo_actual + estancia.monto if LibroCuenta.objects.exists() else estancia.monto
            )
        
        response_data = {
            'message': 'Check-out realizado exitosamente',
            'estancia': LibroEstanciaSerializer(estancia).data
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except LibroEstancia.DoesNotExist:
        return Response({'error': 'Estancia no encontrada'}, 
                       status=status.HTTP_404_NOT_FOUND)

def calculate_discount_for_guest(huesped):
    """Calcular descuento automático basado en visitas (RF-06)"""
    if huesped.visitas >= 15:
        return Decimal('20.00')
    elif huesped.visitas >= 10:
        return Decimal('15.00')
    elif huesped.visitas >= 5:
        return Decimal('10.00')
    elif huesped.visitas >= 3:
        return Decimal('5.00')
    return Decimal('0.00')

@api_view(['GET'])
def get_discount_for_guest(request, dni):
    """Obtener descuento disponible para un huésped"""
    try:
        huesped = Huesped.objects.get(dni=dni)
        descuento = calculate_discount_for_guest(huesped)
        
        return Response({
            'dni': dni,
            'nombre': huesped.nombre,
            'visitas': huesped.visitas,
            'descuento_disponible': descuento,
            'descuento_actual': huesped.descuento
        })
    except Huesped.DoesNotExist:
        return Response({'error': 'Huésped no encontrado'}, 
                       status=status.HTTP_404_NOT_FOUND)

# ========== DASHBOARD TIEMPO REAL ==========
@api_view(['GET'])
def dashboard_realtime(request):
    """Dashboard en tiempo real (RF-03)"""
    
    # Estadísticas generales
    total_habitaciones = Habitacion.objects.count()
    habitaciones_ocupadas = Habitacion.objects.filter(estado='OCUPADA').count()
    habitaciones_disponibles = Habitacion.objects.filter(estado='DISPONIBLE').count()
    habitaciones_limpieza = Habitacion.objects.filter(estado='LIMPIEZA').count()
    habitaciones_mantenimiento = Habitacion.objects.filter(estado='MANTENIMIENTO').count()
    
    # Huéspedes actuales (con check-in pero sin check-out)
    huespedes_actuales = LibroEstancia.objects.filter(
        fecha_salida__isnull=True
    ).count()
    
    # Reservas pendientes de hoy
    from datetime import date
    reservas_hoy = Reserva.objects.filter(
        fecha_ingreso__date=date.today(),
        estado_reserva='CONFIRMADA'
    ).count()
    
    # Ingresos del día
    ingresos_hoy = LibroEstancia.objects.filter(
        fecha_entrada=date.today(),
        pagado=True
    ).aggregate(total=models.Sum('monto'))['total'] or 0
    
    # Estado detallado de habitaciones
    habitaciones_detalle = []
    for habitacion in Habitacion.objects.all():
        # Buscar huésped actual si está ocupada
        huesped_actual = None
        if habitacion.estado == 'OCUPADA':
            estancia = LibroEstancia.objects.filter(
                habitacion=habitacion,
                fecha_salida__isnull=True
            ).first()
            if estancia:
                huesped_actual = estancia.huesped.nombre
        
        habitaciones_detalle.append({
            'codigo': habitacion.codigo,
            'tipo': habitacion.get_tipo_display(),
            'estado': habitacion.estado,
            'estado_display': habitacion.get_estado_display(),
            'precio': habitacion.precio,
            'huesped_actual': huesped_actual
        })
    
    dashboard_data = {
        'resumen': {
            'total_habitaciones': total_habitaciones,
            'ocupadas': habitaciones_ocupadas,
            'disponibles': habitaciones_disponibles,
            'limpieza': habitaciones_limpieza,
            'mantenimiento': habitaciones_mantenimiento,
            'ocupacion_porcentaje': round((habitaciones_ocupadas / total_habitaciones) * 100, 2) if total_habitaciones > 0 else 0
        },
        'operaciones_hoy': {
            'huespedes_actuales': huespedes_actuales,
            'reservas_pendientes': reservas_hoy,
            'ingresos': ingresos_hoy
        },
        'habitaciones': habitaciones_detalle,
        'timestamp': datetime.now().isoformat()
    }
    
    return Response(dashboard_data)

@api_view(['GET'])
def current_guests(request):
    """Lista de huéspedes actuales en el hotel"""
    estancias_actuales = LibroEstancia.objects.filter(
        fecha_salida__isnull=True
    ).select_related('huesped', 'habitacion')
    
    huespedes_data = []
    for estancia in estancias_actuales:
        huespedes_data.append({
            'codigo_estancia': estancia.codigo,
            'huesped': {
                'dni': estancia.huesped.dni,
                'nombre': estancia.huesped.nombre,
                'celular': estancia.huesped.celular
            },
            'habitacion': {
                'codigo': estancia.habitacion.codigo,
                'tipo': estancia.habitacion.get_tipo_display()
            },
            'fecha_entrada': estancia.fecha_entrada,
            'hora_entrada': estancia.hora_entrada,
            'monto': estancia.monto,
            'pagado': estancia.pagado
        })
    
    return Response(huespedes_data)

@api_view(['GET'])
def reporte_ocupacion_mensual(request):
    """Reporte mensual de ocupación (RF-08)"""
    from django.db.models import Count
    from datetime import datetime, timedelta
    import calendar
    
    # Parámetros
    año = int(request.GET.get('año', datetime.now().year))
    mes = int(request.GET.get('mes', datetime.now().month))
    
    # Primer y último día del mes
    primer_dia = datetime(año, mes, 1).date()
    ultimo_dia = datetime(año, mes, calendar.monthrange(año, mes)[1]).date()
    
    # Estadísticas del mes
    total_habitaciones = Habitacion.objects.count()
    
    # Ocupación por día
    ocupacion_diaria = []
    fecha_actual = primer_dia
    
    while fecha_actual <= ultimo_dia:
        ocupadas = LibroEstancia.objects.filter(
            fecha_entrada__lte=fecha_actual,
            fecha_salida__gte=fecha_actual
        ).count()
        
        # Incluir estancias que no han terminado
        ocupadas += LibroEstancia.objects.filter(
            fecha_entrada__lte=fecha_actual,
            fecha_salida__isnull=True
        ).count()
        
        porcentaje = (ocupadas / total_habitaciones) * 100 if total_habitaciones > 0 else 0
        
        ocupacion_diaria.append({
            'fecha': fecha_actual.isoformat(),
            'ocupadas': ocupadas,
            'disponibles': total_habitaciones - ocupadas,
            'porcentaje_ocupacion': round(porcentaje, 2)
        })
        
        fecha_actual += timedelta(days=1)
    
    # Estadísticas generales del mes
    estancias_mes = LibroEstancia.objects.filter(
        fecha_entrada__range=[primer_dia, ultimo_dia]
    )
    
    ingresos_mes = estancias_mes.filter(pagado=True).aggregate(
        total=models.Sum('monto')
    )['total'] or 0
    
    huespedes_unicos = estancias_mes.values('huesped').distinct().count()
    
    # Habitaciones más populares
    habitaciones_populares = estancias_mes.values(
        'habitacion__codigo', 'habitacion__tipo'
    ).annotate(
        reservas=Count('habitacion')
    ).order_by('-reservas')[:5]
    
    reporte = {
        'periodo': {
            'año': año,
            'mes': mes,
            'nombre_mes': calendar.month_name[mes],
            'primer_dia': primer_dia.isoformat(),
            'ultimo_dia': ultimo_dia.isoformat()
        },
        'resumen': {
            'total_habitaciones': total_habitaciones,
            'total_estancias': estancias_mes.count(),
            'huespedes_unicos': huespedes_unicos,
            'ingresos_total': ingresos_mes,
            'ocupacion_promedio': round(
                sum([d['porcentaje_ocupacion'] for d in ocupacion_diaria]) / len(ocupacion_diaria), 2
            ) if ocupacion_diaria else 0
        },
        'ocupacion_diaria': ocupacion_diaria,
        'habitaciones_populares': list(habitaciones_populares)
    }
    
    return Response(reporte)

@api_view(['GET'])
def reporte_ingresos(request):
    """
    GET ?fecha_inicio=2025-05-01&fecha_fin=2025-05-31
    Devuelve ingresos diarios y por tipo de habitación.
    """
    fi = request.GET.get('fecha_inicio')
    ff = request.GET.get('fecha_fin')

    if not fi or not ff:
        ff = date.today()
        fi = ff - timedelta(days=30)
    else:
        fi = datetime.strptime(fi, '%Y-%m-%d').date()
        ff = datetime.strptime(ff, '%Y-%m-%d').date()

    estancias = LibroEstancia.objects.filter(
        fecha_entrada__range=[fi, ff],
        pagado=True
    )

    total = estancias.aggregate(total=Sum('monto'))['total'] or 0

    ingresos_diarios = estancias.values('fecha_entrada').annotate(
        total_dia=Sum('monto'),
        estancias=Count('codigo')
    ).order_by('fecha_entrada')

    ingresos_por_tipo = estancias.values(
        'habitacion__tipo'
    ).annotate(
        total=Sum('monto'),
        estancias=Count('codigo')
    )

    return Response({
        'periodo': {'fecha_inicio': fi, 'fecha_fin': ff},
        'total_ingresos': total,
        'ingresos_diarios': list(ingresos_diarios),
        'ingresos_por_tipo': list(ingresos_por_tipo),
    })

