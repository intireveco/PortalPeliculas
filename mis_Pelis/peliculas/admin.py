from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect, render
from django.urls import path

from .models import (Actor, Calificacion, Director, HistorialVisualizacion,
                     ListaPersonalizada, Pelicula)
from .omdb import ErrorOMDb, buscar_por_titulo, importar_pelicula

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
    change_list_template = 'admin/pelicula_change_list.html'  # agrega el botón "Importar desde OMDb"

    @admin.display(description='N° calificaciones')
    def total_calificaciones(self, obj):
        return obj.calificaciones.count()

    # --- Importar desde OMDb: una página extra dentro del admin ---
    def get_urls(self):
        urls_propias = [
            path('importar-omdb/', self.admin_site.admin_view(self.importar_omdb),
                 name='peliculas_importar_omdb'),
        ]
        return urls_propias + super().get_urls()

    def importar_omdb(self, request):
        if not self.has_add_permission(request):  # solo quien puede agregar películas
            raise PermissionDenied

        # POST = el usuario confirmó: guardamos la película
        if request.method == 'POST':
            try:
                pelicula = importar_pelicula(request.POST.get('imdb_id', ''))
                self.message_user(request, f'"{pelicula}" se importó desde OMDb.', messages.SUCCESS)
                return redirect('admin:peliculas_pelicula_change', pelicula.pk)
            except ErrorOMDb as error:
                self.message_user(request, str(error), messages.ERROR)

        # GET con título = buscar y mostrar una vista previa (todavía no guarda nada)
        titulo = request.GET.get('titulo', '').strip()
        anio = request.GET.get('anio', '').strip()
        resultado = None
        if titulo:
            try:
                resultado = buscar_por_titulo(titulo, anio)
            except ErrorOMDb as error:
                self.message_user(request, str(error), messages.ERROR)

        contexto = {
            **self.admin_site.each_context(request),
            'opts': self.model._meta,
            'title': 'Importar película desde OMDb',
            'titulo': titulo,
            'anio': anio,
            'resultado': resultado,
        }
        return render(request, 'admin/importar_omdb.html', contexto)


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
