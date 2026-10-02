from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

urlpatterns = [
    path('', views.catalogo, name='catalogo'),

    # Cuentas de usuario
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('registro/', views.registro, name='registro'),

    # Películas
    path('pelicula/<int:pk>/', views.detalle_pelicula, name='detalle_pelicula'),
    path('pelicula/<int:pk>/calificar/', views.calificar, name='calificar'),
    path('pelicula/<int:pk>/calificacion/eliminar/', views.eliminar_calificacion, name='eliminar_calificacion'),
    path('pelicula/<int:pk>/ver/', views.registrar_visualizacion, name='registrar_visualizacion'),
    path('historial/', views.historial, name='historial'),

    # Listas personalizadas (CRUD)
    path('listas/', views.mis_listas, name='mis_listas'),
    path('listas/nueva/', views.crear_lista, name='crear_lista'),
    path('listas/<int:pk>/', views.ver_lista, name='ver_lista'),
    path('listas/<int:pk>/editar/', views.editar_lista, name='editar_lista'),
    path('listas/<int:pk>/eliminar/', views.eliminar_lista, name='eliminar_lista'),
    path('listas/publicas/', views.listas_publicas, name='listas_publicas'),

    # Top 10 y búsqueda
    path('top10/', views.top10, name='top10'),
    path('buscar/', views.buscar, name='buscar'),
]
