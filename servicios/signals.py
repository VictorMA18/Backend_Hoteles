from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import LibroEstancia
from .utils import build_dashboard_snapshot

@receiver(post_save, sender=LibroEstancia)
def push_dashboard_on_estancia_change(sender, **kwargs):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "dashboard",
        {
            "type": "dashboard.update",
            "data": build_dashboard_snapshot()
        }
    )

