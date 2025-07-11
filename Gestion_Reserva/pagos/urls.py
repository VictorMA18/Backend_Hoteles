from django.urls import path
from . import views, webhooks
from django.http import HttpResponse
from .views import pagar_cuenta

urlpatterns = [
    path('webhook/', webhooks.stripe_webhook, name='stripe_webhook'),
    path('pagar/<uuid:cuenta_id>/', pagar_cuenta, name='pagar_cuenta'),
    path('exito/', lambda r: HttpResponse("✅ Pago exitoso."), name='pago_exito'),
    path('cancelado/', lambda r: HttpResponse("❌ Pago cancelado."), name='pago_cancelado'),
]