from .models import Habitacion, LibroEstancia, Reserva
from datetime import datetime, date
from django.db import models

def build_dashboard_snapshot():
    total = Habitacion.objects.count()
    ocupadas = Habitacion.objects.filter(estado="OCUPADA").count()
    disponibles = Habitacion.objects.filter(estado="DISPONIBLE").count()
    limpieza = Habitacion.objects.filter(estado="LIMPIEZA").count()
    mantenimiento = Habitacion.objects.filter(estado="MANTENIMIENTO").count()

    ingresos_hoy = LibroEstancia.objects.filter(
        fecha_entrada=date.today(), pagado=True
    ).aggregate(total=models.Sum('monto'))['total'] or 0

    return {
        "timestamp": datetime.now().isoformat(),
        "habitaciones": {
            "total": total,
            "ocupadas": ocupadas,
            "disponibles": disponibles,
            "limpieza": limpieza,
            "mantenimiento": mantenimiento,
            "ocupacion_%": round((ocupadas / total) * 100, 2) if total else 0
        },
        "ingresos_hoy": ingresos_hoy,
    }

