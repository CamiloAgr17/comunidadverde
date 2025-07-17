from django.shortcuts import render
from .models import CentroReciclaje
from django.utils.safestring import mark_safe
import json
from inicio.models import Organizacion

def mapa_view(request):
    organizaciones_qs = Organizacion.objects.exclude(latitud__isnull=True, longitud__isnull=True)\
        .values('nombre', 'latitud', 'longitud')
    
    organizaciones = []
    for org in organizaciones_qs:
         organizaciones.append({
            'nombre': org['nombre'],
            'latitud': float(org['latitud']),
            'longitud': float(org['longitud']),
        })

    organizaciones_json = mark_safe(json.dumps(list(organizaciones)))
    return render(request, "mapa/index.html", {"organizaciones_json": organizaciones_json})


