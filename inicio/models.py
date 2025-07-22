from django.contrib.auth.models import User
from django.db import models


class Etiqueta(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


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

## MODELO POSTS

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=280, blank=False, null=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    etiquetas = models.ManyToManyField(Etiqueta, blank=True, related_name='posts')
    esta_eliminado = models.BooleanField(default=False)

    def total_likes(self):
        return self.likes.count()

    def total_comments(self):
        return self.comments.count()

    def popularity_score(self):
        return self.total_likes() + self.total_comments()

    def __str__(self):
        return f'{self.author.username}: {self.content[:30]}'
    
## MODELO COMENTARIOS
class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField(max_length=200)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    esta_eliminado = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.author.username} on Post {self.post.id}'
    
## MODELO LIKES
class Like(models.Model):
    post = models.ForeignKey(Post, related_name='likes', on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('post', 'usuario') 

    def __str__(self):
        return f'{self.usuario.username} likes Post {self.post.id}'
    
## MODELO NOTIFICACIONES
class Notification(models.Model):
    # El usuario que recibe la notificación (el que fue seguido)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    # El usuario que causó la notificación (el que siguió)
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    NOTIFICATION_TYPES = (
        ('follow', 'Seguimiento'),
        ('like', 'Me Gusta'),
        ('comment', 'Comentario'),
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='follow' # Puedes establecer un valor por defecto si lo deseas
    )

    # Relación de la notificación con algún post
    post = models.ForeignKey('Post', on_delete=models.CASCADE, null=True, blank=True)
    # Mensaje de la notificación (ej. "UsuarioX te ha seguido")
    message = models.CharField(max_length=255)
    # Fecha y hora de creación de la notificación
    created_at = models.DateTimeField(auto_now_add=True)
    # Si la notificación ha sido leída por el usuario
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at'] # Ordenar las notificaciones de las más nuevas a las más antiguas

    def __str__(self):
        return f"Notificación para {self.user.username} de {self.from_user.username}: {self.message}"