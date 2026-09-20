# -*- coding: utf-8 -*-
"""
Pone la huella del contenido en los enlaces a css/style.css y js/app.js.

    python tools/versionar-assets.py

Reescribe el href/src de las 11 paginas como "css/style.css?v=ab12cd34", donde
el sufijo son los 8 primeros caracteres del md5 del propio archivo. Al cambiar
el CSS cambia la URL, asi que el navegador se ve obligado a bajarlo de nuevo.

Por que importa: el Caddyfile sirve el CSS y el JS con max-age=3600. Sin esta
huella, un visitante que ya tenga el sitio abierto puede seguir viendo el
diseno viejo hasta una hora despues del despliegue. El HTML si se revalida
siempre, asi que la pagina nueva apunta al asset nuevo de inmediato.

Hay que correrlo antes de cada despliegue en el que se haya tocado el CSS o el
JS (y volver a commitear las paginas que queden modificadas).
"""

import glob
import hashlib
import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# (ruta del asset, patron que lo referencia en el HTML)
ASSETS = [
    ("css/style.css", re.compile(r'(href=")(css/style\.css)(?:\?v=[0-9a-f]+)?(")')),
    ("js/app.js",     re.compile(r'(src=")(js/app\.js)(?:\?v=[0-9a-f]+)?(")')),
]


def huella(ruta):
    with open(os.path.join(ROOT, ruta), "rb") as f:
        return hashlib.md5(f.read()).hexdigest()[:8]


def main():
    versiones = [(pat, ruta, huella(ruta)) for ruta, pat in ASSETS]
    for ruta, _ in ASSETS:
        print("%-16s %s" % (ruta, huella(ruta)))

    tocados = 0
    for pagina in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        original = io.open(pagina, encoding="utf-8").read()
        nuevo = original
        for pat, ruta, v in versiones:
            nuevo = pat.sub(r'\g<1>\g<2>?v=' + v + r'\g<3>', nuevo)
        if nuevo != original:
            io.open(pagina, "w", encoding="utf-8", newline="").write(nuevo)
            tocados += 1
            print("  actualizado %s" % os.path.basename(pagina))

    print("%d pagina(s) actualizada(s)" % tocados)


if __name__ == "__main__":
    main()
