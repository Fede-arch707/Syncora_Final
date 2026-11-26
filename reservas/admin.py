from django.contrib import admin

from .models import CategoriaEvento, Pago, Reserva, Salon


@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ubicacion', 'activo')
    search_fields = ('nombre', 'ubicacion')
    list_filter = ('activo',)
    list_per_page = 25


@admin.register(CategoriaEvento)
class CategoriaEventoAdmin(admin.ModelAdmin):
    list_display = ('nombre',)
    search_fields = ('nombre',)


class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0
    fields = ('fecha', 'monto', 'metodo', 'nota')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 'cliente', 'salon', 'tipo_evento', 'estado',
        'total', 'total_pagado_admin', 'saldo_admin',
    )
    list_filter = ('estado', 'salon', 'tipo_evento', 'fecha')
    search_fields = ('cliente__nombre', 'cliente__dni', 'salon__nombre', 'tipo_evento__nombre', 'notas')
    autocomplete_fields = ('cliente', 'salon', 'tipo_evento')
    list_select_related = ('cliente', 'salon', 'tipo_evento')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_per_page = 25
    readonly_fields = ('total_pagado_admin', 'saldo_admin', 'creado_en')
    fieldsets = (
        ('Datos del evento', {'fields': ('cliente', 'salon', 'tipo_evento', 'fecha', 'estado')}),
        ('Importes', {'fields': ('total', 'cuotas_totales', 'pagado_inicial', 'total_pagado_admin', 'saldo_admin')}),
        ('Otros datos', {'fields': ('notas', 'creado_en')}),
    )
    inlines = (PagoInline,)

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('pagos')

    @admin.display(description='Total pagado')
    def total_pagado_admin(self, obj):
        return obj.total_pagado

    @admin.display(description='Saldo pendiente')
    def saldo_admin(self, obj):
        return obj.saldo


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'reserva', 'monto', 'metodo')
    list_filter = ('metodo', 'fecha')
    search_fields = ('reserva__cliente__nombre', 'reserva__cliente__dni', 'reserva__salon__nombre')
    autocomplete_fields = ('reserva',)
    list_select_related = ('reserva__cliente', 'reserva__salon')
    date_hierarchy = 'fecha'
    ordering = ('-fecha',)
    list_per_page = 25
