
from django.contrib import admin
from .models import Organizacion, Voluntario
from .models import Etiqueta
@admin.register(Voluntario)
class VoluntarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombre', 'latitud', 'longitud', 'mostrar_etiquetas')

    def mostrar_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas_favoritas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas Favoritas'


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombre', 'telefono', 'latitud', 'longitud', 'mostrar_etiquetas')

    def mostrar_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas_favoritas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas Favoritas'


@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)