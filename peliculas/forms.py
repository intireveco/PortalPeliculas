from django import forms

from .models import Calificacion, HistorialVisualizacion


class CalificacionForm(forms.ModelForm):
    class Meta:
        model = Calificacion
        fields = ['puntuacion', 'comentario']
        widgets = {
            'puntuacion': forms.Select(choices=[(n, f'{n} ★') for n in range(1, 6)]),
            'comentario': forms.Textarea(attrs={'rows': 3, 'placeholder': '¿Qué te pareció? (opcional)'}),
        }

    def clean_comentario(self):
        comentario = self.cleaned_data.get('comentario', '').strip()  # quitamos espacios sobrantes
        if len(comentario) > 500:
            raise forms.ValidationError('El comentario no puede superar los 500 caracteres.')
        return comentario


class VisualizacionForm(forms.ModelForm):
    class Meta:
        model = HistorialVisualizacion
        fields = ['minutos_visto']

    def clean_minutos_visto(self):
        minutos = self.cleaned_data['minutos_visto']
        # La vista asigna la película antes de validar (form.instance.pelicula)
        duracion = self.instance.pelicula.duracion
        if minutos > duracion:
            raise forms.ValidationError(f'La película dura {duracion} minutos; no puedes ver más que eso.')
        return minutos
