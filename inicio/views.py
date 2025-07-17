from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import RegistroOrganizacionForm, RegistroVoluntarioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import json
from .models import Post, Etiqueta, Voluntario, Organizacion, Seguimiento, User, Comentario, Like, Notificacion
from django.db.models import F, ExpressionWrapper, IntegerField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Case, When, IntegerField, Value
from .models import Post, Organizacion, Etiqueta


@login_required # Asegura que solo usuarios logueados puedan acceder a esta vista
def feed_view(request):
    #Vista que renderiza la plantilla principal del feed.
    #Pasa el objeto 'request' al contexto para acceder a 'request.user.id' en la plantilla.
    return render(request, 'feed.html', {'request': request})
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse

def normalizar_telefono(telefono):
    if telefono:
        numero = ''.join(filter(str.isdigit, telefono))
        if not numero.startswith('507'):
            numero = '507' + numero
        return numero
    return None
@login_required
@require_GET
def feed_api_view(request):
    usuario_actual = request.user

    limite = int(request.GET.get('limite', 10))
    offset = int(request.GET.get('offset', 0))

    # Obtener etiquetas favoritas del perfil (Voluntario u Organizacion)
    etiquetas_fav = []
    try:
        perfil = usuario_actual.voluntario
        etiquetas_fav = perfil.etiquetas_favoritas.all()
    except Exception:
        try:
            perfil = usuario_actual.organizacion
            etiquetas_fav = perfil.etiquetas_favoritas.all()
        except Exception:
            etiquetas_fav = []

    etiquetas_fav_ids = [e.id for e in etiquetas_fav]

    # Obtener etiquetas de posts en los que el usuario ha comentado
    comentarios = usuario_actual.comentarios_creados.select_related('post').prefetch_related('post__etiquetas')
    etiquetas_comentarios_ids = set()
    for c in comentarios:
        etiquetas_comentarios_ids.update(e.id for e in c.post.etiquetas.all())

    etiquetas_prioritarias_ids = set(etiquetas_fav_ids) | etiquetas_comentarios_ids

    # Queryset base
    posts_queryset = Post.objects.filter(esta_eliminado=False).select_related('autor').prefetch_related('etiquetas')

    if etiquetas_prioritarias_ids:
        condicion_prioridad = Case(
            When(etiquetas__id__in=etiquetas_prioritarias_ids, then=Value(1)),
            default=Value(0),
            output_field=IntegerField(),
        )
        posts_queryset = posts_queryset.annotate(
            prioridad=condicion_prioridad
        ).order_by('-prioridad', '-fecha_creacion').distinct()
    else:
        posts_queryset = posts_queryset.order_by('-fecha_creacion')

    total_posts = posts_queryset.count()
    posts_a_devolver = posts_queryset[offset:offset + limite]

    posts_data = []
    for post in posts_a_devolver:
        usuario_dio_like = post.likes_recibidos.filter(usuario=usuario_actual).exists()

        telefono_whatsapp = None
        es_organizacion = False
        try:
            organizacion = Organizacion.objects.get(user=post.autor)
            telefono_whatsapp = organizacion.telefono  # o llama a normalizar_telefono si tienes esa función
            es_organizacion = True
        except Organizacion.DoesNotExist:
            pass

        posts_data.append({
            'id': post.id,
            'contenido': post.contenido,
            'autor': post.autor.username,
            'autor_id': post.autor.id,
            'fecha_creacion': post.fecha_creacion.isoformat(),
            'conteo_likes': post.conteo_likes if hasattr(post, 'conteo_likes') else 0,
            'conteo_comentarios': post.conteo_comentarios if hasattr(post, 'conteo_comentarios') else 0,
            'etiquetas': [etiqueta.nombre for etiqueta in post.etiquetas.all()],
            'esta_eliminado': post.esta_eliminado,
            'usuario_dio_like': usuario_dio_like,
            'telefono_whatsapp': telefono_whatsapp,
            'es_organizacion': es_organizacion
        })

    hay_mas = (offset + limite) < total_posts

    return JsonResponse({
        'posts': posts_data,
        'hay_mas': hay_mas,
        'siguiente_offset': offset + limite if hay_mas else None
    })
