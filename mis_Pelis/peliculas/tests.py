"""
PRUEBAS OPCIONALES (7 pruebas) (no son obligatorias para la evaluación).

Se ejecutan con una base de datos SQLite temporal para no tocar Supabase.
En PowerShell (Windows):
    $env:DATABASE_URL="sqlite:///pruebas.sqlite3"; python manage.py test
En Git Bash / Mac / Linux:
    DATABASE_URL=sqlite:///pruebas.sqlite3 python manage.py test
"""
from django.contrib.auth.models import User
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.urls import reverse

from .omdb import ErrorOMDb, importar_pelicula
from .models import Calificacion, Director, HistorialVisualizacion, ListaPersonalizada, Pelicula


class PortalTests(TestCase):
    def setUp(self):
        director = Director.objects.create(nombre='Christopher Nolan', nacionalidad='Británica')
        self.pelicula = Pelicula.objects.create(titulo='El origen', director=director, anio=2010, duracion=148)
        self.ana = User.objects.create_user('ana', password='ClaveSegura123')
        self.beto = User.objects.create_user('beto', password='ClaveSegura123')

    def test_promedio_se_calcula_solo(self):
        Calificacion.objects.create(usuario=self.ana, pelicula=self.pelicula, puntuacion=5)
        Calificacion.objects.create(usuario=self.beto, pelicula=self.pelicula, puntuacion=2)
        self.pelicula.refresh_from_db()
        self.assertEqual(self.pelicula.calificacion_promedio, 3.5)

    def test_visualizacion_suma_contador(self):
        HistorialVisualizacion.objects.create(usuario=self.ana, pelicula=self.pelicula, minutos_visto=74)
        self.pelicula.refresh_from_db()
        self.assertEqual(self.pelicula.visualizaciones, 1)

    def test_mis_listas_pide_login(self):
        respuesta = self.client.get(reverse('mis_listas'))
        self.assertEqual(respuesta.status_code, 302)  # lo manda al login

    def test_no_puede_editar_lista_ajena(self):
        lista = ListaPersonalizada.objects.create(usuario=self.ana, nombre='Favoritas')
        self.client.login(username='beto', password='ClaveSegura123')
        respuesta = self.client.get(reverse('editar_lista', args=[lista.pk]))
        self.assertEqual(respuesta.status_code, 404)

    def test_lista_privada_oculta(self):
        lista = ListaPersonalizada.objects.create(usuario=self.ana, nombre='Secreta', publica=False)
        respuesta = self.client.get(reverse('ver_lista', args=[lista.pk]))
        self.assertEqual(respuesta.status_code, 404)


# Respuesta falsa de OMDb: así la prueba no necesita internet ni clave real
RESPUESTA_FALSA = {
    'Response': 'True', 'Title': 'Interstellar', 'Year': '2014', 'Runtime': '169 min',
    'Genre': 'Adventure, Drama, Sci-Fi', 'Director': 'Christopher Nolan',
    'Actors': 'Matthew McConaughey, Anne Hathaway', 'Plot': 'Viaje espacial.',
    'Poster': 'N/A', 'imdbID': 'tt0816692',
}


@override_settings(OMDB_API_KEY='clave-de-prueba')
class OmdbTests(TestCase):
    @patch('peliculas.omdb.requests.get')
    def test_importar_crea_pelicula_director_y_actores(self, get_falso):
        get_falso.return_value.json.return_value = RESPUESTA_FALSA
        pelicula = importar_pelicula('tt0816692')
        self.assertEqual(pelicula.duracion, 169)
        self.assertEqual(pelicula.genero, 'drama')  # primer género que conocemos
        self.assertEqual(pelicula.director.nombre, 'Christopher Nolan')
        self.assertEqual(pelicula.actores.count(), 2)

    @patch('peliculas.omdb.requests.get')
    def test_no_importa_dos_veces(self, get_falso):
        get_falso.return_value.json.return_value = RESPUESTA_FALSA
        importar_pelicula('tt0816692')
        with self.assertRaises(ErrorOMDb):
            importar_pelicula('tt0816692')
