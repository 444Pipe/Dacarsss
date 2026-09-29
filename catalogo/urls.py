from django.urls import path

from catalogo import views

app_name = "catalogo"

urlpatterns = [
    path("catalogo/", views.lista, name="lista"),
    path("catalogo/<slug:slug>/", views.categoria, name="categoria"),
    path("producto/<slug:slug>/", views.producto, name="producto"),
    # El feed de Google Merchant Center. No va en el sitemap ni en el menú:
    # su único lector es el robot de Google Shopping.
    path("feed-productos.xml", views.feed_google, name="feed-google"),
]
