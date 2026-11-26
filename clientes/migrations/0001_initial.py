from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=120)),
                ('dni', models.CharField(max_length=16, unique=True, validators=[django.core.validators.RegexValidator(r'^\d{7,11}$', 'Ingresá de 7 a 11 dígitos, sin puntos.')])),
                ('telefono', models.CharField(blank=True, max_length=30)),
                ('direccion', models.CharField(blank=True, max_length=200)),
                ('observaciones', models.TextField(blank=True)),
                ('vetado', models.BooleanField(default=False)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
            ],
            options={'ordering': ['nombre'], 'verbose_name': 'cliente', 'verbose_name_plural': 'clientes'},
        ),
    ]
