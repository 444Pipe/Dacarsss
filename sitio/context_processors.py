from django.conf import settings


def negocio(request):
    """Los datos del negocio, para no repetirlos en 11 plantillas."""
    return {"negocio": settings.NEGOCIO}
