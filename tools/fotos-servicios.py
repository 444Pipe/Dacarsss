# -*- coding: utf-8 -*-
"""
Prepara una foto para la intro de una landing de servicio.

    python tools/fotos-servicios.py <imagen-original> <nombre>

    python tools/fotos-servicios.py ~/Descargas/latoneria.png latoneria

Recorta al centro en cuadrado y deja tres WebP en static/img/servicios/:
<nombre>-600.webp, <nombre>-900.webp y <nombre>-1200.webp. Son los que pide
templates/sitio/_intro_foto.html con foto="<nombre>".

Por qué cuadrado: en PC la foto se muestra 4:5 y en celular 4:3, y las dos se
recortan de la misma imagen con object-fit. Desde un cuadrado ninguno de los
dos recortes pierde más de una cuarta parte, así que el motivo tiene que ir al
centro del encuadre.

El original no se guarda en el repo: la de 1200 ya es la copia de trabajo.
"""

import os
import sys

try:
    from PIL import Image
except ImportError:
    sys.exit("Falta Pillow:\n\n    pip install Pillow\n")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DESTINO = os.path.join(ROOT, "static", "img", "servicios")
LADOS = (600, 900, 1200)


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    origen, nombre = sys.argv[1], sys.argv[2]

    img = Image.open(origen).convert("RGB")
    lado = min(img.size)
    if lado < max(LADOS):
        print(f"Ojo: la original mide {img.size[0]}x{img.size[1]}; la de 1200 va a salir estirada.")
    x = (img.width - lado) // 2
    y = (img.height - lado) // 2
    img = img.crop((x, y, x + lado, y + lado))

    os.makedirs(DESTINO, exist_ok=True)
    for n in LADOS:
        ruta = os.path.join(DESTINO, f"{nombre}-{n}.webp")
        img.resize((n, n), Image.LANCZOS).save(ruta, "WEBP", quality=80, method=6)
        print(f"{os.path.relpath(ruta, ROOT)}  {os.path.getsize(ruta) // 1024} KB")


if __name__ == "__main__":
    main()
