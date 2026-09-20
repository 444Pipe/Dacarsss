"""Filtros propios.

`pesos` está acá y no delegado al formato de Django porque en Colombia el peso
se escribe sin centavos y con punto de miles, y depender de la configuración
regional del servidor para algo tan visible es pedir que un día salga
"$450,000.00" en la ficha de un producto.
"""

import json
from urllib.parse import quote

from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def json_txt(valor):
    """El valor como cadena JSON, con comillas incluidas. Para el JSON-LD.

    El escape de `<`, `>` y `&` es el mismo que hace `json_script` de Django:
    sin él, una descripción de producto que contenga `</script>` cierra el
    bloque y el resto del JSON-LD se renderiza como HTML.
    """
    texto = json.dumps("" if valor is None else str(valor), ensure_ascii=False)
    texto = texto.replace("<", "\\u003C").replace(">", "\\u003E").replace("&", "\\u0026")
    return mark_safe(texto)


@register.filter
def pesos(valor):
    """450000 -> $450.000"""
    if valor is None or valor == "":
        return ""
    try:
        numero = int(round(float(valor)))
    except (TypeError, ValueError):
        return valor
    return "$" + "{:,}".format(numero).replace(",", ".")


@register.filter
def miles(valor):
    """450000 -> 450.000, sin el signo."""
    try:
        return "{:,}".format(int(round(float(valor)))).replace(",", ".")
    except (TypeError, ValueError):
        return valor


@register.filter
def foto(archivo, ancho=800):
    """La URL de una imagen con las transformaciones de entrega de Cloudinary.

    `c_limit` no es opcional: sin él Cloudinary **amplía** la imagen, y una foto
    de 600 px servida a w_1080 termina pesando más que el original. Está medido
    en el proyecto (ver el README, sección Cloudinary).

    Si el archivo no vive en Cloudinary (desarrollo local), devuelve su URL tal
    cual.
    """
    try:
        url = archivo.url
    except (AttributeError, ValueError):
        return ""
    marca = "/image/upload/"
    if marca not in url:
        return url
    izquierda, derecha = url.split(marca, 1)
    return "{}{}f_auto,q_auto,c_limit,w_{}/{}".format(
        izquierda, marca, int(ancho), derecha
    )


@register.simple_tag
def whatsapp(texto=""):
    """Enlace a WhatsApp con el mensaje ya escrito."""
    numero = settings.NEGOCIO["whatsapp"]
    if not texto:
        texto = "Hola DACARS, quiero cotizar un servicio."
    return "https://wa.me/{}?text={}".format(numero, quote(texto))


@register.simple_tag
def whatsapp_producto(producto, variante=None):
    partes = ["Hola DACARS, me interesa: " + producto.nombre]
    if variante is not None and variante.nombre:
        partes.append("(" + variante.nombre + ")")
    texto = " ".join(partes) + ". ¿Me pueden dar más información?"
    return "https://wa.me/{}?text={}".format(
        settings.NEGOCIO["whatsapp"], quote(texto)
    )
