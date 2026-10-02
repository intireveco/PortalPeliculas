import logging

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import DatabaseError, IntegrityError
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import CalificacionForm, RegistroForm, VisualizacionForm
from .models import Calificacion, HistorialVisualizacion, Pelicula

logger = logging.getLogger(__name__)


# =====================================================================
# Funciones de ayuda (no son vistas)
# =====================================================================
def estados_del_usuario(usuario):
    """Devuelve {id_pelicula: 'VISTA' o 'PROGRESO'} según el historial del usuario."""
    if not usuario.is_authenticated:
        return {}
    maximos = (HistorialVisualizacion.objects.filter(usuario=usuario)
               .values('pelicula_id').annotate(maximo=Max('porcentaje_visto')))
    return {fila['pelicula_id']: 'VISTA' if fila['maximo'] >= 90 else 'PROGRESO' for fila in maximos}


# =====================================================================
# Historial de visualización ("play")
# =====================================================================
@login_required   # si no ha iniciado sesión, lo manda al login
@require_POST     # solo acepta envíos de formulario (POST), no visitas directas (GET)
def registrar_visualizacion(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    form = VisualizacionForm(request.POST, pelicula=pelicula)

    if form.is_valid():
        try:
            registro = form.save(commit=False)   # aún no se guarda...
            registro.usuario = request.user      # ...el dueño lo pone el servidor, no el formulario
            registro.pelicula = pelicula
            registro.save()

            messages.success(
                request,
                f'Visualización registrada ({registro.porcentaje_visto}% visto).'
            )

        except DatabaseError:
            logger.exception('Error al registrar visualización')
            messages.error(request, 'No se pudo registrar la visualización.')

    else:
        for error in form.errors.get('minutos_visto', []):
            messages.error(request, error)

    return redirect('pelicula_detalle', pk=pk)


@login_required
def mi_historial(request):
    # request.user.historial = SOLO el historial del usuario conectado
    historial = request.user.historial.select_related('pelicula')
    pagina = Paginator(historial, 20).get_page(request.GET.get('page'))

    return render(
        request,
        'peliculas/historial.html',
        {'pagina': pagina}
    )
    
# =====================================================================
# Calificaciones: cada usuario crea/edita/borra SOLO las suyas
# =====================================================================
@login_required
@require_POST
def calificar(request, pk):
    pelicula = get_object_or_404(Pelicula, pk=pk)
    form = CalificacionForm(request.POST)
    if form.is_valid():
        try:
            calificacion = form.save(commit=False)
            calificacion.usuario = request.user
            calificacion.pelicula = pelicula
            calificacion.save()   # la señal del Paso 6 recalcula el promedio
            messages.success(request, '¡Gracias por calificar!')
        except IntegrityError:
            # La UniqueConstraint del modelo impide calificar 2 veces la misma película
            messages.warning(request, 'Ya calificaste esta película. Puedes editar tu calificación.')
    else:
        messages.error(request, 'Elige una puntuación entre 1 y 5.')
    return redirect('pelicula_detalle', pk=pk)


@login_required
def calificacion_editar(request, pk):
    # Filtrar por usuario=request.user: si la calificación es de otro usuario, responde 404
    calificacion = get_object_or_404(Calificacion, pk=pk, usuario=request.user)
    form = CalificacionForm(request.POST or None, instance=calificacion)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Calificación actualizada.')
        return redirect('pelicula_detalle', pk=calificacion.pelicula_id)
    return render(request, 'peliculas/formulario.html', {
        'form': form, 'titulo': f'Editar calificación de «{calificacion.pelicula.titulo}»'})


@login_required
def calificacion_eliminar(request, pk):
    calificacion = get_object_or_404(Calificacion, pk=pk, usuario=request.user)
    if request.method == 'POST':
        pelicula_id = calificacion.pelicula_id
        calificacion.delete()
        messages.success(request, 'Calificación eliminada.')
        return redirect('pelicula_detalle', pk=pelicula_id)
    return render(request, 'peliculas/confirmar_eliminar.html', {
        'objeto': calificacion, 'volver': calificacion.pelicula.get_absolute_url()})