@login_required
@require_POST
def crear_post(request):
    #API para crear una nueva publicación.
    try:
        data = json.loads(request.body)
        contenido = data.get('contenido')
        etiquetas_ids = data.get('etiquetas_ids', []) 

        if not contenido:
            return JsonResponse({'estado': 'error', 'mensaje': 'El contenido del post no puede estar vacío.'}, status=400)

        post = Post.objects.create(
            contenido=contenido,
            autor=request.user
        )

        if etiquetas_ids:
            etiquetas_para_post = Etiqueta.objects.filter(id__in=etiquetas_ids)
            post.etiquetas.set(etiquetas_para_post) # Asignar las etiquetas usando el método .set() del ManyToManyField
        
        return JsonResponse({'estado': 'exito', 'mensaje': 'Post creado exitosamente.', 'post_id': post.id})

    except json.JSONDecodeError:
        return JsonResponse({'estado': 'error', 'mensaje': 'Formato de JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al crear el post: {str(e)}'}, status=500)
    
@login_required
@require_http_methods(["DELETE"])
def eliminar_post(request, post_id):
    #API para marcar un post como eliminado.
    post = get_object_or_404(Post, id=post_id)

    if post.autor != request.user:
        return JsonResponse({'estado': 'error', 'mensaje': 'No tienes permiso para eliminar este post.'}, status=403)

    post.esta_eliminado = True
    post.save()

    return JsonResponse({'estado': 'exito', 'mensaje': 'Post eliminado.'})

@require_GET
def obtener_comentarios_de_post(request, post_id):
    #API para obtener los comentarios de un post específico,
    #incluyendo la información del post (incluso si está eliminado lógicamente).
    post = get_object_or_404(Post, id=post_id)

    post_data = {
        'id': post.id,
        'contenido': post.contenido,
        'autor': post.autor.username,
        'autor_id': post.autor.id,
        'fecha_creacion': post.fecha_creacion.isoformat(),
        'conteo_likes': post.conteo_likes,
        'conteo_comentarios': post.conteo_comentarios,
        'etiquetas': [etiqueta.nombre for etiqueta in post.etiquetas.all()],
        'esta_eliminado': post.esta_eliminado,
        'mensaje_eliminado': "Este post ha sido eliminado." if post.esta_eliminado else None,
    }

    comentarios_data = []
    for comentario in post.comentarios.all().select_related('autor').order_by('fecha_creacion'):
        comentarios_data.append({
            'id': comentario.id,
            'contenido': comentario.contenido,
            'autor': comentario.autor.username,
            'autor_id': comentario.autor.id,
            'fecha_creacion': comentario.fecha_creacion.isoformat(),
        })

    return JsonResponse({
        'post_info': post_data,
        'comentarios': comentarios_data
    })

@login_required
@require_POST
def crear_comentario(request):
    #API para crear un nuevo comentario en un post.
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        contenido = data.get('contenido')

        if not post_id or not contenido:
            return JsonResponse({'estado': 'error', 'mensaje': 'ID de post o contenido del comentario faltante.'}, status=400)
        
        post = get_object_or_404(Post, id=post_id)

        comentario = Comentario.objects.create(
            post=post,
            autor=request.user,
            contenido=contenido
        )

        # Actualizar conteo de comentarios en el Post
        post.conteo_comentarios = post.comentarios.count()
        post.save()

        return JsonResponse({'estado': 'exito', 'mensaje': 'Comentario creado exitosamente.', 'comentario_id': comentario.id})

    except json.JSONDecodeError:
        return JsonResponse({'estado': 'error', 'mensaje': 'Formato de JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al crear el comentario: {str(e)}'}, status=500)
    
