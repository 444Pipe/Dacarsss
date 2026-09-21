from django.conf import settings

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
