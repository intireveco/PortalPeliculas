
from django.shortcuts import render
from .models import Pelicula

def listar_peliculas(request):
    # Consultamos todas las películas. 
    # El modelo ya las entrega ordenadas por año descendente gracias a la clase Meta.
    peliculas = Pelicula.objects.all()
    
    # Enviamos los datos al template 'listar.html' mediante el contexto
    return render(request, 'peliculas/listar.html', {'peliculas': peliculas})