@login_required
@require_http_methods(["DELETE"])
def eliminar_comentario(request, comentario_id):
    #API para eliminar un comentario.
    comentario = get_object_or_404(Comentario, id=comentario_id)

    if comentario.autor != request.user:
        return JsonResponse({'estado': 'error', 'mensaje': 'No tienes permiso para eliminar este comentario.'}, status=403)

    if comentario.post and not comentario.post.esta_eliminado:
        post = comentario.post
        comentario.delete()
        post.conteo_comentarios = post.comentarios.count()
        post.save()
    else:
        comentario.delete()

    return JsonResponse({'estado': 'exito', 'mensaje': 'Comentario eliminado exitosamente.'})

@login_required
@require_GET
def obtener_perfil_usuario(request, user_id):
    """
    API para obtener los detalles de un usuario (Voluntario/Organizacion)
    incluyendo sus seguidos, seguidores y el conteo total de actividad.
    También indica si el usuario actual sigue a este perfil.
    """
    try:
        user_profile = get_object_or_404(User, id=user_id)
        
        perfil_data = {
            'id': user_profile.id,
            'username': user_profile.username,
            'es_voluntario': False,
            'es_organizacion': False,
            'etiquetas_favoritas': [],
            'seguidos_ids': [],
            'seguidores_ids': [],
            'posts': 0
        }
        
        if hasattr(user_profile, 'voluntario'):
            perfil = user_profile.voluntario
            perfil_data['es_voluntario'] = True
            perfil_data['etiquetas_favoritas'] = [e.nombre for e in perfil.etiquetas_favoritas.all()]
            perfil_data['seguidos_ids'] = [u.id for u in perfil.seguidos]
            perfil_data['seguidores_ids'] = [u.id for u in perfil.seguidores]
            perfil_data['posts'] = perfil.posts
        elif hasattr(user_profile, 'organizacion'):
            perfil = user_profile.organizacion
            perfil_data['es_organizacion'] = True
            perfil_data['etiquetas_favoritas'] = [e.nombre for e in perfil.etiquetas_favoritas.all()]
            perfil_data['seguidos_ids'] = [u.id for u in perfil.seguidos]
            perfil_data['seguidores_ids'] = [u.id for u in perfil.seguidores]
            perfil_data['posts'] = perfil.posts


        
        perfil_data['esta_siguiendo'] = Seguimiento.objects.filter(seguidor=request.user, seguido=user_profile).exists()

        return JsonResponse(perfil_data)

    except User.DoesNotExist:
        return JsonResponse({'estado': 'error', 'mensaje': 'Usuario no encontrado.'}, status=404)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al obtener el perfil: {str(e)}'}, status=500)
    
@login_required
@require_POST
def alternar_seguimiento_usuario(request):
    #API para seguir o dejar de seguir a un usuario.
    try:
        data = json.loads(request.body)
        usuario_id_a_seguir = data.get('usuario_id')

        if not usuario_id_a_seguir:
            return JsonResponse({'estado': 'error', 'mensaje': 'ID de usuario a seguir no proporcionado.'}, status=400)

        usuario_a_seguir = get_object_or_404(User, id=usuario_id_a_seguir)

        if request.user == usuario_a_seguir:
            return JsonResponse({'estado': 'error', 'mensaje': 'No puedes seguirte a ti mismo.'}, status=400)

        seguimiento, created = Seguimiento.objects.get_or_create(seguidor=request.user, seguido=usuario_a_seguir)

        if not created:
            seguimiento.delete()
            return JsonResponse({'estado': 'exito', 'mensaje': f'Dejaste de seguir a {usuario_a_seguir.username}.'})
        else:
            Notificacion.objects.create(
                recipiente=usuario_a_seguir,  # El usuario que FUE seguido (el que recibe la notificación)
                actor=request.user,          # El usuario que REALIZÓ la acción de seguir
                notification_type='follow',  # El tipo de notificación
                message=f"{request.user.username} te ha empezado a seguir.", # Mensaje personalizado
                link=f"/usuarios/{request.user.id}/" # Enlace al perfil del seguidor (ajusta si tu URL de perfil es diferente)
            )
            return JsonResponse({'estado': 'exito', 'mensaje': f'Ahora sigues a {usuario_a_seguir.username}.'})

    except json.JSONDecodeError:
        return JsonResponse({'estado': 'error', 'mensaje': 'Formato de JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al alternar seguimiento: {str(e)}'}, status=500)
    
