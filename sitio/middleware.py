"""Una sola versión del dominio.

Railway manda el dominio raíz (dacarslujos.com) y el www al mismo servicio, así
que sin esto el sitio entero responde 200 en los dos: para Google son dos sitios
con el mismo contenido. El canonical ayuda a elegir, pero no reemplaza al 301,
que además le pasa al www todo lo que el raíz haya acumulado.

Antes lo hacía el Caddyfile. Con la migración a Django, Caddy salió del camino
y la redirección se perdió sin que nada fallara: por eso vive ahora acá.

No se usa PREPEND_WWW de Django a propósito: le pone "www." a cualquier host que
no lo tenga, incluido el de Railway (x.up.railway.app -> www.x.up.railway.app),
que no existe. Esto solo mira el raíz del dominio configurado.
"""

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class DominioCanonico:
    def __init__(self, get_response):
        self.get_response = get_response
        dominio = settings.DOMINIO
        # Solo aplica si el dominio configurado es el www: si algún día se
        # decide servir sin www, esto no debe redirigir en sentido contrario.
        self.raiz = dominio[4:] if dominio.startswith("www.") else None
        self.destino = "https://" + dominio

    def __call__(self, request):
        if self.raiz and request.get_host().split(":")[0] == self.raiz:
            return HttpResponsePermanentRedirect(self.destino + request.get_full_path())
        return self.get_response(request)
