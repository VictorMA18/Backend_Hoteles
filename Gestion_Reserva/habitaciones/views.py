from django.shortcuts import render
from django.http import StreamingHttpResponse
from habitaciones.models import Habitacion
from django.utils.timezone import now

import time
import json

# SSE para mostrar habitaciones disponibles en tiempo real
def habitaciones_disponibles_sse(request):
    def event_stream():
        last_data = ''
        while True:
            disponibles = cache.get("habitaciones_disponibles", [])
            data_json = json.dumps(disponibles, default=str)

            if data_json != last_data:
                last_data = data_json
                yield f"data: {data_json}\n\n"

            time.sleep(1)

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

