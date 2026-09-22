"""Las vistas públicas del catálogo."""

from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from catalogo.models import Categoria, Marca, Producto
from sitio.templatetags.dacars import whatsapp_cotizar

POR_PAGINA = 24

ORDENES = {
    "relevancia": ("-destacado", "orden", "nombre"),
    "nuevos": ("-creado",),
    "nombre": ("nombre",),
}


def _categorias_con_productos(actual=None):
    """Las categorías que tienen algo publicado, con su cuenta.

    Una categoría vacía no sale en el selector: mandar a alguien a una
    página en blanco es peor que no ofrecerla. La que se está mirando se
    muestra siempre, aunque esté vacía, para que el selector no mienta sobre
    dónde está parado.
    """
    cuentas = dict(
        Producto.objects.publicados()
        .values_list("categoria")
        .annotate(n=Count("id"))
        .values_list("categoria", "n")
    )
    salida = []
    for c in Categoria.objects.filter(activa=True):
        c.cuantos = cuentas.get(c.pk, 0)
        if c.cuantos or (actual and c.pk == actual.pk):
            salida.append(c)
    return salida


def _portadas(categorias, productos):
    """Una foto por categoría para las tarjetas grandes del catálogo.

    Si la categoría tiene imagen propia cargada en el panel, esa. Si no, la
    del primer producto que tenga foto, en el orden en que se listan.
    """
    primera = {}
    for p in productos:
        if p.categoria_id not in primera and p.imagen_principal:
            primera[p.categoria_id] = p.imagen_principal.imagen
    for c in categorias:
        c.portada = c.imagen if c.imagen else primera.get(c.pk)
    return categorias


def _listado(request, categoria=None):
    productos = Producto.objects.publicados().con_todo()
    if categoria:
        productos = productos.filter(categoria=categoria)

    busqueda = request.GET.get("q", "").strip()
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda)
            | Q(resumen__icontains=busqueda)
            | Q(descripcion__icontains=busqueda)
            | Q(compatibilidad__icontains=busqueda)
            | Q(marca__nombre__icontains=busqueda)
            | Q(variantes__sku__icontains=busqueda)
            | Q(variantes__nombre__icontains=busqueda)
        ).distinct()

    marca = request.GET.get("marca", "").strip()
    if marca:
        productos = productos.filter(marca__slug=marca)

    # "Solo lo que hay" filtra por disponible real, no por el stock bruto:
    # lo reservado por otro pedido no está disponible aunque siga en el local.
    solo_disponibles = request.GET.get("hay") == "1"

    orden = request.GET.get("orden", "relevancia")
    productos = productos.order_by(*ORDENES.get(orden, ORDENES["relevancia"]))

    lista = list(productos)
    # "Solo lo que hay" y el orden por precio no dicen nada mientras todo el
    # catálogo esté a cotizar: el filtro se esconde hasta que haya algo con
    # existencias que filtrar.
    hay_vendibles = any(not p.a_cotizar for p in lista)
    if solo_disponibles:
        lista = [p for p in lista if not p.agotado]

    paginas = Paginator(lista, POR_PAGINA)
    pagina = paginas.get_page(request.GET.get("pagina"))

    # Los parámetros de filtro que hay que arrastrar en los enlaces de página.
    filtros = request.GET.copy()
    filtros.pop("pagina", None)

    if categoria:
        titulo = "{} en Villavicencio | DACARS".format(categoria.nombre)[:70]
        descripcion = (
            categoria.descripcion
            or "{} para tu carro en Villavicencio, Meta. Precios y disponibilidad al día en DACARS.".format(
                categoria.nombre
            )
        )[:160]
    else:
        titulo = "Catálogo de lujos y accesorios | DACARS Villavicencio"
        descripcion = (
            "Iluminación LED, CarPlay inalámbrico, cámaras de reversa y más para "
            "tu carro en Villavicencio. Míralos instalados y cotiza por WhatsApp."
        )

    categorias = _categorias_con_productos(categoria)
    filtrando = bool(busqueda or marca or solo_disponibles or request.GET.get("pagina"))

    return render(
        request,
        "catalogo/lista.html",
        {
            "titulo": titulo,
            "descripcion": descripcion,
            # Los filtros y las páginas no se indexan por separado: son la
            # misma mercancía recortada de otra forma, y Google lo lee como
            # contenido duplicado. El canonical siempre apunta a la página
            # limpia de la categoría (o del catálogo).
            "canonical": categoria.get_absolute_url() if categoria else "/catalogo/",
            "robots": (
                "noindex, follow"
                if filtrando
                else "index, follow, max-snippet:-1, max-image-preview:large"
            ),
            "seccion": "catalogo",
            # El menú solo ofrece el catálogo si hay algo publicado. Estando
            # adentro, lo hay por definición (o es una búsqueda vacía, y el
            # enlace sigue sirviendo para volver).
            "hay_catalogo": True,
            "categoria": categoria,
            "categorias": categorias,
            # Las tarjetas grandes de categoría solo en la entrada del
            # catálogo: con un filtro puesto, lo que se busca son productos.
            "portadas": (
                _portadas(categorias, lista)
                if not (categoria or filtrando) and len(categorias) > 1
                else []
            ),
            "hay_vendibles": hay_vendibles,
            "marcas": Marca.objects.filter(activa=True, productos__activo=True).distinct(),
            "pagina": pagina,
            "total": len(lista),
            "busqueda": busqueda,
            "marca_activa": marca,
            "orden": orden,
            "solo_disponibles": solo_disponibles,
            "filtros": filtros.urlencode(),
        },
    )


def lista(request):
    return _listado(request)


def categoria(request, slug):
    cat = get_object_or_404(Categoria, slug=slug, activa=True)
    return _listado(request, categoria=cat)


def producto(request, slug):
    prod = get_object_or_404(
        Producto.objects.publicados().con_todo(),
        slug=slug,
    )
    relacionados = (
        Producto.objects.publicados()
        .con_todo()
        .filter(categoria=prod.categoria)
        .exclude(pk=prod.pk)[:4]
    )
    principal = prod.imagen_principal
    return render(
        request,
        "catalogo/producto.html",
        {
            "titulo": prod.titulo_seo,
            "descripcion": prod.descripcion_seo,
            "og_tipo": "product",
            "og_imagen": principal.imagen.url if principal else "",
            "seccion": "catalogo",
            "hay_catalogo": True,
            "producto": prod,
            "variantes": prod.variantes_activas,
            "relacionados": relacionados,
            # El botón flotante del pie también cotiza este producto, no un
            # «quiero cotizar un servicio» genérico.
            "wa_flotante": whatsapp_cotizar(prod) if prod.a_cotizar else "",
        },
    )
