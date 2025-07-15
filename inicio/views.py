from django.shortcuts import render, redirect
from .forms import RegistroOrganizacionForm, RegistroVoluntarioForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .models import Etiqueta, Voluntario, Organizacion


def pagina_inicio(request):
    return render(request, 'inicio.html')

def registro(request):
    return render(request, 'registro.html')

def registro_voluntario(request):
    if request.method == 'POST':
        form = RegistroVoluntarioForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('seleccionar_etiquetas')
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
                return redirect('pagina_inicio')  # redirige a la vista de selección de etiquetas
            else:
                logout(request)
                return render(request, 'login.html', {
                    'form': form,
                    'error': 'Usuario no tiene rol asignado.'
                })
    else:
        form = AuthenticationForm()
    return render(request, 'login.html', {'form': form})



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