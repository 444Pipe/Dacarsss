"""Las páginas del sitio: portada, las 9 landings, robots y manifest."""

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control

from catalogo.models import Categoria, Producto
from sitio.paginas import SLUGS


def portada(request):
    # El catálogo asoma en la portada: si el comercio carga productos, la
    # página de inicio los muestra sin que nadie tenga que tocar una plantilla.
    destacados = list(
        Producto.objects.publicados().con_todo().filter(destacado=True)[:4]
    )
    return render(
        request,
        "sitio/index.html",
        {"destacados": destacados, "hay_catalogo": _hay_catalogo()},
    )


def servicio(request, slug):
    if slug not in SLUGS:
        raise Http404
    categorias = Categoria.objects.filter(activa=True, servicio=slug)
    productos = list(
        Producto.objects.publicados().con_todo().filter(categoria__servicio=slug)[:4]
    )
    return render(
        request,
        "sitio/" + slug + ".html",
        {
            "slug": slug,
            "categoria_del_servicio": categorias.first(),
            "productos_del_servicio": productos,
            "hay_catalogo": _hay_catalogo(),
        },
    )


def _hay_catalogo():
    """El enlace al catálogo solo se muestra si hay algo que mostrar.

    Mientras el comercio no cargue el primer producto, el menú no manda a una
    página vacía.
    """
    return Producto.objects.publicados().exists()


@cache_control(max_age=86400)
def robots(request):
    sitio = settings.NEGOCIO["sitio"]
    lineas = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /carrito/",
        "Disallow: /pedido/",
        "",
        "# Rastreadores de IA: bienvenidos.",
        "User-agent: GPTBot",
        "Allow: /",
        "",
        "User-agent: PerplexityBot",
        "Allow: /",
        "",
        "User-agent: ClaudeBot",
        "Allow: /",
        "",
        "Sitemap: " + sitio + "/sitemap.xml",
        "",
    ]
    return HttpResponse("\n".join(lineas), content_type="text/plain; charset=utf-8")


@cache_control(max_age=86400)
def manifest(request):
    return render(
        request, "sitio/manifest.webmanifest", content_type="application/manifest+json"
    )
