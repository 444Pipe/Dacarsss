"""Mapa de URLs de DACARS.

Las páginas del sitio viven en URLs limpias, sin extensión
(`/ppf-villavicencio`). Regla que no se negocia: **las direcciones viejas con
`.html` no se rompen**. Responden 301 a la limpia (ver sitio/urls.py), porque
son las que ya tienen Google, el perfil de Google Business, Instagram y cada
enlace compartido por WhatsApp. Lo nuevo cuelga de rutas propias.
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap

from django.urls import include, path

from sitio.sitemaps import SITEMAPS

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": SITEMAPS},
        name="django.contrib.sitemaps.views.sitemap",
    ),
    path("", include("catalogo.urls")),
    path("", include("pedidos.urls")),
    path("", include("sitio.urls")),
]

if settings.DEBUG and not settings.USAR_CLOUDINARY:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
