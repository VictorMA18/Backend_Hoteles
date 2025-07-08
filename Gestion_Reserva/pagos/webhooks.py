import stripe
import json
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import CuentaCobrar
from reservas.models import Reserva, EstadoReserva
from habitaciones.models import EstadoHabitacion

stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def stripe_webhook(request):
    print("📩 Webhook recibido")
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    # Manejar eventos de pago
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        handle_payment_succeeded(payment_intent)
    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        handle_payment_failed(payment_intent)
    
    return HttpResponse(status=200)

def handle_payment_succeeded(payment_intent):
    print("✔️ Procesando pago exitoso")
    cuenta_id = payment_intent.metadata.get('cuenta_id')
    print(f"➡️ Cuenta ID recibida: {cuenta_id}")
    try:
        cuenta = CuentaCobrar.objects.get(id_cuenta=cuenta_id)
        print(f"💰 Cuenta encontrada: {cuenta}")

        cuenta.monto_pagado = cuenta.monto_total
        cuenta.estado = 'PAGADO'
        cuenta.save()
        print("✅ Cuenta actualizada a PAGADO")

        reserva = cuenta.codigo_reserva
        reserva.id_estado_reserva = EstadoReserva.objects.get(nombre='Confirmada')
        reserva.save()
        print("✅ Reserva actualizada a Confirmada")

        habitacion = reserva.codigo_habitacion
        habitacion.id_estado = EstadoHabitacion.objects.get(nombre='Ocupada')
        habitacion.save()
        print("✅ Habitación actualizada a Ocupada")

    except CuentaCobrar.DoesNotExist:
        print("❌ Cuenta no encontrada")
    except Exception as e:
        print(f"⚠️ Error inesperado: {e}")

def handle_payment_failed(payment_intent):
    cuenta_id = payment_intent.metadata.get('cuenta_id')
    try:
        cuenta = CuentaCobrar.objects.get(id_cuenta=cuenta_id)
        
        # Actualizar estado de la cuenta
        cuenta.estado = 'VENCIDO'
        cuenta.save()
        
        # Actualizar estado de la reserva
        reserva = cuenta.codigo_reserva
        reserva.id_estado_reserva = EstadoReserva.objects.get(nombre='Cancelada')  # Asegúrate de tener este estado
        reserva.save()
        
        # Liberar habitación
        habitacion = reserva.codigo_habitacion
        habitacion.id_estado = EstadoHabitacion.objects.get(nombre='Disponible')  # Asegúrate de tener este estado
        habitacion.save()
        
    except CuentaCobrar.DoesNotExist:
        # Registrar el error para seguimiento
        pass