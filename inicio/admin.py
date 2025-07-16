
from django.contrib import admin
from .models import Organizacion, Voluntario, Etiqueta, Post, Comentario, Seguimiento

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('contenido', 'autor', 'fecha_creacion', 'conteo_likes', 'conteo_comentarios', 'esta_eliminado')
    list_filter = ('fecha_creacion', 'autor', 'etiquetas')

@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('post', 'autor', 'contenido', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'autor', 'post')
    search_fields = ('contenido', 'autor__username')
    raw_id_fields = ('post', 'autor')

@admin.register(Voluntario)
class VoluntarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nombre', 'latitud', 'longitud', 'mostrar_etiquetas')

    def mostrar_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas_favoritas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas Favoritas'


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'nombre', 'descripcion', 'telefono', 'latitud', 'longitud', 'mostrar_etiquetas')

    def mostrar_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas_favoritas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas Favoritas'

@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('seguidor', 'seguido', 'fecha_seguimiento')
    list_filter = ('fecha_seguimiento',)
    search_fields = ('seguidor__username', 'seguido__username') # Permite buscar por nombre de usuario