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
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name='posts')  # sin null ni max_length
    conteo_likes = models.IntegerField(default=0)
    conteo_comentarios = models.IntegerField(default=0)
    esta_eliminado = models.BooleanField(default=False)

    def delete(self, *args, **kwargs):
        self.esta_eliminado = True  # corregido is_deleted a esta_eliminado
        self.save()

    class Meta:
        ordering = ['-fecha_creacion']  # Orden por defecto

    def __str__(self):
        status = "(Eliminado)" if self.esta_eliminado else ""
        return f"Post de {self.autor.username}: {self.contenido[:70]}... {status}"


class Comentario(models.Model):
    post = models.ForeignKey(Post, on_delete=models.SET_NULL, null=True, related_name='comentarios')
    autor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios_creados')
    contenido = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_creacion']
        verbose_name_plural = "Comentarios"

    def __str__(self):
        return f"Comentario de {self.autor.username} en Post {self.post.id}: {self.contenido[:30]}..."


class Voluntario(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    etiquetas_favoritas = models.ManyToManyField(Etiqueta, blank=True)

    @property
    def posts(self):
        conteo_posts = self.user.posts_creados.count()
        conteo_comentarios = self.user.comentarios_creados.count()
        return conteo_posts + conteo_comentarios

    @property
    def seguidos(self):
        return User.objects.filter(seguidores__seguidor=self.user)

    @property
    def seguidores(self):
        return User.objects.filter(seguidos__seguido=self.user)

    def __str__(self):
        return self.nombre


class Organizacion(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(max_length=500, default="")
    telefono = models.CharField(max_length=20)
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    etiquetas_favoritas = models.ManyToManyField(Etiqueta, blank=True)

    @property
    def posts(self):
        conteo_posts = self.user.posts_creados.filter(esta_eliminado=False).count()
        conteo_comentarios = self.user.comentarios_creados.count()
        return conteo_posts + conteo_comentarios

    @property
    def seguidos(self):
        return User.objects.filter(seguidores__seguidor=self.user)

    @property
    def seguidores(self):
        return User.objects.filter(seguidos__seguido=self.user)

    class Meta:
        verbose_name_plural = "Organizaciones"

    def __str__(self):
        return self.nombre


class Seguimiento(models.Model):
    seguidor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seguidos')
    seguido = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seguidores')
    fecha_seguimiento = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('seguidor', 'seguido')

    def __str__(self):
        return f"{self.seguidor.username} sigue a {self.seguido.username}"
    
class Notificacion(models.Model):
    # El usuario que debe recibir la notificación (ej. el que fue seguido)
    recipiente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notificaciones')
    
    # El usuario que realizó la acción que generó la notificación (ej. el que siguió)
    actor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='actions_made', null=True, blank=True)
    
    # Tipo de notificación. 'follow' es el que usaremos ahora.
    TIPO_NOTIFICACION = (
        ('follow', 'Nuevo seguidor'),
        # Para añadir más tipos aquí en el futuro (ej. 'like', 'comment')
    )
    notification_type = models.CharField(max_length=20, choices=TIPO_NOTIFICACION)
    
    # Mensaje opcional para la notificación (ej. "usuarioX te ha empezado a seguir")
    message = models.TextField(blank=True, null=True)
    
    # Enlace asociado a la notificación (ej. al perfil del 'actor')
    link = models.CharField(max_length=255, blank=True, null=True)
    
    # Fecha y hora en que se creó la notificación
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Indica si el usuario ha leído o visto esta notificación
    leido = models.BooleanField(default=False)

    class Meta:
        # Ordena las notificaciones de la más nueva a la más antigua por defecto
        ordering = ['-fecha_creacion'] 

    class Meta:
        verbose_name_plural = "Notificaciones"

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'Usuario desconocido'
        return f"Notificación para {self.recipiente.username} ({self.get_notification_type_display()} por {actor_name})"

# Likes para los posts
class Like(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes_dados')
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='likes_recibidos')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'post')  # evita duplicados

    def __str__(self):
        return f"{self.usuario.username} le dio like al post {self.post.id}"
