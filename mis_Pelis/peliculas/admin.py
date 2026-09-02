import requests
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from .models import Pelicula

@admin.register(Pelicula)
class PeliculaAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'director', 'anio', 'estado')
    list_filter = ('estado',)
    search_fields = ('titulo', 'director')
    change_list_template = "admin/pelicula_change_list.html"

    # Añadimos la ruta personalizada dentro del Admin
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('buscar-api/', self.admin_site.admin_view(self.buscar_api_view), name='buscar_pelicula_api'),
        ]
        return custom_urls + urls

    # Vista que procesa la búsqueda o el guardado
    def buscar_api_view(self, request):
        if request.method == 'POST' and 'guardar_pelicula' in request.POST:
            # Recibimos los datos confirmados desde la plantilla
            titulo = request.POST.get('titulo')
            director = request.POST.get('director')
            anio = request.POST.get('anio')
            poster_url = request.POST.get('poster_url')
            estado = request.POST.get('estado')

            # Convertimos el año a entero si viene disponible
            try:
                anio_int = int(anio[:4]) if anio else None
            except ValueError:
                anio_int = None

            # Guardamos la película en la Base de Datos
            Pelicula.objects.create(
                titulo=titulo,
                director=director,
                anio=anio_int,
                poster_url=poster_url,
                estado=estado
            )
            self.message_user(request, f"¡Película '{titulo}' guardada con éxito!", level=messages.SUCCESS)
            return redirect('admin:peliculas_pelicula_changelist')

        context = dict(
            self.admin_site.each_context(request),
            opts=self.model._meta,
        )
        return render(request, 'admin/buscar_api.html', context)