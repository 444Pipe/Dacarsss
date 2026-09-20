#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Convierte los 11 HTML estáticos en plantillas de Django.

Se corre **una sola vez**, en la migración. Después las plantillas se editan a
mano: este script y los generadores viejos de `tools/` quedan archivados.

Por qué un script y no copiar a mano: cada página trae entre 200 y 600 líneas
de JSON-LD. Moverlas a ojo es garantía de perder un atributo en alguna, y un
JSON-LD roto no se nota mirando la página — se nota tres meses después, cuando
Google dejó de mostrar las preguntas frecuentes.

Cómo queda partido cada archivo:

    <head>
      meta          por página   -> {% block meta %}
      carga (css)   común        -> va en base.html
      enlaces       común        -> va en base.html
      preload       por página   -> {% block preload %}
      json-ld       por página   -> {% block jsonld %}
    <body>
      carga (html)  común        -> va en base.html
      encabezado    dos formas   -> _encabezado.html / _encabezado_home.html
      main          por página   -> {% block contenido %}
      pie           dos formas   -> _pie.html / _pie_home.html

Lo que el script **verifica** antes de escribir nada: que las regiones comunes
sean idénticas byte a byte en las 11 páginas, y que las nueve landings
compartan encabezado y pie. Si algo no cuadra, muestra la diferencia y se
planta, en vez de emitir plantillas calladamente distintas al original.

Uso:
    python legacy/tools/migrar-a-django.py            # emite las plantillas
    python legacy/tools/migrar-a-django.py --revisar  # solo verifica, no escribe
"""

import difflib
import os
import re
import sys

class Error(Exception):
    pass


def _raiz():
    """La carpeta del proyecto, esté el script en tools/ o en legacy/tools/."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    while aqui != os.path.dirname(aqui):
        if os.path.exists(os.path.join(aqui, "manage.py")):
            return aqui
        aqui = os.path.dirname(aqui)
    raise Error("No encontré la raíz del proyecto (falta manage.py)")


RAIZ = _raiz()
DESTINO = os.path.join(RAIZ, "templates", "sitio")

# Después de la migración, los HTML originales viven en legacy/html/.
ORIGEN = os.path.join(RAIZ, "legacy", "html")
if not os.path.isdir(ORIGEN):
    ORIGEN = RAIZ

PORTADA = "index.html"
SERVICIOS = [
    "ppf-villavicencio",
    "polarizados-villavicencio",
    "detailing-villavicencio",
    "accesorios-4x4-villavicencio",
    "lujos-y-accesorios-villavicencio",
    "iluminacion-para-carros-villavicencio",
    "sonido-para-carros-villavicencio",
    "llantas-villavicencio",
    "pdr-desabolladura-sin-pintura-villavicencio",
]

MARCA_CARGA = "<!-- Pantalla de carga"
MARCA_CSS = '<link rel="stylesheet" href="css/style.css'

CABEZA_FIJA = (
    '<meta charset="utf-8">\n',
    '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n',
)

# Dónde se cuelga la franja del catálogo en cada página.
ANCLA_HOME = "<!-- ============ CONTACTO ============ -->"
ANCLA_LANDING = '<section class="sec sec--alt" id="faq">'

FRANJA_HOME = (
    '{% include "catalogo/_seccion.html" with productos=destacados '
    'etiqueta="Catálogo" titulo="Lo que tenemos en el local" '
    'bajada="Accesorios y repuestos con precio y disponibilidad al día. '
    'Lo apartás desde acá y cerramos por WhatsApp." %}\n\n'
)

FRANJA_LANDING = (
    '{% include "catalogo/_seccion.html" with productos=productos_del_servicio '
    'etiqueta="En el local" titulo="Productos para este servicio" '
    "ver_mas=categoria_del_servicio.get_absolute_url %}\n\n"
)

# La hoja del catálogo solo se descarga si hay algo que mostrar: mientras el
# comercio no cargue productos, las landings pesan exactamente lo que pesaban.
CSS_CATALOGO = (
    "{% block css_extra %}{% if productos_del_servicio or destacados %}\n"
    "<link rel=\"stylesheet\" href=\"{% static 'css/catalogo.css' %}\">"
    "{% endif %}{% endblock %}\n"
)


