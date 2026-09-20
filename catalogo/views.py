"""Las vistas públicas del catálogo."""

from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from catalogo.models import Categoria, Marca, Producto

POR_PAGINA = 24

ORDENES = {
    "relevancia": ("-destacado", "orden", "nombre"),
    "nuevos": ("-creado",),
    "nombre": ("nombre",),
}


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
            "Accesorios, lujos y repuestos para tu carro en Villavicencio, Meta. "
            "Mirá precios y disponibilidad, y cerrá el pedido por WhatsApp."
        )

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
                if (busqueda or marca or solo_disponibles or request.GET.get("pagina"))
                else "index, follow, max-snippet:-1, max-image-preview:large"
            ),
            "seccion": "catalogo",
            "categoria": categoria,
            "categorias": Categoria.objects.filter(activa=True),
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
            "producto": prod,
            "variantes": prod.variantes_activas,
            "relacionados": relacionados,
        },
    )
