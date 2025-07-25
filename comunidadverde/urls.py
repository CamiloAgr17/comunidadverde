from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inicio.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'), 
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('', include('mapa.urls')),
] 
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)