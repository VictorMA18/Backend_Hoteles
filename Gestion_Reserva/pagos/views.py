import stripe
import json
from django.shortcuts import redirect, get_object_or_404
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from .models import CuentaCobrar
from django.shortcuts import render
from .services import crear_payment_intent

stripe.api_key = settings.STRIPE_SECRET_KEY


# --- API para iniciar pago de CuentaCobrar ---
@login_required
def iniciar_pago_stripe(request, cuenta_id):
    try:
        cuenta = CuentaCobrar.objects.get(id_cuenta=cuenta_id)
        if cuenta.estado != 'PENDIENTE':
            return HttpResponse("Esta cuenta ya ha sido pagada.", status=400)
        # Verifica que la cuenta pertenezca al usuario autenticado
        if cuenta.dni_huesped != request.user.huesped:
            return JsonResponse({'error': 'No tienes permiso para pagar esta cuenta'}, status=403)

        # Crea el PaymentIntent solo si la cuenta está pendiente
        client_secret = crear_payment_intent(cuenta)

        return JsonResponse({
            'client_secret': client_secret,
            'cuenta_id': str(cuenta.id_cuenta),
            'monto': float(cuenta.saldo_pendiente),
            'stripe_public_key': settings.STRIPE_PUBLIC_KEY
        })
    except CuentaCobrar.DoesNotExist:
        return JsonResponse({'error': 'Cuenta no encontrada'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# --- API para iniciar pago de Booking (si aún lo usas) ---
@csrf_exempt
def create_payment_intent(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            booking_id = data['booking_id']

            booking = Booking.objects.get(id=booking_id)

            intent = stripe.PaymentIntent.create(
                amount=int(booking.total_price * 100),
                currency='usd',
                automatic_payment_methods={'enabled': True},
                metadata={
                    'booking_id': booking.id,
                    'user_id': request.user.id
                }
            )

            booking.payment_intent_id = intent.id
            booking.save()

            return JsonResponse({'clientSecret': intent.client_secret})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)


# --- Webhook de Stripe protegido ---
@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    # Manejar eventos
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        metadata = payment_intent.get('metadata', {})

        if 'booking_id' in metadata:
            handle_payment_succeeded_booking(payment_intent)
        elif 'cuenta_id' in metadata:
            handle_payment_succeeded_cuenta(payment_intent)

    elif event['type'] == 'payment_intent.payment_failed':
        # Opcional: manejar fallo
        pass

    return HttpResponse(status=200)


# --- Manejo del pago exitoso (booking) ---
def handle_payment_succeeded_booking(payment_intent):
    booking_id = payment_intent.metadata['booking_id']
    try:
        booking = Booking.objects.get(id=booking_id)
        booking.payment_status = 'succeeded'
        booking.save()
        # Aquí podrías enviar un email de confirmación
    except Booking.DoesNotExist:
        pass


# --- Manejo del pago exitoso (cuenta) ---
def handle_payment_succeeded_cuenta(payment_intent):
    cuenta_id = payment_intent.metadata.get('cuenta_id')
    print(f"✔️ Procesando pago exitoso para cuenta_id={cuenta_id}")
    try:
        cuenta = CuentaCobrar.objects.get(id_cuenta=cuenta_id)
        cuenta.estado = 'PAGADO'
        cuenta.save()
        print(f"✅ Cuenta {cuenta_id} marcada como PAGADO")
    except CuentaCobrar.DoesNotExist:
        print(f"❌ Cuenta con ID {cuenta_id} no encontrada")


def pagar_cuenta(request, cuenta_id):
    cuenta = get_object_or_404(CuentaCobrar, id_cuenta=cuenta_id)

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'unit_amount': int(cuenta.monto_total * 100),
                'product_data': {
                    'name': f'Pago de reserva {cuenta.codigo_reserva_id}',
                },
            },
            'quantity': 1,
        }],
        payment_intent_data={  # 👈 clave para que metadata llegue al webhook
            'metadata': {
                'cuenta_id': str(cuenta.id_cuenta)
            }
        },
        success_url='http://localhost:8000/pagos/exito/',
        cancel_url='http://localhost:8000/pagos/cancelado/',
    )

    return redirect(session.url, code=303)