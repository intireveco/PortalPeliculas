from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('peliculas.urls')),  # todas las páginas de nuestra app
]
