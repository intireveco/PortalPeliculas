from django.contrib import admin

from .models import (Actor, Calificacion, Director, HistorialVisualizacion,
                     ListaPersonalizada, Pelicula)

admin.site.site_header = 'Portal de Películas - Administración'
admin.site.site_title = 'Portal de Películas'


@admin.register(Director)
class DirectorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'nacionalidad', 'fecha_nacimiento', 'cantidad_peliculas')
    search_fields = ('nombre', 'nacionalidad')
    list_filter = ('nacionalidad',)

    @admin.display(description='Películas')
    def cantidad_peliculas(self, obj):
        return obj.peliculas.count()


@admin.register(Pelicula)
class PeliculaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'director', 'anio', 'genero',
                    'calificacion_promedio', 'visualizaciones', 'total_calificaciones')
    search_fields = ('titulo', 'director__nombre')
    list_filter = ('genero', 'anio', 'director')
    readonly_fields = ('calificacion_promedio', 'visualizaciones')  # se calculan solos
    list_per_page = 20

    @admin.display(description='N° calificaciones')
    def total_calificaciones(self, obj):
        return obj.calificaciones.count()


@admin.register(Actor)
class ActorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'fecha_nacimiento', 'cantidad_peliculas')
    search_fields = ('nombre',)
    list_filter = ('peliculas__genero',)
    filter_horizontal = ('peliculas',)  # selector cómodo para la relación N a N

    @admin.display(description='Películas')
    def cantidad_peliculas(self, obj):
        return obj.peliculas.count()


@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'pelicula', 'puntuacion', 'fecha')
    search_fields = ('usuario__username', 'pelicula__titulo')
    list_filter = ('puntuacion', 'fecha')

    def delete_queryset(self, request, queryset):
        # Al borrar varias a la vez, borramos una por una para que
        # se recalcule el promedio de cada película.
        for calificacion in queryset:
            calificacion.delete()


@admin.register(HistorialVisualizacion)
class HistorialVisualizacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'pelicula', 'minutos_visto', 'porcentaje_visto', 'fecha')
    search_fields = ('usuario__username', 'pelicula__titulo')
    list_filter = ('fecha', 'pelicula__genero')


@admin.register(ListaPersonalizada)
class ListaPersonalizadaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'usuario', 'publica', 'cantidad_peliculas')
    search_fields = ('nombre', 'usuario__username')
    list_filter = ('publica',)
    filter_horizontal = ('peliculas',)

    @admin.display(description='Películas')
    def cantidad_peliculas(self, obj):
        return obj.peliculas.count()
