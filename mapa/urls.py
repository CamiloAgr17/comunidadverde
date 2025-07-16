from django.urls import path
from . import views

urlpatterns = [
    path('mapa/', views.mapa_view, name='mapa'),
]