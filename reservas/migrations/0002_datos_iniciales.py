from django.db import migrations


def crear_datos(apps, schema_editor):
    Salon = apps.get_model('reservas', 'Salon')
    CategoriaEvento = apps.get_model('reservas', 'CategoriaEvento')
    Salon.objects.get_or_create(nombre='El Poli')
    for nombre in ('Cumpleaños', 'Casamiento', 'Evento empresarial', 'Otro'):
        CategoriaEvento.objects.get_or_create(nombre=nombre)


class Migration(migrations.Migration):
    dependencies = [('reservas', '0001_initial')]
    operations = [migrations.RunPython(crear_datos, migrations.RunPython.noop)]
