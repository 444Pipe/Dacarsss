from django.urls import path
from django.views.generic import RedirectView

from sitio import views
from sitio.paginas import HUB_META, SLUGS

urlpatterns = [
    path("", views.portada, name="portada"),
    # Cualquiera que llegue a /index.html va a la raíz. El canonical siempre
    # dijo "/", así que las dos URLs sirviendo lo mismo sería contenido
    # duplicado gratis.
    path("index.html", RedirectView.as_view(url="/", permanent=True)),
    path(HUB_META, views.hub_meta, name="hub-meta"),
    path("robots.txt", views.robots, name="robots"),
    path("manifest.webmanifest", views.manifest, name="manifest"),
    path("favicon.ico", views.favicon, name="favicon"),
]

# Las landings, sin extensión: /ppf-villavicencio.
urlpatterns += [
    path(slug, views.servicio, {"slug": slug}, name="servicio-" + slug)
    for slug in SLUGS
]


def _a_la_limpia(pagina):
    # query_string: quien llega de un anuncio con ?utm_... no pierde la
    # etiqueta de la campaña en el salto.
    return RedirectView.as_view(url="/" + pagina, permanent=True, query_string=True)


# Las direcciones con .html no se rompen: responden 301 a la limpia. Son las
# que ya circulan en Google, en el perfil de Google Business, en Instagram y en
# cada enlace compartido por WhatsApp, y el 301 le dice a Google que la página
# se mudó y le traspasa lo que la vieja había ganado. La barra final también
# redirige, para que cada página tenga una sola dirección.
for pagina in SLUGS + [HUB_META]:
    urlpatterns += [
        path(pagina + ".html", _a_la_limpia(pagina)),
        path(pagina + "/", _a_la_limpia(pagina)),
    ]