@login_required
def obtener_notificaciones(request):
    notificaciones = Notificacion.objects.filter(recipiente=request.user).select_related('actor')

    notificacion_list = []
    for notificacion in notificaciones:
        notificacion_list.append({
            'id': notificacion.id,
            'actor_username': notificacion.actor.username if notificacion.actor else 'Usuario desconocido',
            'actor_id': notificacion.actor.id if notificacion.actor else None,
            'notification_type': notificacion.notification_type,
            'message': notificacion.message,
            'link': notificacion.link,
            'fecha_creacion': notificacion.fecha_creacion.isoformat(),
            'leido': notificacion.leido
        })
    
    return JsonResponse({'notificaciones': notificacion_list})

@login_required 
@require_POST 
def marcar_notificacion_como_leida(request):
    try:
        data = json.loads(request.body)
        id_notificacion = data.get('id_notificacion')
        marcar_todo = data.get('marcar_todo', False)

        if marcar_todo:
            # Marca todas las notificaciones no leídas para el usuario actual como leídas
            Notificacion.objects.filter(recipiente=request.user, is_read=False).update(is_read=True)
            return JsonResponse({'estado': 'exito', 'mensaje': 'Todas las notificaciones han sido marcadas como leídas.'})
        elif id_notificacion:
            # Marca una notificación específica como leída
            notificacion = get_object_or_404(Notificacion, id=id_notificacion, recipiente=request.user)
            if not notificacion.is_read:
                notificacion.is_read = True
                notificacion.save()
            return JsonResponse({'estado': 'exito', 'mensaje': f'Notificación {id_notificacion} marcada como leída.'})
        else:
            return JsonResponse({'estado': 'error', 'mensaje': 'ID de notificación no proporcionado o parámetro "marcar_todo" es falso.'}, status=400)
    except json.JSONDecodeError:
        return JsonResponse({'estado': 'error', 'mensaje': 'Formato de JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al marcar notificación: {str(e)}'}, status=500)

def pagina_inicio(request):
    return render(request, 'inicio.html')

def registro(request):
    return render(request, 'registro.html')

def registro_voluntario(request):
    if request.method == 'POST':
        form = RegistroVoluntarioForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            # Crear perfil voluntario si no existe
            Voluntario.objects.get_or_create(user=usuario)
            # Iniciar sesión automático
            login(request, usuario)
            # Redirigir a seleccionar etiquetas
            return redirect('seleccionar_etiquetas')
    else:
        form = RegistroVoluntarioForm()
    return render(request, 'registro_voluntario.html', {'form': form})
def registro_organizacion(request):
    if request.method == 'POST':
        form = RegistroOrganizacionForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            Organizacion.objects.get_or_create(user=usuario)
            login(request, usuario)
            return redirect('seleccionar_etiquetas')
    else:
        form = RegistroOrganizacionForm()
    return render(request, 'registro_organizacion.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            # Revisa si es voluntario u organización
            if hasattr(user, 'voluntario') or hasattr(user, 'organizacion'):
                return redirect('feed')  # redirige al feed si tiene rol válido
            else:
                logout(request)
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Usuario no tiene rol asignado.'
                })
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})  # 👈 aquí va login.html



