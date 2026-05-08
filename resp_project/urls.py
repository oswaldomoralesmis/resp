from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    #path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('', include('servidores.urls')),
    path('catalogos/', include('catalogos.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('cargas/', include('cargas.urls')),
    path('reportes/', include('reportes.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
