from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import Avg


class Director(models.Model):
    nombre = models.CharField(max_length=150, unique=True)
    nacionalidad = models.CharField(max_length=100)
    fecha_nacimiento = models.DateField('fecha de nacimiento', null=True, blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'directores'

    def __str__(self):
        return self.nombre


class Pelicula(models.Model):
    GENEROS = [
        ('accion', 'Acción'),
        ('animacion', 'Animación'),
        ('ciencia_ficcion', 'Ciencia ficción'),
        ('comedia', 'Comedia'),
        ('drama', 'Drama'),
        ('terror', 'Terror'),
        ('otro', 'Otro'),
    ]

    titulo = models.CharField('título', max_length=200)
    # Una película tiene UN director; un director tiene MUCHAS películas (1 a N)
    director = models.ForeignKey(Director, on_delete=models.PROTECT, related_name='peliculas')
    sinopsis = models.TextField(blank=True)
    anio = models.PositiveIntegerField(
        'año', validators=[MinValueValidator(1888), MaxValueValidator(2100)]
    )
    duracion = models.PositiveIntegerField(
        'duración (minutos)', validators=[MinValueValidator(1)]
    )
    genero = models.CharField('género', max_length=20, choices=GENEROS, default='otro')
    imagen = models.URLField('imagen (URL del póster)', max_length=500, blank=True)
    # Estos dos campos se calculan solos; nadie los escribe a mano
    calificacion_promedio = models.FloatField('calificación promedio', default=0)
    visualizaciones = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-anio', 'titulo']
        verbose_name = 'película'
        unique_together = ['titulo', 'anio']  # no se repite la misma película

    def __str__(self):
        return f'{self.titulo} ({self.anio})'

    def actualizar_promedio(self):
        """Recalcula el promedio con todas las calificaciones de la película."""
        resultado = self.calificaciones.aggregate(promedio=Avg('puntuacion'))
        self.calificacion_promedio = round(resultado['promedio'] or 0, 2)
        self.save(update_fields=['calificacion_promedio'])


class Actor(models.Model):
    nombre = models.CharField(max_length=150)
    fecha_nacimiento = models.DateField('fecha de nacimiento', null=True, blank=True)
    # Un actor sale en muchas películas y una película tiene muchos actores (N a N)
    peliculas = models.ManyToManyField(Pelicula, related_name='actores', blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name_plural = 'actores'

    def __str__(self):
        return self.nombre


class Calificacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calificaciones')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='calificaciones')
    puntuacion = models.PositiveSmallIntegerField(
        'puntuación', validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True, max_length=500)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'calificación'
        verbose_name_plural = 'calificaciones'
        unique_together = ['usuario', 'pelicula']  # una calificación por usuario y película

    def __str__(self):
        return f'{self.usuario} → {self.pelicula}: {self.puntuacion}★'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.pelicula.actualizar_promedio()  # promedio automático al guardar

    def delete(self, *args, **kwargs):
        pelicula = self.pelicula
        super().delete(*args, **kwargs)
        pelicula.actualizar_promedio()  # y también al borrar


class HistorialVisualizacion(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='historial')
    pelicula = models.ForeignKey(Pelicula, on_delete=models.CASCADE, related_name='historial')
    fecha = models.DateTimeField(auto_now_add=True)
    minutos_visto = models.PositiveIntegerField('minutos vistos', validators=[MinValueValidator(1)])

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'historial de visualización'
        verbose_name_plural = 'historial de visualizaciones'

    def __str__(self):
        return f'{self.usuario} vio {self.pelicula}'

    @property
    def porcentaje_visto(self):
        """Qué porcentaje de la película vio (máximo 100)."""
        return min(100, round(self.minutos_visto * 100 / self.pelicula.duracion))

    def save(self, *args, **kwargs):
        es_nuevo = self.pk is None
        super().save(*args, **kwargs)
        if es_nuevo:  # cada "play" nuevo suma una visualización a la película
            self.pelicula.visualizaciones += 1
            self.pelicula.save(update_fields=['visualizaciones'])


class ListaPersonalizada(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listas')
    nombre = models.CharField(max_length=100)
    peliculas = models.ManyToManyField(Pelicula, related_name='listas', blank=True)
    publica = models.BooleanField('pública', default=False)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'lista personalizada'
        verbose_name_plural = 'listas personalizadas'
        unique_together = ['usuario', 'nombre']  # un usuario no repite nombres de lista

    def __str__(self):
        return f'{self.nombre} ({self.usuario})'
