from django.urls import path
from .views import inicio, goIndex, goParams, createAutor

urlpatterns = [
    path('home/', inicio, name='inicio'), # Path enseña la ruta de la url que quiero ejecutar - name es un alias
    path('index/<int:decision>/', goIndex, name='index'),
    path('parametros/<int:id>/', goParams, name='params'),
    path('formulario/', createAutor, name='create-autor')
]