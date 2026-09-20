# -*- coding: utf-8 -*-
"""
Cambia el dominio del sitio en todos lados de una sola pasada.

    python tools/set-dominio.py https://dacars-production.up.railway.app
    python tools/set-dominio.py https://www.dacars.com.co

Por que importa: si el canonical apunta a un dominio que no existe, Google no
indexa nada. Mientras el dominio definitivo no este montado, el canonical debe
apuntar al que de verdad esta sirviendo el sitio.

Que toca:

  templates/sitio/*.html   el <head> de las 10 paginas migradas: canonical,
                           hreflang, Open Graph, Twitter y el JSON-LD entero.
                           Ahi el dominio esta escrito a mano, heredado del
                           sitio estatico.
  README.md                la documentacion.

Que NO toca, porque no hace falta:

  El catalogo, el carrito y las fichas de producto arman sus URLs con la
  variable DOMINIO del entorno (ver dacars/settings.py -> NEGOCIO). Cambiar
  esa variable en Railway alcanza para todo lo nuevo.
  El sitemap y el robots.txt los genera Django con el mismo dato.

O sea: despues de correr esto hay que **cambiar tambien DOMINIO** en las
variables del servicio, o el sitio viejo y el nuevo apuntaran a dominios
distintos. El script lo recuerda al final.
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cualquier dominio que hayamos usado antes.
PATRON = re.compile(
    r"https?://(?:www\.)?"
    r"(?:dacars\.com\.co|[a-z0-9-]+\.up\.railway\.app|[a-z0-9.-]+\.railway\.app)"
)

PLANTILLAS = os.path.join(ROOT, "templates", "sitio")
SUELTOS = ["README.md", os.path.join("tools", "set-dominio.py")]


def normalizar(d):
    d = d.strip().rstrip("/")
    if not d.startswith("http"):
        d = "https://" + d
    return d


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(2)

    nuevo = normalizar(sys.argv[1])
    host = nuevo.split("//", 1)[1]

    objetivos = []
    if os.path.isdir(PLANTILLAS):
        objetivos += [
            os.path.join("templates", "sitio", f)
            for f in sorted(os.listdir(PLANTILLAS))
            if f.endswith(".html")
        ]
    objetivos += [f for f in SUELTOS if os.path.exists(os.path.join(ROOT, f))]

    total = 0
    for rel in objetivos:
        ruta = os.path.join(ROOT, rel)
        txt = io.open(ruta, encoding="utf-8").read()
        nuevo_txt, n = PATRON.subn(nuevo, txt)
        if n:
            io.open(ruta, "w", encoding="utf-8", newline="\n").write(nuevo_txt)
            total += n
            print("  %-52s %3d" % (rel, n))

    print("\n%d referencias actualizadas a %s" % (total, nuevo))
    print("")
    print("FALTA UN PASO. En Railway -> Variables, pone:")
    print("    DOMINIO=%s" % host)
    print("Sin eso, el catalogo y el sitemap siguen apuntando al dominio viejo.")
    print("")
    print("Y verifica que quedo bien:")
    print("    python manage.py test sitio")


if __name__ == "__main__":
    main()
