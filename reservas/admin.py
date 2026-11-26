from django.contrib import admin
from .models import Salon, CategoriaEvento, Reserva, Pago

@admin.register(Salon)
class SalonAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')

@admin.register(CategoriaEvento)
class CategoriaEventoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)

class PagoInline(admin.TabularInline):
    model = Pago
    extra = 0

@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'cliente', 'salon', 'estado', 'total', 'saldo')
    list_filter = ('estado', 'salon', 'fecha')
    search_fields = ('cliente__nombre', 'cliente__dni')
    inlines = [PagoInline]

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('reserva', 'fecha', 'monto', 'metodo')
