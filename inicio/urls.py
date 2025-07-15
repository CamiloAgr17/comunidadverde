from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicio, name='pagina_inicio'),
    path('registro/', views.registro, name='registro'),
    path('registro/voluntario/', views.registro_voluntario, name='registro_voluntario'),
    path('registro/organizacion/', views.registro_organizacion, name='registro_organizacion'),
    path('login/', views.login_view, name='login'),
    path('seleccionar-etiquetas/', views.seleccionar_etiquetas, name='seleccionar_etiquetas'),
    path('feed/', views.feed, name='feed'),
]
