from django.urls import path
from . import views

urlpatterns = [
    path('', views.pagina_inicio, name='pagina_inicio'),
    path('registro/', views.registro, name='registro'),
    path('registro/voluntario/', views.registro_voluntario, name='registro_voluntario'),
    path('registro/organizacion/', views.registro_organizacion, name='registro_organizacion'),
    path('login/', views.login_view, name='login'),
    path('seleccionar-etiquetas/', views.seleccionar_etiquetas, name='seleccionar_etiquetas'),
    path('obtener-etiquetas-para-post/', views.obtener_etiquetas_para_post, name='obtener_etiquetas_para_post'),

    path('obtener-etiquetas-para-post/', views.obtener_etiquetas_para_post, name='obtener_etiquetas_para_post'),

    ## RUTA FEED
    path('feed/', views.feed, name='feed'),
    ## RUTA PARA CREAR POSTS
    path('post/crear/', views.crear_post, name='crear_post'),
    ## RUTA LIKES
    #path('like/<int:post_id>/', views.toggle_like, name='toggle_like'),

    path('like-toggle/', views.toggle_like_ajax, name='toggle_like_ajax'),

    ## Obtener datos para perfil
    path('profile-data/<int:user_id>/', views.get_user_profile_data, name='get_user_profile_data'),

    ## Follow / Unfollow
    path('toggle-follow/<int:user_id>/', views.toggle_follow, name='toggle_follow'),
]
