import stripe
from django.conf import settings
from .models import CuentaCobrar
from reservas.models import Reserva

stripe.api_key = settings.STRIPE_SECRET_KEY

def crear_payment_intent(cuenta_cobrar):
    """Crea un PaymentIntent en Stripe para una cuenta por cobrar"""
    # Validaciones previas al pago
    if cuenta_cobrar.estado != 'PENDIENTE':
        raise ValueError("La cuenta no está pendiente de pago")

    if cuenta_cobrar.saldo_pendiente <= 0:
        raise ValueError("La cuenta ya está pagada")

    try:
        # Convertir monto a centavos (Stripe usa centavos)
        amount = int(cuenta_cobrar.saldo_pendiente * 100)

        # Crear PaymentIntent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            automatic_payment_methods={'enabled': True},
            metadata={
                'cuenta_id': str(cuenta_cobrar.id_cuenta),
                'reserva_id': str(cuenta_cobrar.codigo_reserva.id),
                'huesped_dni': cuenta_cobrar.dni_huesped.dni
            }
        )

        # Guardar el ID del intent en la base de datos
        cuenta_cobrar.payment_intent_id = intent.id
        cuenta_cobrar.save()

        return intent.client_secret

    except Exception as e:
        raise ValueError(f"Error al crear PaymentIntent: {str(e)}")