# ---------------------------------------------------------------------------
# Partir
# ---------------------------------------------------------------------------
def partir(ruta):
    with open(ruta, "r", encoding="utf-8") as f:
        texto = f.read()

    p = {}

    # ---- head ----
    i = texto.index("<head>") + len("<head>\n")
    j = texto.index(MARCA_CARGA)

    # El charset y el viewport son iguales en las 11 y viven en base.html.
    # Dejarlos también acá los duplicaría en cada página.
    lineas = texto[i:j].splitlines(True)
    if tuple(lineas[:2]) != CABEZA_FIJA:
        raise Error(
            "%s no empieza con el charset y el viewport esperados:\n%s"
            % (os.path.basename(ruta), "".join(lineas[:2]))
        )
    p["meta"] = "".join(lineas[2:])

    fin_carga = texto.index("</style>\n", j) + len("</style>\n")
    p["carga_css"] = texto[j:fin_carga]

    i_css = texto.index(MARCA_CSS, fin_carga)
    p["enlaces"] = texto[fin_carga:i_css]
    fin_css = texto.index("\n", i_css) + 1
    p["css_link"] = texto[i_css:fin_css]

    p["jsonld"] = texto[fin_css:texto.index("</head>")]

    # ---- body ----
    i_body = texto.index("<body>") + len("<body>\n")
    # La pantalla de carga y su respaldo en línea: hasta el primer </script>.
    fin_carga_html = texto.index("</script>\n", i_body) + len("</script>\n")
    p["carga_html"] = texto[i_body:fin_carga_html]

    i_main = texto.index("<main", fin_carga_html)
    p["encabezado"] = texto[fin_carga_html:i_main]

    fin_main = texto.index("</main>\n", i_main) + len("</main>\n")
    p["contenido"] = texto[i_main:fin_main]

    p["pie"] = texto[fin_main:texto.index("</body>")]

    return p


# ---------------------------------------------------------------------------
# Verificar
# ---------------------------------------------------------------------------
def iguales(nombre, valores):
    """Devuelve la región común. Falla mostrando el diff si no lo es."""
    referencia = ref_archivo = None
    for archivo, valor in valores:
        if referencia is None:
            referencia, ref_archivo = valor, archivo
            continue
        if valor != referencia:
            diff = list(
                difflib.unified_diff(
                    referencia.splitlines(),
                    valor.splitlines(),
                    ref_archivo,
                    archivo,
                    lineterm="",
                )
            )[:40]
            raise Error(
                "La región '%s' difiere entre %s y %s:\n%s"
                % (nombre, ref_archivo, archivo, "\n".join(diff))
            )
    return referencia


def sin_preloads(texto):
    return "".join(l for l in texto.splitlines(True) if 'rel="preload"' not in l)


def solo_preloads(texto):
    return "".join(l for l in texto.splitlines(True) if 'rel="preload"' in l)


def sin_activa(html):
    return html.replace(' class="is-active"', "")


# El botón flotante de WhatsApp lleva un texto distinto en cada landing
# ("quiero cotizar PPF", "quiero cotizar polarizado"). Eso es contenido, no
# ruido: se saca del pie y viaja como variable, así el parcial queda uno solo
# y cada página sigue mandando su mensaje.
RE_WA = re.compile(r'(<a class="wa" href=")([^"]+)(")')


def sacar_wa(pie):
    encontrado = RE_WA.search(pie)
    if not encontrado:
        raise Error("No encontré el botón flotante de WhatsApp en el pie")
    url = encontrado.group(2)
    return RE_WA.sub(r"\1{{ wa_flotante }}\3", pie, count=1), url


# ---------------------------------------------------------------------------
# Reescribir
# ---------------------------------------------------------------------------
def absolutizar(html):
    """Los enlaces relativos pasan a absolutos.

    En el sitio estático todas las páginas vivían en la raíz, así que
    `href="ppf-villavicencio.html"` resolvía bien. Ahora hay URLs con más
    niveles (/producto/algo/) y desde ahí ese mismo enlace apuntaría a
    /producto/ppf-villavicencio.html. La URL final no cambia; solo deja de
    depender de dónde estaba parado el lector.
    """
    html = html.replace('href="index.html#', 'href="/#')
    html = html.replace('href="index.html"', 'href="/"')
    for slug in SERVICIOS:
        html = html.replace('href="%s.html' % slug, 'href="/%s.html' % slug)
    html = html.replace('href="manifest.webmanifest"', 'href="/manifest.webmanifest"')
    html = re.sub(
        r'href="css/style\.css(\?v=[0-9a-f]+)?"',
        'href="{% static \'css/style.css\' %}"',
        html,
    )
    html = re.sub(
        r'src="js/app\.js(\?v=[0-9a-f]+)?"',
        'src="{% static \'js/app.js\' %}"',
        html,
    )
    return html


ENLACE_CATALOGO = (
    '{% if hay_catalogo %}<a href="{% url \'catalogo:lista\' %}"'
    '{% if seccion == "catalogo" %} class="is-active"{% endif %}>Catálogo</a>'
    "{% endif %}\n"
)

