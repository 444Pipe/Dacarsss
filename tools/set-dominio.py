# -*- coding: utf-8 -*-
"""
Cambia el dominio del sitio en todos lados de una sola pasada.

    python tools/set-dominio.py https://www.dacarslujos.com
    python tools/set-dominio.py https://dacars-production.up.railway.app

Toca: el <head> de las paginas (canonical, hreflang, Open Graph, Twitter),
el JSON-LD completo, sitemap.xml, robots.txt, el 301 del .htaccess (Apache)
y el del Caddyfile (Railway), y los scripts de tools/ para que lo que se
regenere despues siga apuntando al dominio correcto.

Por que importa: si el canonical apunta a un dominio que no existe, Google no
indexa nada. Mientras el dominio definitivo no este montado, el canonical debe
apuntar al que de verdad esta sirviendo el sitio.

Un limite conocido: en la PROSA del README, una mencion al apex sin www queda
como www al pasar por otro dominio y volver, porque ahi el script no puede
saber si el apex se nombraba a proposito. Los archivos que sirven el sitio
(paginas, sitemap, robots, .htaccess, Caddyfile) si vuelven byte a byte: al
mudar de dominio, vale la pena mirar el diff del README antes del commit.
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cualquier dominio que hayamos usado antes. Al mudarse a uno nuevo hay que
# agregarlo aqui a mano, o la siguiente corrida no sabra reconocerlo para
# cambiarlo. Este archivo no se toca a si mismo: se comeria sus propios ejemplos.
HOSTS = [r'dacarslujos\.com',
         r'dacars\.com\.co',
         # Cada etiqueta arranca con letra o numero a proposito: con
         # '[a-z0-9.-]+' el patron engancha el '.up.railway.app' de
         # cualquier ejemplo escrito en prosa y se come el resto.
         r'[a-z0-9-]+(?:\.[a-z0-9-]+)*\.railway\.app']

# Con protocolo: https://www.dominio  ->  el dominio nuevo completo
PATRON = re.compile(r'https?://(?:www\.)?(?:%s)' % "|".join(HOSTS))
# Sin protocolo: el host suelto en prosa del README o en un comando de ejemplo.
# Los dos guardas hacen falta para no enganchar a mitad de un host: sin el
# lookbehind, 'TU-URL.up.railway.app' coincide desde el punto y queda
# 'TU-URLwww.dominio-nuevo'; sin el lookahead se comeria el 'dacarslujos.com'
# de un 'dacarslujos.com.mx' ajeno.
PATRON_HOST = re.compile(r'(?<![\w.-])(?:www\.)?(?:%s)(?![\w-])'
                         % "|".join(HOSTS))

ARCHIVOS = ["sitemap.xml", "robots.txt", ".htaccess", "Caddyfile",
            "README.md",
            os.path.join("tools", "patch-index.py"),
            os.path.join("tools", "generar-servicios.py"),
            os.path.join("tools", "generar-sitemap.py"),
            os.path.join("tools", "usar-cloudinary.py")]


def normalizar(d):
    d = d.strip().rstrip("/")
    if not d.startswith("http"):
        d = "https://" + d
    return d


def arreglar_htaccess(nuevo, host):
    u"""El .htaccess redirige una variante del dominio a la otra, y ahi el host
    va crudo y con los puntos escapados: PATRON no lo ve. Se reescribe entero
    para que apunte siempre a donde apunta el canonical."""
    ruta = os.path.join(ROOT, ".htaccess")
    if not os.path.exists(ruta):
        return
    txt = io.open(ruta, encoding="utf-8").read()
    bloque = re.compile(r"\n  # Forzar (?:www|el dominio sin www).*?\[R=301,L\]\n",
                        re.S)

    if ".railway.app" in host:
        # Dominio provisional: no hay variante propia que redirigir.
        # El salto anterior al bloque ya esta en el texto: reponerlo
        # dejaria una linea en blanco de mas en cada ida y vuelta.
        salida = bloque.sub("", txt)
        aviso = u"quitada la redirección de dominio (no aplica en railway.app)"
    else:
        apex = host[4:] if host.startswith("www.") else host
        if host.startswith("www."):
            titulo, desde = u"Forzar www", apex
        else:
            titulo, desde = u"Forzar el dominio sin www", "www." + apex
        nuevo_bloque = (u"\n  # %s (debe coincidir con el canonical del HTML)\n"
                        u"  RewriteCond %%{HTTP_HOST} ^%s$ [NC]\n"
                        u"  RewriteRule ^(.*)$ %s/$1 [R=301,L]\n"
                        % (titulo, desde.replace(".", r"\."), nuevo))
        if bloque.search(txt):
            salida = bloque.sub(lambda m: nuevo_bloque, txt, count=1)
        else:
            # Se venia de railway: hay que reponer el bloque que se habia quitado.
            salida = txt.replace("\n  # index.html -> /",
                                 nuevo_bloque + "\n  # index.html -> /", 1)
        aviso = u"redirección 301 de %s a %s" % (desde, nuevo)

    if salida != txt:
        io.open(ruta, "w", encoding="utf-8", newline="\n").write(salida)
        print(u"  %-50s %s" % (".htaccess", aviso))


def arreglar_caddyfile(nuevo, host):
    u"""Mismo 301 que el .htaccess, pero para Railway, que no lee .htaccess.
    El host va crudo en un matcher, asi que PATRON tampoco lo ve aqui."""
    ruta = os.path.join(ROOT, "Caddyfile")
    if not os.path.exists(ruta):
        return
    txt = io.open(ruta, encoding="utf-8").read()
    bloque = re.compile(u"\n\t# --- Una sola versi\u00f3n del dominio ---.*?"
                        u"permanent\n", re.S)

    if ".railway.app" in host:
        # Dominio provisional: no hay par apex/www que unificar.
        salida = bloque.sub(u"", txt)  # ver la nota en arreglar_htaccess
        aviso = u"quitado el 301 de dominio (no aplica en railway.app)"
    else:
        apex = host[4:] if host.startswith("www.") else host
        desde = apex if host.startswith("www.") else "www." + apex
        nuevo_bloque = (
            u"\n\t# --- Una sola versi\u00f3n del dominio ---\n"
            u"\t# Railway manda el apex y el www al mismo servicio: sin este 301 las dos\n"
            u"\t# versiones responden 200 y Google ve el sitio duplicado. Tiene que\n"
            u"\t# coincidir con el canonical del HTML. El .htaccess hace lo mismo en\n"
            u"\t# Apache, pero Railway no lo lee.\n"
            u"\t@otra-variante host %s\n"
            u"\tredir @otra-variante %s{uri} permanent\n" % (desde, nuevo))
        if bloque.search(txt):
            salida = bloque.sub(lambda m: nuevo_bloque, txt, count=1)
        else:
            # Se venia de railway: hay que reponer el bloque que se habia quitado.
            salida = txt.replace(u"\tencode zstd gzip\n",
                                 u"\tencode zstd gzip\n" + nuevo_bloque, 1)
        aviso = u"301 de %s a %s" % (desde, nuevo)

    if salida != txt:
        io.open(ruta, "w", encoding="utf-8", newline="\n").write(salida)
        print(u"  %-50s %s" % ("Caddyfile", aviso))


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)

    nuevo = normalizar(sys.argv[1])
    host = nuevo.split("//", 1)[1]
    apex = host[4:] if host.startswith("www.") else host

    objetivos = [f for f in os.listdir(ROOT) if f.endswith(".html")]
    objetivos += [f for f in ARCHIVOS if os.path.exists(os.path.join(ROOT, f))]

    total = 0
    for rel in sorted(objetivos):
        ruta = os.path.join(ROOT, rel)
        txt = io.open(ruta, encoding="utf-8").read()

        # Lo que ya estaba en el dominio nuevo coincide igual: se cuenta solo
        # lo que de verdad cambia, o una segunda corrida reporta cientos de
        # cambios sin haber tocado un byte.
        cambios = [0]

        def reemplazar(m, destino):
            if m.group(0) == destino:
                return m.group(0)
            cambios[0] += 1
            return destino

        salida = PATRON.sub(lambda m: reemplazar(m, nuevo), txt)

        def cambiar_host(m):
            encontrado = m.group(0)
            suyo = encontrado[4:] if encontrado.startswith("www.") else encontrado
            # La prosa distingue el apex del www a proposito: el 301 va de uno
            # al otro. Si el host ya es del dominio de destino, no se aplana.
            if suyo == apex:
                return encontrado
            return reemplazar(m, host)

        # El host crudo de .htaccess y Caddyfile lo manejan sus dos funciones:
        # aqui solo se toca el host suelto de la prosa y de los ejemplos.
        if rel not in (".htaccess", "Caddyfile"):
            salida = PATRON_HOST.sub(cambiar_host, salida)

        if salida != txt:
            io.open(ruta, "w", encoding="utf-8", newline="\n").write(salida)
            total += cambios[0]
            print("  %-50s %3d" % (rel, cambios[0]))

    arreglar_htaccess(nuevo, host)
    arreglar_caddyfile(nuevo, host)

    print("\n%d referencias actualizadas a %s" % (total, nuevo))
    print("Revisa que el canonical quedo bien:  grep -m2 canonical index.html")


if __name__ == "__main__":
    main()
