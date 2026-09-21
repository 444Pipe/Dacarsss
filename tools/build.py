# -*- coding: utf-8 -*-
"""
Corre el pipeline completo del sitio, en orden.

    python tools/build.py

Existe porque el orden importa y antes no estaba escrito en ningun lado:
generar-servicios.py SOBRESCRIBE las 9 landings, asi que todo lo que las
retoca tiene que correr despues. Correr los scripts sueltos y en otro orden
deja el sitio a medio parchear (fue lo que paso con los iconos de marca).

    1. generar-servicios.py   crea las 10 landings desde cero
    2. generar-meta.py        hub departamental del Meta
    3. patch-index.py         capa de SEO local sobre index.html
    4. patch-video.py         hero, reels y testimonio en index.html
    5. patch-carga.py         pantalla de carga
    6. fix-iconos.py          glifos de marca correctos (WhatsApp, IG, FB)
    7. generar-sitemap.py     sitemap.xml desde las paginas que existen
    8. usar-cloudinary.py     assets a Cloudinary
    9. versionar-assets.py    huella de contenido en css/js  <- SIEMPRE ultimo

El 2 va detras del 1 porque generar-meta.py importa la plantilla compartida
(TPL_CABEZA / TPL_PIE) de generar-servicios.py y escribe una pagina mas, que
los parcheadores 5 y 6 tienen que alcanzar.

Los pasos 1-6 emiten rutas locales (statics/...) y el 8 las convierte, asi que
el 8 no se puede adelantar.

El 7 queda encajonado entre los parcheadores y Cloudinary a proposito:
generar-sitemap.py le pone a cada URL un lastmod que solo se mueve cuando la
huella del HTML cambia. Si corriera antes del 6 la huella seria de una pagina
a medio parchear, y si corriera despues del 8 cada resubida de un asset a
Cloudinary (que cambia el /v<numero>/ de las URLs) moveria la fecha de las 12
paginas sin que el contenido hubiera cambiado. Ahi el lastmod dejaria de
significar nada, que es la forma mas facil de que Google deje de mirarlo.

Y el 9 va despues del 8 por una razon concreta: versionar-assets.py calcula el
md5 de js/app.js, y usar-cloudinary.py MODIFICA js/app.js (le mete las URLs de
los posters del hero). Si se corriera al reves, el ?v= del HTML tendria el hash
del app.js viejo y los navegadores se quedarian con la version cacheada.

FUERA DEL PIPELINE, a proposito:
    generar-video.py     necesita ffmpeg y los reels originales. Se corre a
                         mano cuando cambia el material de video.
    subir-cloudinary.py  necesita red y credenciales. Se corre a mano cuando
                         cambian los archivos de statics/.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PASOS = [
    ("generar-servicios.py", "las 10 landings de servicio"),
    ("generar-meta.py", "hub departamental del Meta"),
    ("patch-index.py", "SEO local en la portada"),
    ("patch-video.py", "hero, reels y testimonio"),
    ("patch-carga.py", "pantalla de carga"),
    ("fix-iconos.py", "glifos de marca"),
    ("generar-sitemap.py", "sitemap.xml"),
    ("usar-cloudinary.py", "assets a Cloudinary"),
    ("versionar-assets.py", "huella de contenido en css/js"),
]


def main():
    # Sin esto, los print con tildes de los scripts revientan en consolas
    # Windows que no estan en UTF-8.
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8")

    for i, (script, que) in enumerate(PASOS, 1):
        ruta = os.path.join(ROOT, "tools", script)
        if not os.path.exists(ruta):
            sys.exit("Falta tools/%s" % script)

        print("\n[%d/%d] %-22s %s" % (i, len(PASOS), script, que))
        print("-" * 64)
        # Sin el flush, el stdout del padre queda en buffer y la salida del
        # hijo aparece ANTES de su propio encabezado.
        sys.stdout.flush()
        res = subprocess.run([sys.executable, ruta], cwd=ROOT, env=entorno)
        if res.returncode != 0:
            sys.exit(
                "\nFALLO en %s (codigo %d).\n"
                "El sitio quedo a medio generar: arregla el error y volve a "
                "correr tools/build.py entero, no los pasos sueltos.\n"
                % (script, res.returncode)
            )

    print("\n" + "=" * 64)
    print("Listo. El sitio quedo consistente.")
    print("Para verlo:  python -m http.server 5173")


if __name__ == "__main__":
    main()
