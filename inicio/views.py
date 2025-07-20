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
            return redirect('feed')  # Redirige al feed después de crear el post
    else:
        form = PostForm()
    return render(request, 'crear_post.html', {'form': form})
