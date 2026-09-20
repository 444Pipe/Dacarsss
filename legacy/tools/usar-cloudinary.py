# -*- coding: utf-8 -*-
"""
Reescribe las referencias a statics/ para que apunten a Cloudinary.

    python tools/usar-cloudinary.py            # aplica
    python tools/usar-cloudinary.py --revertir # vuelve a las rutas locales

Corre DESPUES de tools/subir-cloudinary.py, que es quien deja el inventario
en tools/cloudinary-map.json.

Idempotente en los dos sentidos: si volves a subir los assets (sube la version
en Cloudinary) y lo corres otra vez, actualiza las URLs ya escritas en vez de
duplicarlas.

Toca las 11 paginas, js/app.js, manifest.webmanifest y sitemap.xml.

NO toca los scripts de tools/. Se intento y fue un error: los generadores
arman las URLs concatenando (SITE + "/statics/video/" + slug + ".jpg"), asi
que un reemplazo textual deja engendros como SITE + "/https://res.cloudinary..."
y encima no alcanza las partes variables. Este script es el ULTIMO paso del
pipeline, igual que fix-iconos.py: los generadores siguen emitiendo rutas
locales y aca se convierten. Ver tools/build.py, que los corre en orden.

POLITICA DE ENTREGA (medida, no supuesta)
  Imagenes  f_auto,q_auto,c_limit,w_<ancho natural>
            c_limit es lo que impide que Cloudinary AMPLIE un asset: sin eso,
            los posters de reel (608 px de ancho) se servian a 1080 y pesaban
            un 62% MAS que el original.
  og-image  q_auto y nada mas. Sin f_auto a proposito: los crawlers de
            WhatsApp y Facebook no siempre mandan un Accept decente y podrian
            recibir un WebP que no saben mostrar.
  Video     sin transformar. generar-video.py ya los encodeo con ffmpeg;
            pasarles q_auto los reencoda y quedan mas pesados (el testimonio
            pasaba de 6,9 a 9,3 MB). Aca la ganancia es el CDN, no recomprimir.
"""

import io
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPA = os.path.join(ROOT, "tools", "cloudinary-map.json")
SITE = "https://www.dacars.com.co"

# Archivos donde se reescriben las referencias. Ningun .py: ver el docstring.
# El js/ se barre entero a proposito, no solo app.js: cualquier script nuevo
# que pida un asset (loader.js pide el logo del wordmark) tiene que entrar aca,
# o en produccion da 404 — statics/ ya no viaja en la imagen Docker.
OBJETIVOS = (
    [f for f in sorted(os.listdir(ROOT)) if f.endswith(".html")]
    + ["js/" + f for f in sorted(os.listdir(os.path.join(ROOT, "js"))) if f.endswith(".js")]
    + ["manifest.webmanifest", "sitemap.xml"]
)

# Donde la URL TIENE que ser absoluta: Open Graph, Twitter Card, JSON-LD y el
# sitemap. Una ruta relativa ahi no la resuelve ningun crawler. Se usa al
# revertir, para devolver SITE + "/statics/..." y no solo "statics/...".
RE_CTX_ABSOLUTO = re.compile(
    r"<script[^>]*application/ld\+json[^>]*>.*?</script>"
    r"|<meta[^>]*(?:og:image|twitter:image)[^>]*>",
    re.S | re.I,
)

PRECONNECT = '<link rel="preconnect" href="https://res.cloudinary.com" crossorigin>'
ANCLA_PRECONNECT = '<link rel="preconnect" href="https://fonts.googleapis.com">'


def cargar_mapa():
    if not os.path.exists(MAPA):
        sys.exit("Falta tools/cloudinary-map.json.\n"
                 "Corre primero:  python tools/subir-cloudinary.py\n")
    with io.open(MAPA, encoding="utf-8") as fh:
        return json.load(fh)


