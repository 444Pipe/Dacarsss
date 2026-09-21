# -*- coding: utf-8 -*-
"""
Genera los iconos del sitio: el logo sobre un cuadrado azul marino.

    python tools/generar-iconos.py

Deja en static/img/icono/:

  favicon.ico            16, 32 y 48 px. La pestana, y lo que pide el
                         navegador (y Google) en /favicon.ico.
  icono-192.png          el <link rel="icon"> grande y el manifest.
  icono-512.png          el manifest (pantalla de inicio en Android).
  icono-maskable-512.png el mismo, con el logo mas chico: Android lo recorta
                         en circulo o en gota, y solo garantiza el 80 % central.
  apple-touch-icon.png   180 px, la pantalla de inicio del iPhone.

Por que con fondo propio: antes el icono era el logo con fondo transparente, y
cada lugar que lo muestra (la pestana, el resultado de Google, el celular) le
ponia el fondo que queria. Un fondo fijo hace que se vea igual en todos lados.

El fondo es negro puro, como la foto de perfil de la marca: el logo (cromo y
destellos azules) esta pensado para verse sobre negro.

Por que cuadrado: el logo mide 1000x729. Un icono que no es cuadrado lo
aplastan o le meten bandas, y Google solo acepta cuadrados (multiplo de 48 px).

Fuente: statics/logo-dacars.png, que esta en el repo pero no en la imagen de
Docker. Los iconos generados si viajan: estan en static/.
"""

import os

try:
    from PIL import Image
except ImportError:
    raise SystemExit("Falta Pillow:\n\n    pip install Pillow\n")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(ROOT, "statics", "logo-dacars.png")
DESTINO = os.path.join(ROOT, "static", "img", "icono")

FONDO = (0, 0, 0)  # negro, como la foto de perfil de la marca

# Cuanto del ancho ocupa el logo
ANCHO_NORMAL = 0.86
# En el maskable, las puntas del logo tienen que caer dentro del circulo del
# 80 % central: con la proporcion del logo eso da un 64 % de ancho.
ANCHO_MASKABLE = 0.64


def cargar_logo():
    logo = Image.open(ORIGEN).convert("RGBA")
    # Recorte al contenido: el PNG trae aire transparente alrededor
    visible = logo.getchannel("A").point(lambda a: 255 if a > 8 else 0)
    return logo.crop(visible.getbbox())


def icono(logo, lado, ancho):
    # Se compone a 4x y se reduce: a 16 px, componer directo deja el logo
    # mas sucio que reducirlo desde grande.
    grande = lado * 4
    base = Image.new("RGBA", (grande, grande), FONDO + (255,))
    w = round(grande * ancho)
    h = round(logo.height * w / logo.width)
    base.alpha_composite(logo.resize((w, h), Image.LANCZOS),
                         ((grande - w) // 2, (grande - h) // 2))
    return base.resize((lado, lado), Image.LANCZOS).convert("RGB")


def main():
    logo = cargar_logo()
    os.makedirs(DESTINO, exist_ok=True)

    salidas = {
        "icono-192.png": icono(logo, 192, ANCHO_NORMAL),
        "icono-512.png": icono(logo, 512, ANCHO_NORMAL),
        "icono-maskable-512.png": icono(logo, 512, ANCHO_MASKABLE),
        "apple-touch-icon.png": icono(logo, 180, ANCHO_NORMAL),
    }
    for nombre, img in salidas.items():
        img.save(os.path.join(DESTINO, nombre), optimize=True)

    tamanos = [16, 32, 48]
    capas = [icono(logo, t, ANCHO_NORMAL) for t in tamanos]
    capas[-1].save(os.path.join(DESTINO, "favicon.ico"), format="ICO",
                   sizes=[(t, t) for t in tamanos], append_images=capas[:-1])

    for nombre in sorted(os.listdir(DESTINO)):
        ruta = os.path.join(DESTINO, nombre)
        print("  static/img/icono/%-24s %6d B" % (nombre, os.path.getsize(ruta)))


if __name__ == "__main__":
    main()
