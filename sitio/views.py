"""Las páginas del sitio: portada, las landings, el hub del Meta, robots y manifest."""

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control

from catalogo.models import Categoria, Producto
from sitio.paginas import HUB_META, SLUGS


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


def hub_meta(request):
    """El hub del departamento del Meta.

    Vista aparte de `servicio` a propósito: esta página no vende un servicio
    concreto, así que no tiene categoría ni productos que mostrar. Meterla en
    `servicio` obligaría a inventarle un slug de catálogo que nadie usaría.
    """
    return render(
        request,
        "sitio/" + HUB_META + ".html",
        {"hay_catalogo": _hay_catalogo()},
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
        "# Rastreadores de IA: bienvenidos a propósito.",
        "#",
        "# Cada vez más gente pregunta «dónde hacen PPF en Villavicencio» en un",
        "# asistente en vez de en un buscador. Si estos agentes no pueden leer",
        "# el sitio, DACARS no existe en esa respuesta. El contenido ya es",
        "# público: bloquearlos no protege nada y cierra un canal que crece.",
        "",
        "User-agent: GPTBot",
        "Allow: /",
        "",
        "User-agent: OAI-SearchBot",
        "Allow: /",
        "",
        "User-agent: ChatGPT-User",
        "Allow: /",
        "",
        "User-agent: ClaudeBot",
        "Allow: /",
        "",
        "User-agent: Claude-User",
        "Allow: /",
        "",
        "User-agent: Claude-SearchBot",
        "Allow: /",
        "",
        "User-agent: PerplexityBot",
        "Allow: /",
        "",
        "User-agent: Perplexity-User",
        "Allow: /",
        "",
        "User-agent: Google-Extended",
        "Allow: /",
        "",
        "User-agent: Applebot",
        "Allow: /",
        "",
        "User-agent: Applebot-Extended",
        "Allow: /",
        "",
        "User-agent: meta-externalagent",
        "Allow: /",
        "",
        "User-agent: Amazonbot",
        "Allow: /",
        "",
        "User-agent: DuckAssistBot",
        "Allow: /",
        "",
        "User-agent: CCBot",
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
