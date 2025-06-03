import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import build_dashboard_snapshot   # (definido debajo)

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("dashboard", self.channel_name)
        await self.accept()
        # Manda un primer snapshot inmediatamente
        await self.send(text_data=json.dumps(build_dashboard_snapshot()))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("dashboard", self.channel_name)

    # Estos eventos los dispararás desde signals o tareas
    async def dashboard_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))

