"""Las páginas del sitio: portada, las landings, el hub del Meta, robots y manifest."""

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.views.decorators.cache import cache_control

from catalogo.models import Categoria, Producto
from catalogo.views import categorias_con_portada
from sitio.paginas import HUB_META, SLUGS
from vehiculos.views import en_vitrina


# Qué categorías alimentan cada bloque de «Recomendados» de la portada.
RECOM_EXTERIOR = ["carpas-y-cubiertas", "iluminacion", "lujos-y-accesorios", "llantas-y-rines", "pitos-y-alarmas"]
RECOM_INTERIOR = ["multimedia-y-carplay", "seguridad-y-parqueo", "tapetes", "sonido", "detailing"]


def _recomendados(con_foto, slugs, cuantos=4):
    """Hasta `cuantos` productos con foto, uno por categoría mientras se pueda.

    Recorrer por categoría en vez de tomar los primeros evita que el bloque
    salga con cuatro bombillos seguidos.
    """
    por_categoria = {}
    for p in con_foto:
        por_categoria.setdefault(p.categoria.slug, []).append(p)
    elegidos = []
    ronda = 0
    while len(elegidos) < cuantos:
        antes = len(elegidos)
        for slug in slugs:
            lista = por_categoria.get(slug, [])
            if ronda < len(lista) and len(elegidos) < cuantos:
                elegidos.append(lista[ronda])
        if len(elegidos) == antes:
            break
        ronda += 1
    return elegidos


def portada(request):
    # El catálogo asoma en la portada: si el comercio carga productos, la
    # página de inicio los muestra sin que nadie tenga que tocar una plantilla.
    #
    # Todo lo que la portada muestra de productos lleva foto: una grilla de
    # recuadros vacíos no vende nada. Los destacados van primero por el orden
    # del modelo (-destacado).
    publicados = Producto.objects.publicados()
    con_foto = list(publicados.con_todo().filter(imagenes__isnull=False).distinct())
    destacados = con_foto[:12]
    novedades = sorted(con_foto, key=lambda p: p.creado, reverse=True)[:12]
    hay_catalogo = _hay_catalogo()
    return render(
        request,
        "sitio/index.html",
        {
            "destacados": destacados,
            "novedades": novedades if novedades != destacados else [],
            "recom_exterior": _recomendados(con_foto, RECOM_EXTERIOR),
            "recom_interior": _recomendados(con_foto, RECOM_INTERIOR),
            "hay_catalogo": hay_catalogo,
            "categorias": categorias_con_portada() if hay_catalogo else [],
            "total_productos": publicados.count(),
            "carros_venta": [c for c in en_vitrina() if not c.vendido][:4],
        },
    )


def servicio(request, slug):
    if slug not in SLUGS:
        raise Http404
    categorias = list(Categoria.objects.filter(activa=True, servicio=slug))
    productos = list(
        Producto.objects.publicados().con_todo().filter(categoria__servicio=slug)[:4]
    )
    # Varias categorías pueden colgar del mismo servicio (Seguridad y Pitos
    # cuelgan de Lujos y accesorios). El «ver más» tiene que llevar a una que
    # tenga algo, no a la primera por orden, que puede estar vacía.
    con_productos = {p.categoria_id for p in productos}
    categoria = next(
        (c for c in categorias if c.pk in con_productos),
        categorias[0] if categorias else None,
    )
    return render(
        request,
        "sitio/" + slug + ".html",
        {
            "slug": slug,
            "categoria_del_servicio": categoria,
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


@cache_control(max_age=3600)
def favicon(request):
    # Las páginas enlazan el icono por su dirección con huella (ver
    # sitio/_iconos.html). Esta queda para quien pide /favicon.ico a ciegas:
    # Google y algunos navegadores. Caché corta, porque la dirección es fija
    # y no cambia cuando cambia el icono. Se sirve el archivo directo y no
    # con una redirección a la versión con huella: un 301 quedaría guardado
    # apuntando al icono viejo el día que cambie.
    ruta = settings.BASE_DIR / "static" / "img" / "icono" / "favicon.ico"
    return HttpResponse(ruta.read_bytes(), content_type="image/x-icon")
