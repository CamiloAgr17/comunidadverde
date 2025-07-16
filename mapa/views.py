from django.shortcuts import render
from .models import CentroReciclaje
from django.utils.safestring import mark_safe
import json

def mapa_view(request):
    centros = CentroReciclaje.objects.all().values('nombre', 'lat', 'lng', 'materiales')
    centros_json = mark_safe(json.dumps(list(centros)))
    return render(request, "mapa/index.html", {"centros_json": centros_json})
