from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .models import Pelicula


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
