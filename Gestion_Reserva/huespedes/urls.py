from django.urls import path
from .views import register_huesped, delete_huesped, login_huesped, get_huesped

urlpatterns = [
    path('registro/', register_huesped, name='registro-huesped'),
    path('eliminar/<str:dni>/', delete_huesped, name='eliminar_huesped'),
    path('login/', login_huesped, name='login_huesped'),
    path('perfil/', get_huesped, name='get_huesped'),
]