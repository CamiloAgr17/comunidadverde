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
    path('obtener-etiquetas-para-post/', views.obtener_etiquetas_para_post, name='obtener_etiquetas_para_post'),
    path('comentarios/crear/', views.crear_comentario, name='crear_comentario'),
    path('comentarios/<int:comentario_id>/eliminar/', views.eliminar_comentario, name='eliminar_comentario'),
    path('usuarios/<int:user_id>/', views.obtener_perfil_usuario, name='obtener_perfil_usuario'),
    path('usuarios/alternar-seguimiento/', views.alternar_seguimiento_usuario, name='alternar_seguimiento_usuario'),
    path('notificaciones/', views.obtener_notificaciones, name='obtener_notificaciones'),
    path('notificaciones/marcar_leida/', views.marcar_notificacion_como_leida, name='marcar_notificacion_como_leida'),
    path('api/like/', views.alternar_like_post, name='alternar_like_post'),
    path('posts/alternar-like/', views.alternar_like_post, name='alternar_like_post'),
]
