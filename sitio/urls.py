from django.urls import path
from django.views.generic import RedirectView

from sitio import views
from sitio.paginas import SLUGS

urlpatterns = [
    path("", views.portada, name="portada"),
    # Cualquiera que llegue a /index.html va a la raíz. El canonical siempre
    # dijo "/", así que las dos URLs sirviendo lo mismo sería contenido
    # duplicado gratis.
    path("index.html", RedirectView.as_view(url="/", permanent=True)),
    path("robots.txt", views.robots, name="robots"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
]

# Las 9 landings, con el .html que ya tienen indexado.
urlpatterns += [
    path(
        slug + ".html",
        views.servicio,
        {"slug": slug},
        name="servicio-" + slug,
    )
    for slug in SLUGS
]
