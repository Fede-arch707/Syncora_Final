from django.contrib import admin
from .models import Cliente

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'dni', 'telefono', 'vetado')
    search_fields = ('nombre', 'dni', 'telefono')
    list_filter = ('vetado',)
