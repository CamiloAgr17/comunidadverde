from django.db import models

class CentroReciclaje(models.Model):
    nombre = models.CharField(max_length=100)
    lat = models.FloatField()  # Latitud
    lng = models.FloatField()  # Longitud
    materiales = models.CharField(max_length=200)  # Ej: "plástico, vidrio"

    def __str__(self):
        return self.nombre