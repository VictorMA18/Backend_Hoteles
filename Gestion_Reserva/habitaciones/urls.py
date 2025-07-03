
from django.urls import path
from .views import habitaciones_dashboard_sse

urlpatterns = [
    path('sse/habitaciones-dashboard/', habitaciones_dashboard_sse, name='habitaciones_dashboard_sse'),
]

