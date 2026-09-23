"""Los pedacitos del panel que Python resuelve mejor que una plantilla.

Django arma el `app_list` con nombres y direcciones, pero nada de iconografía ni
de orden de uso. Eso vive acá y no en la plantilla para no llenarla de `{% if %}`
encadenados: sumar un modelo nuevo es una línea más en un diccionario, no una
rama más en el HTML.

Los nombres de icono apuntan a los `<symbol>` de templates/admin/_sprite.html.

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

# El orden del rail. Django entrega las apps alfabéticamente por nombre, que
# acá deja «Autenticación y autorización» arriba de todo: lo primero que ve
# quien atiende el local serían los usuarios del sistema. Este orden es el del
# trabajo real: primero lo que se toca todos los días.
ORDEN_MENU = [
    "producto",
    "variante",
    "pedido",
    "movimiento",
    "categoria",
    "marca",
    "user",
    "group",
]

# Estos dos van separados del resto por una línea: son la administración del
# panel, no el negocio.
AJUSTES = {"user", "group"}


@register.simple_tag
def icono_de(object_name, app_label=""):
    """El símbolo de un modelo; si no lo conozco, el de su sección."""
    nombre = ICONOS_MODELO.get(str(object_name).lower())
    if nombre:
        return nombre
    return ICONOS_APP.get(str(app_label).lower(), "punto")


@register.filter
def icono_app(app_label):
    return ICONOS_APP.get(str(app_label).lower(), "cuadricula")


@register.simple_tag
def menu_panel(available_apps):
    """Todos los modelos en una sola lista ordenada, partida en dos grupos.

    El rail no repite la agrupación por app de Django: con cuatro apps y ocho
    modelos, los encabezados de grupo ocupan casi tanto como los enlaces, y dos
    de ellos dirían «Pedidos» arriba de un único ítem llamado «Pedidos».
    """
    items = []
    for app in available_apps or []:
        for modelo in app.get("models", []):
            items.append(dict(modelo, app_label=app.get("app_label", "")))

    def donde(modelo):
        nombre = str(modelo.get("object_name", "")).lower()
        if nombre in ORDEN_MENU:
            return (ORDEN_MENU.index(nombre), "")
        # Lo que no está en el orden fijo va al final, alfabético.
        return (len(ORDEN_MENU), str(modelo.get("name", "")))

    items.sort(key=donde)
    es_ajuste = lambda m: str(m.get("object_name", "")).lower() in AJUSTES  # noqa: E731
    return {
        "trabajo": [m for m in items if not es_ajuste(m)],
        "ajustes": [m for m in items if es_ajuste(m)],
    }


@register.simple_tag(takes_context=True)
def activo(context, url):
    """`" es-actual"` si la página actual cuelga de esa dirección.

    Es una comparación por prefijo y no por igualdad para que el ítem del rail
    siga marcado mientras se edita un objeto: `/admin/catalogo/producto/3/change/`
    empieza con `/admin/catalogo/producto/`. Funciona porque los `admin_url`
    terminan en barra, así que «producto/» no matchea «productoimagen/».
    """
    peticion = context.get("request")
    if not peticion or not url:
        return ""
    return " es-actual" if peticion.path.startswith(str(url)) else ""
