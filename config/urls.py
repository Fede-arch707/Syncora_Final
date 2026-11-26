from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from clientes.views import registro

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', registro, name='registro'),
    path('clientes/', include('clientes.urls')),
    path('', include('reservas.urls')),
]
