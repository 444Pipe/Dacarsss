"""Mapa de URLs de DACARS.

Regla que no se negocia: **las URLs del sitio viejo no cambian**, incluido el
`.html` del final. El SEO local que ya está invertido (canonical, sitemap,
JSON-LD, enlaces desde Google) apunta ahí. Lo nuevo cuelga de rutas propias.
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
