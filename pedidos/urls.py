from django.urls import path

from pedidos import views

app_name = "pedidos"

urlpatterns = [
    path("carrito/", views.ver, name="carrito"),
    path("carrito/agregar/", views.agregar, name="agregar"),
    path("carrito/actualizar/", views.actualizar, name="actualizar"),
    path("carrito/quitar/", views.quitar, name="quitar"),
    path("pedido/", views.checkout, name="checkout"),
    path("pedido/<str:numero>/", views.gracias, name="gracias"),
]
