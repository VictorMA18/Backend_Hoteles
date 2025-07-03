from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario

class UsuarioAdmin(BaseUserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = Usuario
    list_display = ('dni', 'nombres', 'apellidos', 'rol', 'is_staff', 'is_active')
    list_filter = ('rol', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('dni', 'password')}),
        ('Información personal', {'fields': ('nombres', 'apellidos', 'email', 'celular', 'id_tipo_doc', 'change_password')}),
        ('Permisos', {'fields': ('rol', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas', {'fields': ('last_login',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('dni', 'nombres', 'apellidos', 'password1', 'password2', 'rol', 'is_staff', 'is_superuser', 'is_active', 'id_tipo_doc')
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    search_fields = ('dni', 'nombres', 'apellidos', 'email')
    ordering = ('dni',)
    filter_horizontal = ('groups', 'user_permissions',)

admin.site.register(Usuario, UsuarioAdmin)