# Generated by Django 5.2.1 on 2025-07-08 02:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reservas', '0004_remove_reserva_descuento'),
    ]

    operations = [
        migrations.AddField(
            model_name='reserva',
            name='descuento_aplicado',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
