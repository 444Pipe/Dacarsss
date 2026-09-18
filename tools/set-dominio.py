# -*- coding: utf-8 -*-
"""
Cambia el dominio del sitio en todos lados de una sola pasada.

    python tools/set-dominio.py https://dacars-production.up.railway.app
    python tools/set-dominio.py https://www.dacars.com.co

Toca: el <head> de las 11 paginas (canonical, hreflang, Open Graph, Twitter),
el JSON-LD completo, sitemap.xml, robots.txt, .htaccess y los scripts de tools/
para que lo regenerado siga apuntando al dominio correcto.

Por que importa: si el canonical apunta a un dominio que no existe, Google no
indexa nada. Mientras el dominio definitivo no este montado, el canonical debe
apuntar al que de verdad esta sirviendo el sitio.
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Cualquier dominio que hayamos usado antes
PATRON = re.compile(r'https?://(?:www\.)?'
                    r'(?:dacars\.com\.co|[a-z0-9-]+\.up\.railway\.app|[a-z0-9.-]+\.railway\.app)')

ARCHIVOS = ["sitemap.xml", "robots.txt", ".htaccess", "README.md",
            os.path.join("tools", "patch-index.py"),
            os.path.join("tools", "generar-servicios.py"),
            os.path.join("tools", "set-dominio.py")]


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

    objetivos = [f for f in os.listdir(ROOT) if f.endswith(".html")]
    objetivos += [f for f in ARCHIVOS if os.path.exists(os.path.join(ROOT, f))]

    total = 0
    for rel in sorted(objetivos):
        ruta = os.path.join(ROOT, rel)
        txt = io.open(ruta, encoding="utf-8").read()
        nuevo_txt, n = PATRON.subn(nuevo, txt)
        if n:
            io.open(ruta, "w", encoding="utf-8", newline="\n").write(nuevo_txt)
            total += n
            print("  %-50s %3d" % (rel, n))

    # El .htaccess fuerza www: solo tiene sentido con dominio propio
    ht = os.path.join(ROOT, ".htaccess")
    if os.path.exists(ht) and ".railway.app" in host:
        txt = io.open(ht, encoding="utf-8").read()
        txt = re.sub(r"\n  # Forzar www.*?\[R=301,L\]\n", "\n", txt, flags=re.S)
        io.open(ht, "w", encoding="utf-8", newline="\n").write(txt)
        print("  .htaccess: quitada la redirección a www (no aplica en railway.app)")

    print("\n%d referencias actualizadas a %s" % (total, nuevo))
    print("Revisa que el canonical quedo bien:  grep -m2 canonical index.html")


if __name__ == "__main__":
    main()
