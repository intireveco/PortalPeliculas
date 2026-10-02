from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CalificacionForm, VisualizacionForm
from .models import Calificacion, Pelicula


# ---------------------------------------------------------------
# READ: catálogo de películas con paginación (8 por página)
# ---------------------------------------------------------------
def catalogo(request):
    peliculas = Pelicula.objects.select_related('director').all()
    paginador = Paginator(peliculas, 8)
    pagina = paginador.get_page(request.GET.get('page'))
    return render(request, 'peliculas/catalogo.html', {'pagina': pagina})


# ---------------------------------------------------------------
# Registro de usuarios nuevos (login y logout los da Django)
# ---------------------------------------------------------------
def registro(request):
    if request.user.is_authenticated:
        return redirect('catalogo')

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            login(request, usuario)  # entra automáticamente
            messages.success(request, f'¡Bienvenido/a, {usuario.username}!')
            return redirect('catalogo')
    else:
        form = UserCreationForm()
    return render(request, 'registration/registro.html', {'form': form})


# ---------------------------------------------------------------
# Detalle de una película: datos, calificaciones y recomendaciones
# ---------------------------------------------------------------
def detalle_pelicula(request, pk):
    pelicula = get_object_or_404(Pelicula.objects.select_related('director'), pk=pk)
    calificaciones = pelicula.calificaciones.select_related('usuario')
    # Recomendación: otras películas del mismo director
    mas_del_director = pelicula.director.peliculas.exclude(pk=pelicula.pk)[:4]

    mi_calificacion = None
    if request.user.is_authenticated:
        mi_calificacion = calificaciones.filter(usuario=request.user).first()

    contexto = {
        'pelicula': pelicula,
        'calificaciones': calificaciones,
        'mas_del_director': mas_del_director,
        'mi_calificacion': mi_calificacion,
        'form_calificacion': CalificacionForm(instance=mi_calificacion),  # precargado si ya calificó
    }
    return render(request, 'peliculas/detalle.html', contexto)


@login_required
@require_POST
def calificar(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    # Si ya había calificado, la editamos; si no, se crea una nueva
    mi_calificacion = Calificacion.objects.filter(usuario=request.user, pelicula=pelicula).first()
    form = CalificacionForm(request.POST, instance=mi_calificacion)

    if form.is_valid():
        try:
            calificacion = form.save(commit=False)
            calificacion.usuario = request.user
            calificacion.pelicula = pelicula
            calificacion.save()  # aquí se recalcula el promedio (ver models.py)
            messages.success(request, 'Tu calificación fue guardada.')
        except DatabaseError:
            messages.error(request, 'No se pudo guardar la calificación. Intenta de nuevo.')
    else:
        messages.error(request, 'Revisa tu calificación: debe ser de 1 a 5 estrellas y el comentario máximo 500 caracteres.')
    return redirect('detalle_pelicula', pk=pk)


@login_required
@require_POST
def eliminar_calificacion(request, pk):
    # Solo encuentra la calificación si es DEL usuario conectado
    calificacion = get_object_or_404(Calificacion, pelicula_id=pk, usuario=request.user)
    calificacion.delete()
    messages.success(request, 'Tu calificación fue eliminada.')
    return redirect('detalle_pelicula', pk=pk)


@login_required
@require_POST
def registrar_visualizacion(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    form = VisualizacionForm(request.POST)
    form.instance.usuario = request.user
    form.instance.pelicula = pelicula

    if form.is_valid():
        try:
            registro_visto = form.save()  # aquí también suma 1 visualización (ver models.py)
            messages.success(request, f'Guardamos que viste el {registro_visto.porcentaje_visto}% de la película.')
        except DatabaseError:
            messages.error(request, 'No se pudo guardar en tu historial. Intenta de nuevo.')
    else:
        for error in form.errors.get('minutos_visto', []):
            messages.error(request, error)
    return redirect('detalle_pelicula', pk=pk)


@login_required
def historial(request):
    registros = request.user.historial.select_related('pelicula')

    # Recomendaciones: películas de directores que ya vio y que aún no ha visto
    vistas = Pelicula.objects.filter(historial__usuario=request.user)
    recomendadas = (Pelicula.objects
                    .filter(director__in=vistas.values('director'))
                    .exclude(pk__in=vistas.values('pk'))
                    .distinct()[:6])

    return render(request, 'peliculas/historial.html', {
        'registros': registros,
        'recomendadas': recomendadas,
    })
