from django.shortcuts import render
from .models import CentroReciclaje

def mapa_view(request):
    centros = CentroReciclaje.objects.all()
    return render(request, 'mapa/index.html', {'centros': centros})