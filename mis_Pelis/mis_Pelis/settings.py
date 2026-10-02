"""
Configuración del proyecto mis_Pelis (Portal de Películas).

Los datos secretos (clave, contraseña de la base de datos) NO se escriben aquí:
se leen del archivo .env con la librería python-decouple.
"""
from pathlib import Path

import dj_database_url
from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Seguridad: todo viene del archivo .env ---
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'peliculas',  # nuestra app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',  # protege los formularios (CSRF)
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mis_Pelis.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,  # busca las plantillas dentro de peliculas/templates/
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mis_Pelis.wsgi.application'

# --- Base de datos PostgreSQL online (Supabase) ---
# La dirección completa está en DATABASE_URL dentro del .env
DATABASES = {
    'default': dj_database_url.parse(config('DATABASE_URL')),
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Santiago'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# --- Login / logout ---
LOGIN_URL = 'login'               # a dónde enviar si no ha iniciado sesión
LOGIN_REDIRECT_URL = 'catalogo'   # a dónde ir después de iniciar sesión
LOGOUT_REDIRECT_URL = 'catalogo'  # a dónde ir después de cerrar sesión

# --- API de OMDb (importar películas desde el admin) ---
# La clave va en el .env; nunca en el código ni en el HTML.
OMDB_API_KEY = config('OMDB_API_KEY', default='')
