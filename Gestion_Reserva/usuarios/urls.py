from django.urls import path
from .views import register_usuario, login_usuario, perfil_usuario, visitas_hospedadas_usuario
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', register_usuario, name='register_usuario'),
    path('login/', login_usuario, name='login_usuario'),
    path('perfil/', perfil_usuario, name='perfil_usuario'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('<str:dni>/visitas-hospedadas/', visitas_hospedadas_usuario, name='visitas_hospedadas_usuario'),
]
