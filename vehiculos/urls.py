from django.urls import path

from vehiculos import views

app_name = "vehiculos"

urlpatterns = [
    path("carros-en-venta/", views.lista, name="lista"),
    path("carros-en-venta/<slug:slug>/", views.detalle, name="detalle"),
]
