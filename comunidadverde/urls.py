from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inicio.urls')),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'), 
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('', include('mapa.urls')),
]