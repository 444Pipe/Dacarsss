# -*- coding: utf-8 -*-
"""
Corre el pipeline completo del sitio, en orden.

    python tools/build.py

Existe porque el orden importa y antes no estaba escrito en ningun lado:
generar-servicios.py SOBRESCRIBE las 9 landings, asi que todo lo que las
retoca tiene que correr despues. Correr los scripts sueltos y en otro orden
deja el sitio a medio parchear (fue lo que paso con los iconos de marca).

    1. generar-servicios.py   crea las 9 landings desde cero
    2. patch-index.py         capa de SEO local sobre index.html
    3. patch-video.py         hero, reels y testimonio en index.html
    4. patch-carga.py         pantalla de carga
    5. fix-iconos.py          glifos de marca correctos (WhatsApp, IG, FB)
    6. usar-cloudinary.py     assets a Cloudinary
    7. versionar-assets.py    huella de contenido en css/js  <- SIEMPRE ultimo

Los pasos 1-5 emiten rutas locales (statics/...) y el 6 las convierte, asi que
el 6 no se puede adelantar.

Y el 7 va despues del 6 por una razon concreta: versionar-assets.py calcula el
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
    ("generar-servicios.py", "las 9 landings de servicio"),
    ("patch-index.py", "SEO local en la portada"),
    ("patch-video.py", "hero, reels y testimonio"),
    ("patch-carga.py", "pantalla de carga"),
    ("fix-iconos.py", "glifos de marca"),
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
