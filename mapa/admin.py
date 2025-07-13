from django.contrib import admin
from .models import CentroReciclaje

@admin.register(CentroReciclaje)
class CentroAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'lat', 'lng', 'materiales')

