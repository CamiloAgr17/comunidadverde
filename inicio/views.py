from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import RegistroOrganizacionForm, RegistroVoluntarioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import json
from .models import Post, Etiqueta, Voluntario, Organizacion, Seguimiento, User, Comentario

@login_required # Asegura que solo usuarios logueados puedan acceder a esta vista
def feed_view(request):
    #Vista que renderiza la plantilla principal del feed.
    #Pasa el objeto 'request' al contexto para acceder a 'request.user.id' en la plantilla.
    return render(request, 'feed.html', {'request': request})

@login_required
@require_GET
def feed_api_view(request):
 
    # API para obtener el feed de publicaciones del usuario, con scroll infinito.
    # Solo muestra posts no eliminados lógicamente.
    usuario_actual = request.user
    
    # Parámetros para el scroll infinito: 'offset' y 'limite'
    limite = int(request.GET.get('limite', 10)) # Cuántos posts cargar por vez
    offset = int(request.GET.get('offset', 0)) # Desde qué posición empezar

    # Consulta base para los posts: solo incluimos posts NO eliminados
    # Ordenamos por fecha de creación descendente para mostrar los más recientes primero
    posts_queryset = Post.objects.filter(esta_eliminado=False).select_related('autor').prefetch_related('etiquetas').order_by('-fecha_creacion')

    # Aplicar offset y limite para la paginación del scroll
    posts_a_devolver = posts_queryset[offset:offset + limite]

    posts_data = []
    for post in posts_a_devolver:
        posts_data.append({
            'id': post.id,
            'contenido': post.contenido,
            'autor': post.autor.username,
            'autor_id': post.autor.id,
            'fecha_creacion': post.fecha_creacion.isoformat(),
            'conteo_likes': post.conteo_likes,
            'conteo_comentarios': post.conteo_comentarios,
            'etiquetas': [etiqueta.nombre for etiqueta in post.etiquetas.all()],
            'esta_eliminado': post.esta_eliminado
        })
    
    # Indicar si hay más posts disponibles para cargar
    hay_mas = (offset + limite) < posts_queryset.count()

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

        if not contenido:
            return JsonResponse({'estado': 'error', 'mensaje': 'El contenido del post no puede estar vacío.'}, status=400)

        post = Post.objects.create(
            contenido=contenido,
            autor=request.user
        )
        
        return JsonResponse({'estado': 'exito', 'mensaje': 'Post creado exitosamente.', 'post_id': post.id})

    except json.JSONDecodeError:
        return JsonResponse({'estado': 'error', 'mensaje': 'Formato de JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al crear el post: {str(e)}'}, status=500)
    
@login_required
@require_http_methods(["DELETE"])
def eliminar_post(request, post_id):
    #API para marcar un post como eliminado lógicamente.
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
    """
    API para seguir o dejar de seguir a un usuario.
    """
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
            return JsonResponse({'estado': 'exito', 'mensaje': f'Ahora sigues a {usuario_a_seguir.username}.'})

    except json.JSONDecodeError:
        return JsonResponse({'estado': 'error', 'mensaje': 'Formato de JSON inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'estado': 'error', 'mensaje': f'Error al alternar seguimiento: {str(e)}'}, status=500)

def pagina_inicio(request):
    return render(request, 'inicio.html')

def registro(request):
    return render(request, 'registro.html')

def registro_voluntario(request):
    if request.method == 'POST':
        form = RegistroVoluntarioForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'seleccionar_etiquetas.html', {'form': form})
    else:
        form = RegistroVoluntarioForm()
    return render(request, 'registro_voluntario.html', {'form': form})

def registro_organizacion(request):
    if request.method == 'POST':
        form = RegistroOrganizacionForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request, 'seleccionar_etiquetas.html', {'form': form})
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
                return redirect('feed')  # redirige al feed
            else:
                logout(request)
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Usuario no tiene rol asignado.'
                })
    else:
        form = AuthenticationForm()
    return render(request, 'feed.html', {'form': form})



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
            perfil = None

    etiquetas = Etiqueta.objects.all()

    if perfil is None:
        return render(request, 'error.html', {'mensaje': 'No se encontró el perfil del usuario.'})

    if request.method == 'POST':
        seleccionadas = request.POST.getlist('etiquetas')
        perfil.etiquetas_favoritas.set(seleccionadas) 
        perfil.save()
        return redirect('pagina_inicio')

    return render(request, 'seleccionar_etiquetas.html', {
        'etiquetas': etiquetas,
        'perfil': perfil,
        'tipo': tipo
    })


@login_required
def feed(request):
    #aqui hay que poner que agarre los posts, pero no han hecho lo de los posts
    #asiq ta vacio
    return render(request, 'feed.html',)