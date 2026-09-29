"""Las vistas públicas del catálogo."""

from xml.etree import ElementTree as ET

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.views.decorators.cache import cache_control

from catalogo.models import Categoria, Marca, Producto
from sitio.templatetags.dacars import foto, whatsapp_cotizar

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
            "Iluminación LED, tapetes, sonido, cámaras y más para tu carro. "
            "Precios al día, envíos a toda Colombia e instalación en Villavicencio."
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
            # Un listado sin productos tampoco se indexa: Google lo trata
            # como página vacía (soft 404) y le baja la confianza al sitio.
            # El día que la categoría tenga su primer producto, vuelve sola.
            "robots": (
                "noindex, follow"
                if filtrando or not lista
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


GNS = "http://base.google.com/ns/1.0"


@cache_control(max_age=3600)
def feed_google(request):
    """El feed de productos para Google Merchant Center.

    Es lo que pone los productos en la pestaña Shopping y en los resultados
    con precio y foto, gratis. Se registra una sola vez en Merchant Center
    (Productos → Feeds → agregar feed programado con esta URL) y Google lo
    relee solo.

    Google exige precio e imagen por producto, así que solo entran los que
    tienen variante con precio Y foto cargada. Un producto a cotizar o sin
    foto queda afuera sin romper el feed: cargarle precio y foto desde el
    panel lo mete solo en la próxima lectura.
    """
    sitio = settings.NEGOCIO["sitio"]
    ET.register_namespace("g", GNS)
    rss = ET.Element("rss", {"version": "2.0"})
    canal = ET.SubElement(rss, "channel")
    ET.SubElement(canal, "title").text = "DACARS — lujos y accesorios para vehículos"
    ET.SubElement(canal, "link").text = sitio + "/catalogo/"
    ET.SubElement(canal, "description").text = (
        "Catálogo de DACARS Villavicencio. Envíos a toda Colombia."
    )

    def g(elemento, campo, texto):
        ET.SubElement(elemento, "{%s}%s" % (GNS, campo)).text = texto

    for producto in Producto.objects.publicados().con_todo():
        principal = producto.imagen_principal
        if not principal:
            continue  # Google exige imagen: entra cuando tenga foto.
        variantes = producto.variantes_activas
        enlace = sitio + producto.get_absolute_url()
        for variante in variantes:
            item = ET.SubElement(canal, "item")
            g(item, "id", variante.sku)
            titulo = producto.nombre
            if len(variantes) > 1 and variante.nombre:
                titulo += " — " + variante.nombre
            g(item, "title", titulo[:150])
            g(item, "description", producto.descripcion_seo or producto.nombre)
            g(item, "link", enlace)
            g(item, "image_link", foto(principal.imagen, 1200))
            extra = [i for i in producto.imagenes.all() if i.pk != principal.pk][:10]
            for imagen in extra:
                g(item, "additional_image_link", foto(imagen.imagen, 1200))
            g(item, "availability", "out_of_stock" if variante.agotada else "in_stock")
            # Para Google, price es el precio normal y sale_price la rebaja:
            # al revés del modelo, donde `precio` ya es lo que se cobra.
            if variante.precio_antes and variante.precio_antes > variante.precio:
                g(item, "price", "{:.0f} COP".format(variante.precio_antes))
                g(item, "sale_price", "{:.0f} COP".format(variante.precio))
            else:
                g(item, "price", "{:.0f} COP".format(variante.precio))
            g(item, "condition", "new")
            if producto.marca:
                g(item, "brand", producto.marca.nombre)
            # Sin códigos de barras cargados: se le dice a Google que no hay
            # GTIN en vez de dejarlo esperando uno.
            g(item, "identifier_exists", "no")
            if len(variantes) > 1:
                g(item, "item_group_id", producto.slug[:50])

    xml = ET.tostring(rss, encoding="unicode", xml_declaration=True)
    return HttpResponse(xml, content_type="application/xml; charset=utf-8")


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