ENLACE_CARRITO = (
    '{% if carrito_unidades %}<a class="nav__bolsa" href="{% url \'pedidos:carrito\' %}"'
    ' aria-label="Ver el carrito">Carrito <b>{{ carrito_unidades }}</b></a>{% endif %}\n'
)


def _linea_con(texto, aguja, que):
    """La línea completa que contiene la aguja.

    Se busca la línea entera y no el fragmento: la portada y las landings
    indentan distinto, y reemplazar un fragmento deja la sangría partida.
    """
    for linea in texto.splitlines(True):
        if aguja in linea:
            return linea
    raise Error("No encontré %s (%s)" % (que, aguja))


def sumar_catalogo(encabezado, ancla_servicios):
    """Mete Catálogo y el contador del carrito en el menú."""
    servicios = _linea_con(encabezado, ancla_servicios, "el enlace de Servicios")
    sangria = servicios[: len(servicios) - len(servicios.lstrip())]
    encabezado = encabezado.replace(
        servicios, servicios + sangria + ENLACE_CATALOGO, 1
    )

    cta = _linea_con(encabezado, 'class="btn btn--wa nav__cta"', "el botón Cotizar")
    sangria = cta[: len(cta) - len(cta.lstrip())]
    return encabezado.replace(cta, sangria + ENLACE_CARRITO + cta, 1)


def sumar_catalogo_pie(pie):
    for ancla in ("      <h4>También</h4>\n", "      <h4>Tambi&eacute;n</h4>\n"):
        if ancla in pie:
            return pie.replace(
                ancla,
                ancla
                + "      {% if hay_catalogo %}<a href=\"{% url 'catalogo:lista' %}\">"
                "Catálogo de productos</a>{% endif %}\n",
                1,
            )
    raise Error("No encontré la columna 'También' del pie")


def marcar_activa(encabezado):
    """El `is-active` pasa a decidirse en la plantilla, no en el archivo."""
    for slug in SERVICIOS:
        plantilla = (
            '<a href="/%s.html"{%% if slug == "%s" %%} class="is-active"{%% endif %%}>'
            % (slug, slug)
        )
        encabezado = encabezado.replace(
            '<a href="/%s.html" class="is-active">' % slug, plantilla
        )
        encabezado = encabezado.replace('<a href="/%s.html">' % slug, plantilla)
    return encabezado


# ---------------------------------------------------------------------------
# Emitir
# ---------------------------------------------------------------------------
BASE = """{%% load static dacars %%}<!DOCTYPE html>
<html lang="es-CO">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
{%% block meta %%}{%% endblock %%}
%(carga_css)s
%(enlaces)s{%% block preload %%}{%% endblock %%}%(css_link)s{%% block css_extra %%}{%% endblock %%}
{%% block jsonld %%}{%% endblock %%}
</head>

<body>
%(carga_html)s
{%% block encabezado %%}{%% include "sitio/_encabezado.html" %%}{%% endblock %%}
{%% block contenido %%}{%% endblock %%}
{%% block pie %%}{%% include "sitio/_pie.html" %%}{%% endblock %%}
</body>
</html>
"""

PAGINA = """{%% extends "sitio/base.html" %%}{%% load static dacars %%}

{%% block meta %%}%(meta)s{%% endblock %%}
%(preload)s%(css_extra)s
{%% block jsonld %%}%(jsonld)s{%% endblock %%}
%(encabezado)s
{%% block contenido %%}%(contenido)s{%% endblock %%}
%(pie)s"""

# El `load` va en cada parcial: `{% include %}` no hereda las etiquetas
# cargadas por la plantilla que incluye.
#
# El aviso va en una sola línea porque Django lexea `{# #}` con una regex sin
# DOTALL: un comentario que abarque dos líneas no es un comentario, su texto
# sale impreso en la página y las etiquetas que tenga adentro se ejecutan.
AVISO = (
    "{% load static dacars %}"
    "{# Generado por tools/migrar-a-django.py desde el sitio estático. "
    "A partir de acá se edita a mano: el script no se vuelve a correr. #}\n"
)


def escribir(ruta, contenido, revisar):
    rel = os.path.relpath(ruta, RAIZ)
    if revisar:
        print("   (revisión) %s" % rel)
        return
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(contenido)
    print("   %s" % rel)


