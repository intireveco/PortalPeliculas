from django.db import models




from django.db import models

class Pelicula(models.Model):
    ESTADO_CHOICES = [
        ('VISTA', 'Ya la vi completa'),
        ('PROGRESO', 'La estoy viendo'),
        ('PENDIENTE', 'Pendiente'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    director = models.CharField(max_length=150, verbose_name="Director", blank=True, null=True)
    anio = models.IntegerField(verbose_name="Año de estreno", blank=True, null=True)
    poster_url = models.URLField(max_length=500, verbose_name="URL de Carátula", blank=True, null=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado")

    class Meta:
        ordering = ['-anio']

    def __str__(self):
        return f"{self.titulo} ({self.anio})"
