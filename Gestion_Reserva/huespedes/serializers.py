from rest_framework import serializers
from .models import Huesped, TipoDocumento

class HuespedSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Huesped
        fields = [
            'dni', 'id_tipo_doc', 'nombres', 'apellidos', 'celular', 'email',
            'fecha_nacimiento', 'nacionalidad', 'direccion', 'contacto_emergencia',
            'telefono_emergencia', 'observaciones', 'visitas_totales', 'password'
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        dni = validated_data.get('dni')
        user = Huesped.objects.create_user(**validated_data)
        user.set_password(password)
        user.groups.clear()  # Limpiar grupos del usuario
        user.is_staff = False
        user.is_superuser = False
        # Lógica para password_change_required
        if password == dni:
            user.password_change_required = True
        else:
            user.password_change_required = False
        user.save()
        return user