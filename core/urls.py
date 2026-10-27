from django.contrib import admin
from django.urls import path, include
from inventario import views as inventario_views
from authentication import views as auth_views

from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('inventario/', include('inventario.urls')),
    path('profile/', auth_views.profile_view, name='profile_direct'),
    path('', inventario_views.dashboard_view, name='dashboard'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