def main():
    revisar = "--revisar" in sys.argv

    archivos = [PORTADA] + [s + ".html" for s in SERVICIOS]
    faltan = [a for a in archivos if not os.path.exists(os.path.join(ORIGEN, a))]
    if faltan:
        raise Error(
            "Faltan los HTML originales: %s\n"
            "Si ya migraste, están en legacy/html/." % ", ".join(faltan)
        )

    print("Leyendo %d paginas..." % len(archivos))
    partes = {a: partir(os.path.join(ORIGEN, a)) for a in archivos}

    print("Verificando las regiones comunes en las %d..." % len(archivos))
    comunes = {}
    for region in ("carga_css", "css_link", "carga_html"):
        comunes[region] = iguales(region, [(a, partes[a][region]) for a in archivos])
    # La portada suma las precargas del video del hero; el resto no las tiene.
    comunes["enlaces"] = iguales(
        "enlaces", [(a, sin_preloads(partes[a]["enlaces"])) for a in archivos]
    )
    print("   ok  pantalla de carga, fuentes y hoja de estilos")

    interiores = [s + ".html" for s in SERVICIOS]
    encabezado_int = iguales(
        "encabezado de servicio",
        [(a, sin_activa(partes[a]["encabezado"])) for a in interiores],
    )

    # El pie se compara sin la URL del botón flotante, que es propia de cada
    # servicio y se pasa como variable.
    wa = {}
    pies = []
    for a in archivos:
        pie, url = sacar_wa(partes[a]["pie"])
        wa[a] = url
        if a in interiores:
            pies.append((a, pie))
    pie_int = iguales("pie de servicio", pies)
    pie_home, _ = sacar_wa(partes[PORTADA]["pie"])
    print("   ok  las 9 landings comparten encabezado y pie")

    if revisar:
        print("\nTodo consistente. Sin --revisar se emiten las plantillas.")
        return

    print("Escribiendo plantillas...")

    escribir(
        os.path.join(DESTINO, "base.html"),
        BASE
        % {
            "carga_css": comunes["carga_css"],
            "enlaces": comunes["enlaces"],
            "css_link": absolutizar(comunes["css_link"]),
            "carga_html": absolutizar(comunes["carga_html"]),
        },
        revisar,
    )

    escribir(
        os.path.join(DESTINO, "_encabezado_home.html"),
        AVISO + sumar_catalogo(absolutizar(partes[PORTADA]["encabezado"]), 'href="#servicios"'),
        revisar,
    )
    escribir(
        os.path.join(DESTINO, "_encabezado.html"),
        AVISO + marcar_activa(sumar_catalogo(absolutizar(encabezado_int), 'href="/#servicios"')),
        revisar,
    )
    # Las páginas nuevas (catálogo, carrito) incluyen el pie sin pasar
    # `wa_flotante`; el respaldo es el mensaje genérico de la portada.
    generico = wa[PORTADA]
    respaldo = '{{ wa_flotante|default:"%s" }}' % generico

    escribir(
        os.path.join(DESTINO, "_pie_home.html"),
        AVISO + sumar_catalogo_pie(absolutizar(pie_home)).replace("{{ wa_flotante }}", respaldo),
        revisar,
    )
    escribir(
        os.path.join(DESTINO, "_pie.html"),
        AVISO + sumar_catalogo_pie(absolutizar(pie_int)).replace("{{ wa_flotante }}", respaldo),
        revisar,
    )

    for archivo in archivos:
        p = partes[archivo]
        home = archivo == PORTADA
        preloads = solo_preloads(p["enlaces"])

        # La franja del catálogo, antes de las preguntas frecuentes en las
        # landings y antes del contacto en la portada.
        contenido = absolutizar(p["contenido"])
        ancla = ANCLA_HOME if home else ANCLA_LANDING
        franja = FRANJA_HOME if home else FRANJA_LANDING
        if ancla not in contenido:
            raise Error("No encontré dónde colgar el catálogo en %s" % archivo)
        contenido = contenido.replace(ancla, franja + ancla, 1)

        escribir(
            os.path.join(DESTINO, archivo),
            PAGINA
            % {
                "meta": absolutizar(p["meta"]),
                "preload": (
                    "{%% block preload %%}\n%s{%% endblock %%}" % preloads
                    if preloads
                    else ""
                ),
                "css_extra": CSS_CATALOGO,
                "jsonld": p["jsonld"],
                "encabezado": (
                    '{% block encabezado %}{% include "sitio/_encabezado_home.html" %}{% endblock %}'
                    if home
                    else ""
                ),
                "contenido": contenido,
                "pie": '{%% block pie %%}{%% include "sitio/%s" with wa_flotante="%s" %%}{%% endblock %%}\n'
                % ("_pie_home.html" if home else "_pie.html", wa[archivo]),
            },
            revisar,
        )

    print("\nListo: %d plantillas, base y 4 parciales." % len(archivos))
    print("Los HTML originales siguen en la raíz. Movelos a legacy/html/ cuando")
    print("hayas comparado el resultado en el navegador.")


if __name__ == "__main__":
    try:
        main()
    except Error as e:
        print("\nERROR: %s" % e)
        sys.exit(1)
