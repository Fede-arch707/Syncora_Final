from django.urls import path
from . import views

urlpatterns = [
    path('', views.calendario, name='calendario'),
    path('reservas/nueva/', views.crear, name='reserva_crear'),
    path('reservas/<int:pk>/', views.detalle, name='reserva_detalle'),
    path('reservas/<int:pk>/editar/', views.editar, name='reserva_editar'),
    path('reservas/<int:pk>/borrar/', views.borrar, name='reserva_borrar'),
    path('reservas/<int:pk>/pagar/', views.agregar_pago, name='pago_crear'),
]