def transformacion(rel, info):
    """La receta de entrega para un asset. Ver POLITICA arriba."""
    if info["resource_type"] == "video":
        return ""
    if rel.endswith("og-image.jpg"):
        return "q_auto"
    return "f_auto,q_auto,c_limit,w_%d" % info["width"]


def url_de(cloud, rel, info):
    tr = transformacion(rel, info)
    ext = ".mp4" if info["resource_type"] == "video" else ""
    partes = [cloud, info["resource_type"], "upload"]
    if tr:
        partes.append(tr)
    partes += ["v%s" % info["version"], info["public_id"]]
    return "https://res.cloudinary.com/" + "/".join(partes) + ext


def patron_local(rel):
    """Coincide con statics/x.png y con https://www.dacars.com.co/statics/x.png"""
    return re.compile(r"(?:" + re.escape(SITE) + r"/)?" + re.escape(rel))


def patron_cloudinary(cloud, info):
    """
    Coincide con una URL de Cloudinary ya escrita para este mismo public_id,
    con cualquier transformacion y cualquier version. Sirve para actualizar
    en vez de duplicar cuando se vuelve a subir.

    El lookahead final evita que 'dacars/logo-dacars' coincida dentro de
    'dacars/logo-dacars-sm': despues del public_id solo puede venir la
    extension o un delimitador.

    El resource_type va fijo, no como (?:image|video): el poster reel-x.jpg y
    el video reel-x.mp4 comparten public_id y solo se distinguen por ahi. Si
    se deja abierto, el patron del poster pisa la URL del video.

    La version es OPCIONAL a proposito. Cloudinary entrega igual sin ella, asi
    que una URL escrita a mano suele venir sin version; si el patron la exigiera
    (como hacia antes), este script no la reconoceria como suya y la dejaria
    intacta para siempre. Fue exactamente lo que paso con el hero vertical: se
    cambio 3x4 por 9x16 a mano, sin version, y quedo apuntando a un asset que
    no existia. Aceptandola opcional, cualquier URL a mano se normaliza sola en
    la siguiente corrida.
    """
    return re.compile(
        r"https://res\.cloudinary\.com/" + re.escape(cloud) +
        r"/" + info["resource_type"] +
        r"/upload/(?:[^/\"'\s]+/)*(?:v\d+/)?" + re.escape(info["public_id"]) +
        r"(?:\.[a-z0-9]{2,5})?(?=[\"'\s)<,])"
    )


def aplicar(texto, cloud, mapa):
    # De mas largo a mas corto: evita que un public_id corto pise a uno que lo
    # contiene como prefijo.
    activos = sorted(
        ((k, v) for k, v in mapa.items() if isinstance(v, dict)),
        key=lambda kv: len(kv[1]["public_id"]), reverse=True,
    )
    n = 0
    for rel, info in activos:
        destino = url_de(cloud, rel, info)
        texto, a = patron_cloudinary(cloud, info).subn(destino, texto)
        texto, b = patron_local(rel).subn(destino, texto)
        n += a + b
    return texto, n


