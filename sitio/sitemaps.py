"""El sitemap, ahora vivo.

Antes era un XML a mano con 10 URLs. Ahora salen solas la portada, las
landings y el hub del Meta, y se les suman las categorías y los productos
que publique el comercio. Un producto
nuevo aparece en el sitemap el mismo día, sin que nadie corra un script.
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from catalogo.models import Categoria, Producto
from sitio.paginas import HUB_META, SLUGS


class Paginas(Sitemap):
    protocol = "https"
    changefreq = "monthly"

    def items(self):
        return ["portada", HUB_META] + SLUGS

    def location(self, item):
        return "/" if item == "portada" else "/" + item + ".html"

    def priority(self, item):
        if item == "portada":
            return 1.0
        # El hub del Meta es la única página que cubre el departamento
        # entero: para las búsquedas regionales no hay otra que la remplace.
        return 0.9 if item == HUB_META else 0.8


class Catalogo(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return ["inicio"]

    def location(self, item):
        return reverse("catalogo:lista")


class Categorias(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        return Categoria.objects.filter(activa=True)

    def lastmod(self, obj):
        return obj.actualizado


class Productos(Sitemap):
    protocol = "https"
    changefreq = "weekly"
    priority = 0.7
    limit = 2000

    def items(self):
        return Producto.objects.publicados()

    def lastmod(self, obj):
        return obj.actualizado


SITEMAPS = {
    "paginas": Paginas,
    "catalogo": Catalogo,
    "categorias": Categorias,
    "productos": Productos,
}
