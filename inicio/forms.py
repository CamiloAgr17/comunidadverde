from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *
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
    

## FORMULARIO PARA EL POST V1
# class PostForm(forms.ModelForm):
#     class Meta:
#         model = Post
#         fields = ['etiquetas', 'content']
#         widgets = {
#             'etiquetas': forms.SelectMultiple(attrs={ 
#                 'class': 'form-control', 
#                 'placeholder': 'Selecciona etiquetas', 
#                 'size': '5' 
#             }),

#             'content': forms.Textarea(attrs={
#                 'rows': 3, 
#                 'placeholder': 'Escribe tu publicación aquí...',
#                 'class': 'modal-textarea'
#                 })
#         }
#         labels = {
#             'etiquetas': 'Etiquetas',
#             'content': ' '
#         }

## FORMULARIO PARA EL POST V2
class PostForm(forms.ModelForm):
    # Override the 'etiquetas' field to customize its queryset and widget
    etiquetas = forms.ModelMultipleChoiceField(
        queryset=Etiqueta.objects.all(), # Always start with all tags
        required=False, # Make it not strictly required if tags are optional
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'size': '1'
        })
        # REMOVE 'empty_label' from here, it causes the TypeError for SelectMultiple
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # === Add this logic to dynamically set options if no tags exist ===
        if not self.fields['etiquetas'].queryset.exists():
            # If no tags exist, we want a single non-selectable option
            self.fields['etiquetas'].choices = [('', 'No hay etiquetas disponibles en este momento')]
            self.fields['etiquetas'].widget.attrs['disabled'] = 'disabled' # Make the select box disabled
            # You might also want to set required=False explicitly here if not already,
            # to ensure the form can be submitted without selecting tags when none exist.
            self.fields['etiquetas'].required = False

    class Meta:
        model = Post
        fields = ['etiquetas', 'content']

        widgets = {
            # 'etiquetas': No longer needed here as we define it directly above
            'content': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Escribe tu publicación aquí...',
                'class': 'modal-textarea',
            })
        }
        labels = {
            'etiquetas': 'Etiquetas',
            'content': ''
        }

    # Optional: If you want to force selection if there *are* tags
    # def clean_etiquetas(self):
    #     etiquetas = self.cleaned_data.get('etiquetas')
    #     # Only apply this validation if the queryset originally had tags
    #     if Etiqueta.objects.exists() and not etiquetas:
    #         raise forms.ValidationError("Debes seleccionar al menos una etiqueta si hay disponibles.")
    #     return etiquetas


## COMENTARIOS
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Añadir un comentario...',
                'class': 'comment-textarea',
                }),
        }

        labels = {
            'content': ''
        }
