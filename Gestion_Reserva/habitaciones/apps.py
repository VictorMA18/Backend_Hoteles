from django.apps import AppConfig

import asyncio

class HabitacionesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'habitaciones'

    def ready(self):
        from .gestion_sse import poll_habitaciones
        loop = asyncio.get_event_loop()
        loop.create_task(poll_habitaciones(3))  # Cada 3 segundos
    