@login_required
def seleccionar_etiquetas(request):
    usuario = request.user
    perfil = None
    tipo = None

    try:
        perfil = Voluntario.objects.get(user=usuario)
        tipo = 'voluntario'
    except Voluntario.DoesNotExist:
        try:
            perfil = Organizacion.objects.get(user=usuario)
            tipo = 'organizacion'
        except Organizacion.DoesNotExist:
            perfil = Voluntario.objects.create(user=usuario)
            tipo = 'voluntario'

    etiquetas = Etiqueta.objects.all()

    if perfil is None:
        return render(request, 'error.html', {'mensaje': 'No se encontró el perfil del usuario.'})

    if request.method == 'POST':
        seleccionadas = request.POST.getlist('etiquetas')
        perfil.etiquetas_favoritas.set(seleccionadas)
        perfil.save()
        return redirect('feed') 

    return render(request, 'seleccionar_etiquetas.html', {
        'etiquetas': etiquetas,
        'perfil': perfil,
        'tipo': tipo
    })


# @login_required
# def feed(request):
#     #aqui hay que poner que agarre los posts, pero no han hecho lo de los posts
#     #asiq ta vacio

#     posts_populares = (
#         Post.objects.filter(esta_eliminado=False)
#         .annotate(popularidad=ExpressionWrapper(
#             F('conteo_likes') + F('conteo_comentarios') * 2, 
#             output_field=IntegerField()
#         ))
#         .order_by('-popularidad', '-fecha_creacion')[:3] 
#     )


#     return render(request, 'feed.html',{
#         'posts_populares': posts_populares,
#         'request': request
#     })

@login_required
def feed(request):
    # Ya no recuperamos posts populares ni solo organizaciones.
    # Ahora recuperamos a todos los usuarios activos.
    # Usamos .select_related() para precargar los perfiles de Organizacion y Voluntario
    # Esto es crucial para el rendimiento y evitar muchas consultas a la DB en el template.
    todos_los_usuarios_activos = User.objects.filter(is_active=True).order_by('username').select_related('organizacion', 'voluntario')
    
    # Preparamos una lista para los usuarios con su tipo de perfil
    usuarios_con_tipo = []
    for usuario in todos_los_usuarios_activos:
        # Excluimos al usuario actual de la lista de "Otros Usuarios" si no quieres que se vea a sí mismo
        if usuario == request.user:
            continue

        tipo_perfil = "Normal" # Por defecto, si no es ni organizacion ni voluntario
        
        # Verificar si es una organización
        if hasattr(usuario, 'organizacion') and usuario.organizacion is not None:
            tipo_perfil = "Organización"
        # Verificar si es un voluntario (si no fue ya una organización)
        elif hasattr(usuario, 'voluntario') and usuario.voluntario is not None:
            tipo_perfil = "Voluntario"
        
        usuarios_con_tipo.append({
            'user_obj': usuario,
            'tipo': tipo_perfil
        })

    return render(request, 'feed.html', {
        'usuarios_con_tipo': usuarios_con_tipo, # Nueva variable de contexto para el sidebar
        'request': request
    })

# QUITAR PONER LIKES
@login_required
@require_POST
def alternar_like_post(request):
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        post = get_object_or_404(Post, id=post_id)

        like, creado = Like.objects.get_or_create(usuario=request.user, post=post)
        if not creado:
            like.delete()
            post.conteo_likes = post.likes_recibidos.count()
            post.save()
            return JsonResponse({'estado': 'exito', 'liked': False})
        else:
            post.conteo_likes += 1
            post.save()
            return JsonResponse({'estado': 'exito', 'liked': True})
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al alternar like: {str(e)}'}, status=500)
    
def obtener_etiquetas_para_post(request):
    etiquetas = Etiqueta.objects.all().values('id', 'nombre').order_by('nombre')
    return JsonResponse(list(etiquetas), safe=False)
