from django.contrib import admin
from django.db.models import Count

from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'dni', 'telefono', 'vetado', 'cantidad_reservas', 'creado_en')
    search_fields = ('nombre', 'dni', 'telefono', 'direccion', 'observaciones')
    list_filter = ('vetado', 'creado_en')
    ordering = ('nombre',)
    list_per_page = 25
    readonly_fields = ('cantidad_reservas', 'creado_en')
    fieldsets = (
        ('Datos del cliente', {'fields': ('nombre', 'dni', 'telefono', 'direccion')}),
        ('Seguimiento', {'fields': ('vetado', 'observaciones', 'cantidad_reservas', 'creado_en')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_cantidad_reservas=Count('reservas', distinct=True))

    @admin.display(description='Cantidad de reservas', ordering='_cantidad_reservas')
    def cantidad_reservas(self, obj):
        return getattr(obj, '_cantidad_reservas', None) if hasattr(obj, '_cantidad_reservas') else obj.reservas.count()
