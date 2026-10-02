from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg
from django.urls import reverse


class Director(models.Model):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre")
    nacionalidad = models.CharField(max_length=100, blank=True, verbose_name="Nacionalidad")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = "Directores"

    def __str__(self):
        return self.nombre


class Pelicula(models.Model):
    ESTADO_CHOICES = [
        ('VISTA', 'Ya la vi completa'),
        ('PROGRESO', 'La estoy viendo'),
        ('PENDIENTE', 'Pendiente'),
    ]

    titulo = models.CharField(max_length=200, verbose_name="Título")
    director = models.ForeignKey(
        Director, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='peliculas', verbose_name="Director",
    )
    sinopsis = models.TextField(blank=True, verbose_name="Sinopsis")
    anio = models.IntegerField(
        verbose_name="Año de estreno", blank=True, null=True,
        validators=[MinValueValidator(1888), MaxValueValidator(2100)],
    )
    duracion = models.PositiveIntegerField(
        verbose_name="Duración (minutos)", blank=True, null=True,
        validators=[MinValueValidator(1), MaxValueValidator(600)],
    )
    genero = models.CharField(max_length=100, blank=True, verbose_name="Género(s)",
                              help_text="Ej: Acción, Drama")
    imagen = models.URLField(max_length=500, verbose_name="Imagen (URL del póster)", blank=True, null=True)
    calificacion_promedio = models.DecimalField(
        max_digits=3, decimal_places=2, default=0, editable=False,
        verbose_name="Calificación promedio",
    )
    visualizaciones = models.PositiveIntegerField(default=0, editable=False, verbose_name="Visualizaciones")
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE', verbose_name="Estado")

    class Meta:
        ordering = ['-anio']

    def __str__(self):
        return f"{self.titulo} ({self.anio})"
    
    def get_absolute_url(self):
    # URL de la ficha de la película, ej: /pelicula/3/
        return reverse('pelicula_detalle', args=[self.pk])

    def actualizar_promedio(self):
        """Recalcula el promedio con TODAS las calificaciones de esta película."""
        promedio = self.calificaciones.aggregate(prom=Avg('puntuacion'))['prom'] or 0
        self.calificacion_promedio = round(promedio, 2)
        self.save(update_fields=['calificacion_promedio'])


class Actor(models.Model):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre")
    fecha_nacimiento = models.DateField(blank=True, null=True, verbose_name="Fecha de nacimiento")
    peliculas = models.ManyToManyField(Pelicula, related_name='actores', blank=True, verbose_name="Películas")

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = "Actores"

    def __str__(self):
        return self.nombre


class Calificacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='calificaciones', verbose_name="Usuario")
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE,
                                 related_name='calificaciones', verbose_name="Película")
    puntuacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Puntuación (1 a 5)",
    )
    comentario = models.TextField(blank=True, max_length=1000, verbose_name="Comentario")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        ordering = ['-fecha']
        verbose_name_plural = "Calificaciones"
        # Un usuario solo puede calificar UNA vez cada película (después la edita)
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'pelicula'], name='una_calificacion_por_usuario'),
        ]

    def __str__(self):
        return f"{self.usuario} → {self.pelicula.titulo}: {self.puntuacion}★"


class HistorialVisualizacion(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='historial', verbose_name="Usuario")
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE,
                                 related_name='historial', verbose_name="Película")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")
    minutos_visto = models.PositiveIntegerField(validators=[MinValueValidator(1)], verbose_name="Minutos vistos")
    porcentaje_visto = models.PositiveSmallIntegerField(default=0, verbose_name="% visto")

    class Meta:
        ordering = ['-fecha']
        verbose_name = "Historial de visualización"
        verbose_name_plural = "Historial de visualizaciones"

    def save(self, *args, **kwargs):
        # Antes de guardar, calculamos el % visto a partir de la duración de la película
        if self.pelicula.duracion:
            self.porcentaje_visto = min(100, round(self.minutos_visto * 100 / self.pelicula.duracion))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.usuario} vio {self.pelicula.titulo} ({self.porcentaje_visto}%)"


class ListaPersonalizada(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                related_name='listas', verbose_name="Usuario")
    nombre = models.CharField(max_length=100, verbose_name="Nombre de la lista")
    peliculas = models.ManyToManyField(Pelicula, related_name='listas', blank=True, verbose_name="Películas")
    publica = models.BooleanField(default=False, verbose_name="¿Es pública?")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Creada el")

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = "Lista personalizada"
        verbose_name_plural = "Listas personalizadas"
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'nombre'], name='nombre_lista_unico_por_usuario'),
        ]

    def __str__(self):
        return f"{self.nombre} ({'pública' if self.publica else 'privada'})"
