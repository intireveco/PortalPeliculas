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
]
