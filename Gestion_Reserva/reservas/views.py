from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.response import Response
from rest_framework import status
from .models import Reserva, HistorialReserva
from .serializers import ReservaSerializer, HistorialReservaSerializer

@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def crear_reserva(request):
    data = request.data.copy()
    # Asigna el huesped autenticado
    data['dni_huesped'] = request.user.pk  # o request.user.dni
    serializer = ReservaSerializer(data=data)
    if serializer.is_valid():
        reserva = serializer.save()
        # Guardar en el historial del huésped
        HistorialReserva.objects.create(huesped=reserva.dni_huesped, reserva=reserva)
        return Response(ReservaSerializer(reserva).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def historial_reservas_huesped(request):
    user = request.user
    historial = HistorialReserva.objects.filter(huesped=user).order_by('-fecha')
    serializer = HistorialReservaSerializer(historial, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)