def revertir(texto, cloud, mapa, archivo):
    """
    Vuelve a las rutas locales. Restaura la forma ABSOLUTA donde hacia falta
    (og:image, twitter:image, JSON-LD, sitemap) y la relativa en el resto,
    que es como estaba escrito el sitio antes de Cloudinary.
    """
    if archivo.endswith(".xml"):
        absolutos = [(0, len(texto))]           # el sitemap es todo absoluto
    else:
        absolutos = [m.span() for m in RE_CTX_ABSOLUTO.finditer(texto)]

    def dentro_de_contexto_absoluto(pos):
        return any(ini <= pos < fin for ini, fin in absolutos)

    # Una SOLA pasada, a proposito: si se hiciera un sub por asset, cada
    # reemplazo correria el texto y los spans de arriba, calculados sobre el
    # original, quedarian desfasados. Dentro de un unico re.sub todas las
    # posiciones se refieren siempre al texto original.
    # La clave es (tipo, public_id), no el public_id solo: reel-x.jpg y
    # reel-x.mp4 comparten public_id y se pisarian entre si.
    por_pid = {(v["resource_type"], v["public_id"]): k
               for k, v in mapa.items() if isinstance(v, dict)}
    if not por_pid:
        return texto, 0

    # Del mas largo al mas corto para que la alternancia prefiera el public_id
    # completo ('dacars/logo-dacars-sm') sobre el que lo prefija ('.../logo-dacars').
    pids = sorted({p for _, p in por_pid}, key=len, reverse=True)
    combinado = re.compile(
        r"https://res\.cloudinary\.com/" + re.escape(cloud) +
        r"/(image|video)/upload/(?:[^/\"'\s]+/)*(?:v\d+/)?(" +
        "|".join(re.escape(p) for p in pids) +
        r")(?:\.[a-z0-9]{2,5})?(?=[\"'\s)<,])"
    )

    def reemplazo(m):
        rel = por_pid[(m.group(1), m.group(2))]
        return (SITE + "/" + rel) if dentro_de_contexto_absoluto(m.start()) else rel

    return combinado.subn(reemplazo, texto)


# Un <link rel="icon"> o un icono del manifest declaran type="image/png".
# Si les dejamos f_auto, Cloudinary entrega WebP y el tipo declarado miente
# (y algunos chequeos de PWA lo marcan como icono invalido). Ahi va f_png.
RE_LINK_ICONO = re.compile(r"<link\b[^>]*\brel=\"(?:icon|apple-touch-icon)\"[^>]*>")


def forzar_png(texto, rel):
    """Cambia f_auto por f_png donde el formato esta declarado como PNG."""
    if rel == "manifest.webmanifest":
        return re.subn(r"(res\.cloudinary\.com/[^\"'\s]*?)f_auto", r"\1f_png", texto)
    return RE_LINK_ICONO.subn(lambda m: m.group(0).replace("f_auto", "f_png"), texto)


def preconnect(texto, quitar=False):
    """Agrega (o saca) el preconnect a res.cloudinary.com. Idempotente."""
    tiene = PRECONNECT in texto
    if quitar:
        if not tiene:
            return texto, 0
        return texto.replace(PRECONNECT + "\n", "").replace(PRECONNECT, ""), 1
    if tiene or ANCLA_PRECONNECT not in texto:
        return texto, 0
    return texto.replace(ANCLA_PRECONNECT, PRECONNECT + "\n" + ANCLA_PRECONNECT, 1), 1


def main():
    marcha_atras = "--revertir" in sys.argv
    mapa = cargar_mapa()
    cloud = mapa.get("_cloud_name")
    if not cloud:
        sys.exit("El mapa no trae _cloud_name. Volve a correr subir-cloudinary.py")

    print("Cloud: %s" % cloud)
    print("Modo:  %s\n" % ("REVERTIR a rutas locales" if marcha_atras else "aplicar Cloudinary"))

    total = 0
    for rel in OBJETIVOS:
        ruta = os.path.join(ROOT, rel.replace("/", os.sep))
        if not os.path.exists(ruta):
            continue
        txt = original = io.open(ruta, encoding="utf-8").read()

        if marcha_atras:
            txt, n = revertir(txt, cloud, mapa, rel)
        else:
            txt, n = aplicar(txt, cloud, mapa)
            txt, f = forzar_png(txt, rel)
            n += f

        if rel.endswith(".html"):
            txt, p = preconnect(txt, quitar=marcha_atras)
            n += p

        if txt != original:
            io.open(ruta, "w", encoding="utf-8", newline="\n").write(txt)
            print("  %-42s %3d referencias" % (rel, n))
            total += n

    print("\n  %d referencias reescritas" % total)
    if not total:
        print("  (ya estaba en el estado pedido)")


if __name__ == "__main__":
    main()
