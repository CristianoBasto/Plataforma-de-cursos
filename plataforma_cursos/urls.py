from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from cursos import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', core_views.home, name='home'),
    path('cursos/', include('cursos.urls')),
    path('usuarios/', include('usuarios.urls')),
    path('pagamentos/', include('pagamentos.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
