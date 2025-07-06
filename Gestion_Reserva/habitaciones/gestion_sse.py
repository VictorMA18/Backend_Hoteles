from habitaciones.models import Habitacion
from asgiref.sync import sync_to_async
import asyncio
import json

subscribers = set()

async def notify_subscribers(data):
    for queue in subscribers.copy():
        await queue.put(data)  # Ahora sí es asyncio.Queue, no una función

def subscribe(queue):
    subscribers.add(queue)
    def unsubscribe():
        subscribers.discard(queue)
    return unsubscribe

async def poll_habitaciones(interval=5):
    last_state = {}
    while True:
        await asyncio.sleep(interval)
        habitaciones = await sync_to_async(list)(
            Habitacion.objects.values('codigo', 'id_estado_id')
        )
        cambios = []
        for h in habitaciones:
            cod = h['codigo']
            estado = h['id_estado_id']
            if cod not in last_state or last_state[cod] != estado:
                cambios.append({'codigo': cod, 'estado': estado})
            last_state[cod] = estado
        if cambios:
            await notify_subscribers(json.dumps({'cambios': cambios}))
