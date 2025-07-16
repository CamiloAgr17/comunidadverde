from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicio, name='pagina_inicio'),
    path('registro/', views.registro, name='registro'),
    path('registro/voluntario/', views.registro_voluntario, name='registro_voluntario'),
    path('registro/organizacion/', views.registro_organizacion, name='registro_organizacion'),
    path('login/', views.login_view, name='login'),
    path('seleccionar-etiquetas/', views.seleccionar_etiquetas, name='seleccionar_etiquetas'),
    path('feed/', views.feed_view, name='feed'),
    path('feed-data/', views.feed_api_view, name='feed_api'),
    path('posts/crear/', views.crear_post, name='crear_post'),
    path('posts/<int:post_id>/eliminar/', views.eliminar_post, name='eliminar_post'),
    path('posts/<int:post_id>/comentarios/', views.obtener_comentarios_de_post, name='obtener_comentarios_post'),
    path('comentarios/crear/', views.crear_comentario, name='crear_comentario'),
    path('comentarios/<int:comentario_id>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),
    path('usuarios/<int:user_id>/', views.obtener_perfil_usuario, name='obtener_perfil_usuario'),
    path('usuarios/alternar-seguimiento/', views.alternar_seguimiento_usuario, name='alternar_seguimiento_usuario'),
]
