
from django.contrib import admin
from .models import *

@admin.register(Etiqueta)
class EtiquetaAdmin(admin.ModelAdmin):
    list_display = ('nombre',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('content', 'author', 'fecha_creacion', 'conteo_likes', 'conteo_comentarios')
    list_filter = ('fecha_creacion', 'author')

    def conteo_likes(self, obj):
        return obj.likes.count()

    def conteo_comentarios(self, obj):
        return obj.comments.count()

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('post', 'author', 'content', 'fecha_creacion')
    list_filter = ('fecha_creacion', 'author')
    raw_id_fields = ('post', 'author')

@admin.register(Voluntario)
class VoluntarioAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombre', 'latitud', 'longitud', 'mostrar_etiquetas')

    def mostrar_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas_favoritas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas Favoritas'


@admin.register(Organizacion)
class OrganizacionAdmin(admin.ModelAdmin):
    list_display = ('user', 'nombre', 'latitud', 'longitud')
    def mostrar_etiquetas(self, obj):
        return ", ".join([e.nombre for e in obj.etiquetas_favoritas.all()])
    mostrar_etiquetas.short_description = 'Etiquetas Favoritas'

@admin.register(Seguimiento)
class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('seguidor', 'seguido', 'fecha_seguimiento')
    list_filter = ('fecha_seguimiento',)
    search_fields = ('seguidor__username', 'seguido__username') # Permite buscar por nombre de usuario