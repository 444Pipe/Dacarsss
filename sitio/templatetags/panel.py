"""Los pedacitos del panel que Python resuelve mejor que una plantilla.

Django arma el `app_list` con nombres y direcciones, pero nada de iconografía.
El mapa vive acá y no en la plantilla para no llenarla de `{% if %}` encadenados:
sumar un modelo nuevo es una línea más en el diccionario, no una rama más en el
HTML.

Los nombres apuntan a los `<symbol>` de templates/admin/_sprite.html.

Esto es del panel, no del sitio, y aun así vive en `sitio`: Django solo busca
templatetags dentro de apps instaladas, y `dacars` no lo está —su AppConfig
hereda de AdminConfig y lo que registra es `django.contrib.admin`—, así que un
`dacars/templatetags/` no lo encontraría nunca.
"""

from django import template

register = template.Library()

# object_name en minúscula -> símbolo del sprite.
ICONOS_MODELO = {
    "producto": "caja",
    "variante": "etiqueta",
    "categoria": "carpeta",
    "marca": "sello",
    "imagenproducto": "foto",
    "pedido": "recibo",
    "itempedido": "recibo",
    "movimiento": "flechas",
    "user": "persona",
    "group": "personas",
}

# app_label -> símbolo. Es el respaldo cuando el modelo no está en el mapa de
# arriba, así un modelo nuevo igual sale con el icono de su sección.
ICONOS_APP = {
    "catalogo": "caja",
    "pedidos": "recibo",
    "inventario": "flechas",
    "auth": "llave",
}


@register.simple_tag
def icono_de(object_name, app_label=""):
    """El símbolo de un modelo; si no lo conozco, el de su sección."""
    nombre = ICONOS_MODELO.get(str(object_name).lower())
    if nombre:
        return nombre
    return ICONOS_APP.get(str(app_label).lower(), "cuadricula")


@register.filter
def icono_app(app_label):
    return ICONOS_APP.get(str(app_label).lower(), "cuadricula")
