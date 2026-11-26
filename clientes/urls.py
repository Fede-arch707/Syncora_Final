from django.urls import path
from . import views

urlpatterns = [
    path('excel/exportar/', views.exportar_excel, name='clientes_exportar_excel'),
    path('nuevo/', views.crear, name='cliente_crear'),
    path('<int:pk>/', views.detalle, name='cliente_detalle'),
    path('<int:pk>/editar/', views.editar, name='cliente_editar'),
    path('<int:pk>/borrar/', views.borrar, name='cliente_borrar'),
]
