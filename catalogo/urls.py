from django.urls import path

from catalogo import views

app_name = "catalogo"

urlpatterns = [
    path("catalogo/", views.lista, name="lista"),
    path("catalogo/<slug:slug>/", views.categoria, name="categoria"),
    path("producto/<slug:slug>/", views.producto, name="producto"),
]
