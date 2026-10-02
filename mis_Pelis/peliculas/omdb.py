"""
Conexión con la API de OMDb (https://www.omdbapi.com).

La consulta se hace desde el SERVIDOR con la librería requests, así la
clave (OMDB_API_KEY) queda en el .env y nunca llega al navegador.
"""
import requests
from django.conf import settings
from django.db import transaction

from .models import Actor, Director, Pelicula

URL_OMDB = 'https://www.omdbapi.com/'

# Géneros de OMDb (en inglés) → nuestros géneros
GENEROS_OMDB = {
    'Action': 'accion',
    'Animation': 'animacion',
    'Sci-Fi': 'ciencia_ficcion',
    'Comedy': 'comedia',
    'Drama': 'drama',
    'Horror': 'terror',
}


class ErrorOMDb(Exception):
    """Error con un mensaje claro para mostrar en el admin."""


def consultar_omdb(**parametros):
    """Hace la petición a OMDb y devuelve el diccionario de respuesta."""
    if not settings.OMDB_API_KEY:
        raise ErrorOMDb('Falta OMDB_API_KEY en el archivo .env.')
    parametros['apikey'] = settings.OMDB_API_KEY

    try:
        respuesta = requests.get(URL_OMDB, params=parametros, timeout=10)
        datos = respuesta.json()
    except requests.RequestException:
        raise ErrorOMDb('No se pudo conectar con OMDb. Revisa tu internet e intenta de nuevo.')
    except ValueError:
        raise ErrorOMDb('OMDb respondió algo inesperado. Intenta de nuevo más tarde.')

    if datos.get('Response') != 'True':
        # Ejemplos: "Movie not found!" o "Invalid API key!"
        raise ErrorOMDb(f"OMDb respondió: {datos.get('Error', 'película no encontrada')}")
    return datos


def primer_numero(texto):
    """Saca el primer número de un texto: '148 min' → 148, '2010' → 2010, 'N/A' → None."""
    numero = ''
    for caracter in texto or '':
        if caracter.isdigit():
            numero += caracter
        elif numero:
            break
    return int(numero) if numero else None


def limpiar(texto):
    """OMDb escribe 'N/A' cuando no tiene un dato; lo cambiamos por texto vacío."""
    return '' if not texto or texto == 'N/A' else texto.strip()


def buscar_por_titulo(titulo, anio=''):
    """Busca UNA película por título (y año opcional) para mostrar la vista previa."""
    parametros = {'t': titulo, 'type': 'movie'}
    if anio:
        parametros['y'] = anio
    return consultar_omdb(**parametros)


def importar_pelicula(imdb_id):
    """Trae la película por su código IMDb y la guarda con su director y actores."""
    datos = consultar_omdb(i=imdb_id)

    titulo = limpiar(datos.get('Title'))
    anio = primer_numero(datos.get('Year'))
    duracion = primer_numero(datos.get('Runtime'))
    if not titulo or not anio or not duracion:
        raise ErrorOMDb('OMDb no informa el título, el año o la duración. Agrégala a mano.')

    # Validación: no repetir películas (mismo título y año)
    if Pelicula.objects.filter(titulo__iexact=titulo, anio=anio).exists():
        raise ErrorOMDb(f'"{titulo} ({anio})" ya está en el catálogo.')

    # Si OMDb trae varios directores, usamos el primero
    nombre_director = limpiar(datos.get('Director')).split(',')[0].strip() or 'Desconocido'

    # Primer género de OMDb que conozcamos; si ninguno calza, "otro"
    genero = 'otro'
    for genero_omdb in limpiar(datos.get('Genre')).split(', '):
        if genero_omdb in GENEROS_OMDB:
            genero = GENEROS_OMDB[genero_omdb]
            break

    # transaction.atomic: o se guarda todo, o no se guarda nada
    with transaction.atomic():
        director, _ = Director.objects.get_or_create(
            nombre=nombre_director, defaults={'nacionalidad': 'Sin información'}
        )
        pelicula = Pelicula.objects.create(
            titulo=titulo,
            director=director,
            sinopsis=limpiar(datos.get('Plot')),
            anio=anio,
            duracion=duracion,
            genero=genero,
            imagen=limpiar(datos.get('Poster')),
        )
        for nombre in limpiar(datos.get('Actors')).split(','):
            nombre = nombre.strip()
            if nombre:
                actor = Actor.objects.filter(nombre=nombre).first() or Actor.objects.create(nombre=nombre)
                actor.peliculas.add(pelicula)
    return pelicula
