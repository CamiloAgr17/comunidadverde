from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST, require_http_methods
from .forms import RegistroOrganizacionForm, RegistroVoluntarioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
import json
from .models import Post, Etiqueta, Voluntario, Organizacion, Seguimiento, User, Comment, Like
from django.db.models import F, ExpressionWrapper, IntegerField
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.http import JsonResponse
from django.db.models import Case, When, IntegerField, Value
from .models import Post, Organizacion, Etiqueta
from .forms import *


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

@login_required
def feed(request):
    posts = Post.objects.all().order_by('-fecha_creacion').prefetch_related('comments', 'likes')
    user_likes = Like.objects.filter(usuario=request.user).values_list('post_id', flat=True)
    form = PostForm() 

    # posts populares
    popular_posts = Post.objects.annotate(
        total_likes=Count('likes'),
        total_comments=Count('comments')
    ).order_by('-total_likes', '-total_comments')[:3]

    # posts no eliminados del usuario
    posts_no_eliminados = Post.objects.filter(
        author=request.user,
        esta_eliminado=False
    ).count()

    # seguidores
    user_followers_count = Seguimiento.objects.filter(seguido=request.user).count()

    # seguidos
    user_following_count = Seguimiento.objects.filter(seguidor=request.user).count()

    comment_forms_errors = {}

    if request.method == 'POST':
        # Intentar procesar el formulario de comentario
        if 'post_id' in request.POST:
            post_id = request.POST.get('post_id')
            post_to_comment = get_object_or_404(Post, id=post_id)
            comment_form_instance = CommentForm(request.POST)

            if comment_form_instance.is_valid():
                comment = comment_form_instance.save(commit=False)
                comment.post = post_to_comment
                comment.author = request.user
                comment.save()
                return redirect('feed') 
            else:
                comment_forms_errors[int(post_id)] = comment_form_instance

    for post in posts:
        post.comment_form = comment_forms_errors.get(post.id, CommentForm())

    context = {
        'posts': posts,
        'form': form,
        'user_likes': set(user_likes),
        'popular_posts': popular_posts,
        'posts_no_eliminados': posts_no_eliminados,
        'user_followers_count': user_followers_count,
        'user_following_count': user_following_count,
    }
    return render(request, 'feed.html', context)

def obtener_etiquetas_para_post(request):
    etiquetas = Etiqueta.objects.all().values('id', 'nombre').order_by('nombre')
    return JsonResponse(list(etiquetas), safe=False)


## VISTA PARA LOS POSTS
@login_required
def crear_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST) 
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            # Guardar las etiquetas seleccionadas
            form.save_m2m() 
            return redirect('feed')
        else:
            # Si el formulario no es válido, renderiza de nuevo con errores
            posts = Post.objects.all().order_by('-fecha_creacion')
            context = {
                'posts': posts,
                'form': form, 
            }
            return render(request, 'feed.html', context)
    else:
        # Si no es un POST, simplemente muestra el formulario vacío
        form = PostForm()
        posts = Post.objects.all().order_by('-fecha_creacion')
        return render(request, 'feed.html', {'form': form, 'posts': posts})

## LIKES
@require_POST
@login_required
def toggle_like_ajax(request):  # ✅ SIN post_id aquí
    post_id = request.POST.get('post_id')

    if not post_id:
        return JsonResponse({'error': 'Falta post_id'}, status=400)

    post = get_object_or_404(Post, id=post_id)

    like, created = Like.objects.get_or_create(post=post, usuario=request.user)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        'liked': liked,
        'total_likes': post.total_likes()
    })

##Obtener INFO de usuario
@login_required
def get_user_profile_data(request, user_id):
    user_to_view = get_object_or_404(User, id=user_id)

    # Contar posts no eliminados del usuario
    post_count = Post.objects.filter(author=user_to_view, esta_eliminado=False).count()

    # Contar seguidores y seguidos
    followers_count = Seguimiento.objects.filter(seguido=user_to_view).count()
    following_count = Seguimiento.objects.filter(seguidor=user_to_view).count()

    # Verificar si el usuario logueado sigue al usuario que se está viendo
    is_following = False
    if request.user.is_authenticated:
        is_following = Seguimiento.objects.filter(
            seguidor=request.user,
            seguido=user_to_view
        ).exists()

    data = {
        'username': user_to_view.username,
        'post_count': post_count,
        'followers_count': followers_count,
        'following_count': following_count,
        'is_following': is_following,
    }
    return JsonResponse(data)

## Follow o Unfollow
@login_required
def toggle_follow(request, user_id):
    if request.method == 'POST':
        user_to_follow = get_object_or_404(User, id=user_id)
        current_user = request.user

        # No se puede seguir a uno mismo
        if current_user == user_to_follow:
            return JsonResponse({'status': 'error', 'message': 'No puedes seguirte a ti mismo.'}, status=400)

        # Verificar si ya se siguen
        follow_exists = Seguimiento.objects.filter(
            seguidor=current_user,
            seguido=user_to_follow
        )

        is_following = False
        if follow_exists.exists():
            # Si ya se siguen, borrar el seguimiento (dejar de seguir)
            follow_exists.delete()
            is_following = False
            message = f'Has dejado de seguir a {user_to_follow.username}'
        else:
            # Si no se siguen, crear el seguimiento (seguir)
            Seguimiento.objects.create(seguidor=current_user, seguido=user_to_follow)
            is_following = True
            message = f'Ahora sigues a {user_to_follow.username}'
        
        # Recalcular seguidores del usuario que se sigue para actualizar el modal
        followers_count = Seguimiento.objects.filter(seguido=user_to_follow).count()


        return JsonResponse({
            'status': 'success',
            'is_following': is_following,
            'followers_count': followers_count,
            'message': message
        })
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)