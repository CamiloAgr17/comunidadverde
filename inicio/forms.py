from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Voluntario, Organizacion
from django.contrib.auth.forms import AuthenticationForm
from mapa.models import CentroReciclaje


class RegistroVoluntarioForm(UserCreationForm):
    nombre = forms.CharField(max_length=100, required=True)
    latitud = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    longitud = forms.DecimalField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'nombre', 'latitud', 'longitud']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            voluntario = Voluntario.objects.create(
                user=user,
                nombre=self.cleaned_data['nombre'],
                latitud=self.cleaned_data['latitud'],
                longitud=self.cleaned_data['longitud']
            )
            if voluntario.latitud and voluntario.longitud:
                CentroReciclaje.objects.create(
                    nombre=voluntario.nombre,
                    lat=voluntario.latitud,
                    lng=voluntario.longitud,
                    materiales="Voluntario"
                )
        return user

class RegistroOrganizacionForm(UserCreationForm):
    nombre = forms.CharField(max_length=100, required=True)
    telefono = forms.CharField(max_length=20, required=True)
    latitud = forms.DecimalField(widget=forms.HiddenInput(), required=False)
    longitud = forms.DecimalField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'nombre', 'telefono', 'latitud', 'longitud']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            organizacion = Organizacion.objects.create(
                user=user,
                nombre=self.cleaned_data['nombre'],
                telefono=self.cleaned_data['telefono'],
                latitud=self.cleaned_data['latitud'],
                longitud=self.cleaned_data['longitud']
            )
            if organizacion.latitud and organizacion.longitud:
                CentroReciclaje.objects.create(
                    nombre=organizacion.nombre,
                    lat=organizacion.latitud,
                    lng=organizacion.longitud,
                    materiales="Organización"
                )
        return user
