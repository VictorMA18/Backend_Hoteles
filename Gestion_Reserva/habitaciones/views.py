from django.http import StreamingHttpResponse
from django.core.cache import cache
import asyncio
import json

async def habitaciones_dashboard_sse(request):
    async def event_stream():
        last_data = ''
        while True:
            habitaciones = cache.get("habitaciones_dashboard", [])
            data_json = json.dumps(habitaciones)

            if data_json != last_data:
                last_data = data_json
                yield f"data: {data_json}\n\n"

            await asyncio.sleep(1)

    async def stream():
        async for chunk in event_stream():
            yield chunk.encode('utf-8')

    return StreamingHttpResponse(stream(), content_type='text/event-stream')

