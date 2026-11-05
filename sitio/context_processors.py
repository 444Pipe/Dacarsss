from django.conf import settings
from django.db import DatabaseError

from sitio.paginas import HUB_META, SERVICIOS


def negocio(request):
    """Los datos del negocio, para no repetirlos en cada plantilla."""
    return {"negocio": settings.NEGOCIO}


def paginas(request):
    """El índice de servicios, para los bloques que enlazan a todos.

    Está acá y no en cada vista porque lo usan el pie y el bloque «Más
    servicios», que salen en todas las páginas del sitio —incluidas las del
    catálogo, que no pasan por las vistas de `sitio`.
    """
    return {"servicios": SERVICIOS, "hub_meta": HUB_META}


def catalogo_menu(request):
    """Las categorías con productos, para el menú y el pie de todas las páginas.

    `hay_catalogo` sale de acá como valor por defecto: una vista que lo
    calcula aparte (la portada, las landings) lo pisa con el suyo. Sin
    productos publicados no hay categorías, y el menú no ofrece el catálogo.
    """
    from catalogo.views import categorias_con_productos  # evita el import circular

    try:
        categorias = categorias_con_productos()
    except DatabaseError:
        # Las migraciones todavía no corrieron (primer arranque).
        categorias = []
    return {"categorias_menu": categorias, "hay_catalogo": bool(categorias)}
