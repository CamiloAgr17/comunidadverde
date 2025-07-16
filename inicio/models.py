from django.contrib.auth.models import User
from django.db import models


class Etiqueta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class Post(models.Model):
    contenido = models.TextField()
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts_creados')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    etiquetas = models.ManyToManyField(Etiqueta, null=True, max_length=100, related_name='posts')
    conteo_likes = models.IntegerField(default=0)
    conteo_comentarios = models.IntegerField(default=0)
    esta_eliminado = models.BooleanField(default=False)
    def delete(self, *args  , **kwargs):
        self.is_deleted = True
        self.save()

    class Meta:
        ordering = ['-fecha_creacion'] # Orden por defecto, aunque lo sobrescribiremos en la vista

    def __str__(self):
         status = "(Eliminado)" if self.esta_eliminado else ""
         return f"Post de {self.author.username}: {self.content[:70]}... {status}"
    
class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_creados')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_creacion']
        verbose_name_plural = "Comentarios"

    def __str__(self):
        return f"Comentario de {self.author.username} en Post {self.post.id}: {self.contenido[:30]}..."


class Voluntario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    etiquetas_favoritas = models.ManyToManyField(Etiqueta, blank=True)

#Propiedad para contar los posts y comentarios
    @property
    def posts(self):
        conteo_posts = self.usuario.posts_creados.count()
        conteo_comentarios = self.usuario.comentarios_creados.count()
        return conteo_posts + conteo_comentarios

    @property
    def seguidos(self):
        # Usuarios que esté siguiendo
        return User.objects.filter(seguidores__seguidor=self.usuario)
    
    @property
    def seguidores(self):
        # Usuarios que le estén siguiendo
        return User.objects.filter(seguidos__seguido=self.usuario)
    
    def __str__(self):
        return self.nombre

class Organizacion(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500, default="")
    telefono = models.CharField(max_length=20)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    etiquetas_favoritas = models.ManyToManyField(Etiqueta, blank=True)

# Propiedad para contar los posts y comentarios
    @property
    def posts(self):
        conteo_posts = self.usuario.posts_creados.filter(esta_eliminado=False).count()
        conteo_comentarios = self.usuario.comentarios_creados.count()
        return conteo_posts + conteo_comentarios
    
# Usuarios que esté siguiendo
    @property
    def seguidos(self):
        return User.objects.filter(seguidores__seguidor=self.usuario)

# Usuarios que le estén siguiendo
    @property
    def seguidores(self):
        return User.objects.filter(seguidos__seguido=self.usuario)

    class Meta:
        verbose_name_plural = "Organizaciones" #Para que salga bien el nombre en el admin

    def __str__(self):
        return self.nombre

# Relación de seguimiento
class Seguimiento(models.Model):
    seguidor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seguidos')
    seguido = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seguidores')
    fecha_seguimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Asegura que un usuario solo pueda seguir a otro una vez
        unique_together = ('seguidor', 'seguido')

    def __str__(self):
        return f"{self.seguidor.username} sigue a {self.seguido.username}"