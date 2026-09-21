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

El fondo es el del hero del sitio: #071020 con la misma cuadricula azul tenue
(.grid en style.css), que se apaga hacia los bordes. La cuadricula va solo en
los tamanos grandes: a 16-48 px las lineas serian ruido, asi que la pestana
queda con el azul liso.

Por que cuadrado: el logo mide 1000x729. Un icono que no es cuadrado lo
aplastan o le meten bandas, y Google solo acepta cuadrados (multiplo de 48 px).

Fuente: statics/logo-dacars.png, que esta en el repo pero no en la imagen de
Docker. Los iconos generados si viajan: estan en static/.
"""

import math
import os

try:
    from PIL import Image, ImageChops, ImageDraw
except ImportError:
    raise SystemExit("Falta Pillow:\n\n    pip install Pillow\n")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ORIGEN = os.path.join(ROOT, "statics", "logo-dacars.png")
DESTINO = os.path.join(ROOT, "static", "img", "icono")

FONDO = (0x07, 0x10, 0x20)  # el del hero del sitio

# La cuadricula de .grid en style.css: lineas rgba(122,163,255,.055) de 1 px
# cada 62 px, con una mascara radial que las apaga hacia afuera. Aqui el icono
# es mucho mas chico que una pantalla, asi que se escala a ~7 celdas por lado
# y se sube un poco la opacidad para que se alcance a ver.
LINEA = (122, 163, 255)
LINEA_ALFA = 0.16
CELDAS = 7
CUADRICULA_DESDE = 128  # px de lado; debajo de esto, fondo liso

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


def fondo(lado, con_cuadricula):
    base = Image.new("RGBA", (lado, lado), FONDO + (255,))
    if not con_cuadricula:
        return base
    lineas = Image.new("L", (lado, lado), 0)
    trazo = ImageDraw.Draw(lineas)
    paso = lado / CELDAS
    grosor = max(1, round(lado / 180))
    for i in range(1, CELDAS):
        p = round(i * paso)
        trazo.rectangle([p, 0, p + grosor - 1, lado], fill=255)
        trazo.rectangle([0, p, lado, p + grosor - 1], fill=255)
    # Mascara radial como la del sitio: plena al centro, nada en las esquinas
    # Es un degradado suave: se calcula a 256 px y se escala.
    chica = 256
    mascara = Image.new("L", (chica, chica), 0)
    px = mascara.load()
    c = chica / 2.0
    for y in range(chica):
        for x in range(chica):
            d = math.hypot((x - c) / (0.75 * c), (y - c * 0.92) / (0.72 * c))
            px[x, y] = int(255 * max(0.0, 1 - d / 1.04))
    mascara = mascara.resize((lado, lado), Image.BILINEAR)
    alfa = ImageChops.multiply(lineas, mascara).point(lambda v: int(v * LINEA_ALFA))
    capa = Image.new("RGBA", (lado, lado), LINEA + (0,))
    capa.putalpha(alfa)
    base.alpha_composite(capa)
    return base


def icono(logo, lado, ancho):
    # Se compone a 4x y se reduce: a 16 px, componer directo deja el logo
    # mas sucio que reducirlo desde grande.
    grande = lado * 4
    base = fondo(grande, lado >= CUADRICULA_DESDE)
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
