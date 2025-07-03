from rest_framework import serializers
from .models import Usuario
from huespedes.models import TipoDocumento

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    id_tipo_doc = serializers.PrimaryKeyRelatedField(
        queryset=TipoDocumento.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = Usuario
        fields = [
            'dni', 'id_tipo_doc', 'nombres', 'apellidos', 'email', 'celular', 'rol', 'password',
            'is_active', 'is_staff', 'change_password', 'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = Usuario.objects.create_user(password=password, **validated_data)
        return user
