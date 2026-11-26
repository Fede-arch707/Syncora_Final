import decimal
import django.db.models.deletion
import django.core.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [('clientes', '0001_initial')]
    operations = [
        migrations.CreateModel(
            name='CategoriaEvento',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=80, unique=True)),
            ],
            options={'ordering': ['nombre'], 'verbose_name': 'categoría de evento', 'verbose_name_plural': 'categorías de eventos'},
        ),
        migrations.CreateModel(
            name='Salon',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('nombre', models.CharField(max_length=100, unique=True)),
                ('ubicacion', models.CharField(blank=True, max_length=200)),
                ('activo', models.BooleanField(default=True)),
            ],
            options={'ordering': ['nombre'], 'verbose_name': 'salón', 'verbose_name_plural': 'salones'},
        ),
        migrations.CreateModel(
            name='Reserva',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fecha', models.DateField(db_index=True)),
                ('estado', models.CharField(choices=[('reservado', 'Reservado'), ('alquilado', 'Alquilado')], default='reservado', max_length=12)),
                ('total', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
                ('cuotas_totales', models.PositiveIntegerField(default=1, validators=[django.core.validators.MinValueValidator(1)])),
                ('pagado_inicial', models.DecimalField(decimal_places=2, default=0, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.00'))])),
                ('notas', models.TextField(blank=True)),
                ('legacy_id', models.PositiveIntegerField(blank=True, editable=False, null=True, unique=True)),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('cliente', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas', to='clientes.cliente')),
                ('salon', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reservas', to='reservas.salon')),
                ('tipo_evento', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reservas', to='reservas.categoriaevento')),
            ],
            options={'ordering': ['fecha'], 'verbose_name': 'reserva', 'verbose_name_plural': 'reservas'},
        ),
        migrations.CreateModel(
            name='Pago',
            fields=[
                ('id', models.BigAutoField(primary_key=True, serialize=False)),
                ('fecha', models.DateField(default=django.utils.timezone.localdate)),
                ('monto', models.DecimalField(decimal_places=2, max_digits=12, validators=[django.core.validators.MinValueValidator(decimal.Decimal('0.01'))])),
                ('metodo', models.CharField(choices=[('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'), ('otro', 'Otro')], default='efectivo', max_length=20)),
                ('nota', models.CharField(blank=True, max_length=255)),
                ('reserva', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pagos', to='reservas.reserva')),
            ],
            options={'ordering': ['fecha', 'pk'], 'verbose_name': 'pago', 'verbose_name_plural': 'pagos'},
        ),
    ]
