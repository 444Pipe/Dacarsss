"""Convierte las fotos del local en fotos de catálogo.

Las fotos llegan como las toma alguien en el mostrador: la caja en la mano,
con el piso y las vitrinas detrás. Este script recorta la caja, le saca la
mano y el fondo, la endereza si vino torcida y la pone sobre un fondo de
estudio con los colores del sitio (grafito, brillo azul de marca y sombra de
apoyo). Sale un cuadrado de 1200 px en WebP, listo para
`catalogo/semillas/fotos/`.

    python tools/fotos-catalogo.py --origen <carpeta con los IMG_xxxx.HEIC|jpg>

Qué foto usa cada producto y qué hay que taparle está en FOTOS, abajo. Si
alguien toma fotos nuevas, se cambia el número de la foto y se corre de nuevo.

Necesita: pillow, pillow-heif, rembg[cpu], opencv-python-headless, numpy.
El modelo de recorte (BiRefNet, ~1 GB) lo baja rembg la primera vez y lo deja
en ~/.rembg. Se probó primero isnet-general-use, que es seis veces más
liviano: se confundía con las cajas negras sobre el piso negro del local y a
veces se quedaba con el brazo en vez de la caja. Tarda unos 25 s por foto.

Lo que NO hace: las fotos del producto instalado en un carro. Esas no se
pueden sacar de una foto de la caja; se generan aparte (Higgsfield) y se
marcan como «imagen de referencia» en el panel.
"""

import argparse
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except ImportError:  # las fotos ya convertidas a JPG no lo necesitan
    pass

LADO = 1200
DESTINO = Path(__file__).resolve().parents[1] / "catalogo" / "semillas" / "fotos"

# slug -> fotos. Cada foto: (número de IMG, nombre de salida, opciones).
#   tapar_rojo  borra lo escrito a mano con marcador rojo (el precio viejo)
#   esquinas    las cuatro esquinas de la cara de la caja, en píxeles de la
#               foto original (arriba-izq, arriba-der, abajo-der, abajo-izq).
#               Para cuando el recorte automático no encuentra la caja: una
#               caja negra sobre el piso negro del local, por ejemplo. La
#               cara se endereza con una transformación de perspectiva.
#   girar       grados (antihorario) después de enderezar
#   tapar_marcador  zonas (x0, y0, x1, y1, en fracciones de la caja ya
#               recortada) donde hay algo escrito a mano con marcador, sobre
#               un color saturado (el amarillo de la caja del sensor)
FOTOS = {
    "luz-led-para-baul-osram-ledambient-trunk-light": [("5770", "osram-trunk-1"), ("5771", "osram-trunk-2")],
    "bombillo-led-h4-c12-super-power-6000k": [("5773", "c12-h4-1"), ("5774", "c12-h4-2")],
    "carplay-ai-box-android-para-pantalla-original": [("5775", "ai-box-1")],
    "adaptador-carplay-inalambrico-rwdp15": [("5777", "rwdp15-1", {"tapar_rojo": True})],
    "adaptador-inalambrico-carplay-y-android-auto-2-en-1": [("5779", "xuda-1")],
    "bombillo-led-h11-imax-pro": [("5781", "imax-pro-1"), ("5782", "imax-pro-2")],
    "alarma-de-reversa-loyta-107-db": [("5784", "loyta-1")],
    "kit-iluminacion-led-ambiente-18-en-1": [
        ("5787", "ambiente-18-1", {"esquinas": [(1371, 427), (2038, 240), (2845, 2714), (1954, 2943)], "girar": -90}),
    ],
    "luces-decorativas-novotec": [("5789", "novotec-deco-1")],
    "restaurador-jcm-plastico-caucho-vinilo-cuero": [("5836", "jcm-1"), ("5837", "jcm-2")],
    "pito-caracol-elephant-future-ninety": [("5838", "elephant-90-1"), ("5839", "elephant-90-2")],
    "pito-de-disco-elephant-super-micro-sm-70d": [("5840", "elephant-sm70d-1"), ("5841", "elephant-sm70d-2")],
    "encendido-por-boton-smart-key-novotec": [("5842", "smart-key-1"), ("5843", "smart-key-2")],
    "sensor-de-parqueo-con-video": [
        ("5844", "sensor-video-1", {"tapar_marcador": [(0.64, 0.49, 0.87, 0.62)]}),
        ("5845", "sensor-video-2", {"tapar_marcador": [(0.36, 0.53, 0.58, 0.64)]}),
    ],
    "camara-de-reversa-tipo-domo-hanex-hx-cm01": [("5846", "hanex-1")],
    "camara-de-reversa-hd-a-prueba-de-agua": [("5847", "cam-waterproof-1"), ("5848", "cam-waterproof-2")],
    "camara-de-reversa-hd-gran-angular": [("5849", "cam-170-1"), ("5850", "cam-170-2")],
    "camara-para-carro-ultra-dvr-ult-801-dos-canales": [("5851", "ultra-801-1"), ("5852", "ultra-801-2")],
    "camara-de-reversa-jlt": [("5853", "jlt-1"), ("5854", "jlt-2")],
}


# --------------------------------------------------------------------------
# Recorte
# --------------------------------------------------------------------------
def abrir(origen, numero):
    """La foto, girada según el EXIF y reducida a 2400 px. Devuelve también
    la escala, para llevar las esquinas marcadas en la original."""
    for ext in (".HEIC", ".heic", ".jpg", ".JPG", ".jpeg"):
        ruta = origen / ("IMG_" + numero + ext)
        if ruta.exists():
            im = ImageOps.exif_transpose(Image.open(ruta)).convert("RGB")
            ancho = im.width
            im.thumbnail((2400, 2400), Image.LANCZOS)
            return im, im.width / ancho
    raise FileNotFoundError("No está IMG_" + numero + " en " + str(origen))


def mascara(im, sesion):
    """La silueta de la caja, sin la mano.

    El modelo deja la mano como un fantasma semitransparente: se endurece el
    alfa, se queda solo el pedazo más grande (la caja) y se le rellenan los
    huecos (los reflejos del plástico a veces se leen como fondo).
    """
    from rembg import remove

    alfa = np.asarray(remove(im, session=sesion, only_mask=True), dtype=np.float32) / 255
    alfa = np.clip((alfa - 0.35) / 0.3, 0, 1)

    binaria = (alfa > 0.5).astype(np.uint8)
    n, etiquetas, datos, _ = cv2.connectedComponentsWithStats(binaria, 8)
    if n <= 1:
        raise ValueError("no se encontró el producto")
    mayor = 1 + int(np.argmax(datos[1:, cv2.CC_STAT_AREA]))
    caja = (etiquetas == mayor).astype(np.uint8)

    # Huecos adentro de la caja: todo lo que no se alcanza desde el borde.
    relleno = caja.copy()
    h, w = caja.shape
    borde = np.zeros((h + 2, w + 2), np.uint8)
    cv2.floodFill(relleno, borde, (0, 0), 1)
    caja = caja | (1 - relleno)

    # El borde suave del modelo se conserva, pero solo alrededor de la caja.
    cerca = cv2.dilate(caja, np.ones((5, 5), np.uint8))
    alfa = np.maximum(alfa * cerca, caja.astype(np.float32))
    return alfa, caja


def tapar_rojo(rgb, caja):
    """Borra lo escrito con marcador rojo (el precio a mano en la caja).

    El umbral de saturación es bajo a propósito: el trazo fino del marcador
    sobre el cartón plateado queda rosado, no rojo. El plateado casi no tiene
    saturación, así que no hay riesgo de comerse la caja.
    """
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    rojo = (((hsv[..., 0] < 15) | (hsv[..., 0] > 155)) & (hsv[..., 1] > 38) & (hsv[..., 2] > 50))
    rojo = (rojo & (caja > 0)).astype(np.uint8)
    rojo = cv2.morphologyEx(rojo, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
    rojo = cv2.dilate(rojo, np.ones((15, 15), np.uint8))
    rgb = cv2.inpaint(rgb, rojo * 255, 12, cv2.INPAINT_TELEA)
    # El relleno arrastra un velo rosado. Sobre una caja plateada no hay rosado
    # legítimo: se le quita el color a lo que quedó.
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    velo = cv2.dilate(rojo, np.ones((25, 25), np.uint8)) > 0
    velo &= ((hsv[..., 0] < 20) | (hsv[..., 0] > 150))
    hsv[..., 1][velo] = 0
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)


def rellenar_mordidas(rgb, alfa, caja):
    """Donde los dedos tapaban el borde, la silueta queda mordida.

    Una caja es convexa: su silueta real es la envolvente convexa del
    recorte. Lo que falta se rellena con lo que lo rodea. Si lo que falta es
    mucho, no es una mordida sino otra forma, y se deja como está.
    """
    contornos, _ = cv2.findContours(caja, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    casco = np.zeros_like(caja)
    cv2.fillPoly(casco, [cv2.convexHull(max(contornos, key=cv2.contourArea))], 1)
    mordida = (casco > 0) & (caja == 0)
    if mordida.sum() > 0.12 * casco.sum():
        return rgb, alfa, caja
    rgb = cv2.inpaint(rgb, mordida.astype(np.uint8) * 255, 15, cv2.INPAINT_TELEA)
    borde = cv2.GaussianBlur(casco.astype(np.float32), (3, 3), 0)
    return rgb, np.maximum(alfa, borde), casco


def tapar_marcador(rgba, zonas):
    """Borra lo escrito a mano con marcador dentro de las zonas dadas.

    El trazo fino sale gris, no negro: se lo reconoce por la falta de color
    contra el amarillo, no solo por lo oscuro. Por eso las zonas tienen que
    caer enteras sobre el color de fondo.
    """
    rgb = np.asarray(rgba.convert("RGB")).copy()
    h, w = rgb.shape[:2]
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    oscuro = ((hsv[..., 1] < 170) | (hsv[..., 2] < 150)).astype(np.uint8)
    marca = np.zeros_like(oscuro)
    for x0, y0, x1, y1 in zonas:
        a, b, c, d = int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h)
        marca[b:d, a:c] = oscuro[b:d, a:c]
    marca = cv2.dilate(marca, np.ones((11, 11), np.uint8))
    limpio = Image.fromarray(cv2.inpaint(rgb, marca * 255, 9, cv2.INPAINT_TELEA)).convert("RGBA")
    limpio.putalpha(rgba.getchannel("A"))
    return limpio


def de_esquinas(im, esquinas, escala):
    """Endereza la cara de la caja a partir de sus cuatro esquinas."""
    p = np.array(esquinas, np.float32) * escala
    ancho = (np.linalg.norm(p[1] - p[0]) + np.linalg.norm(p[2] - p[3])) / 2
    alto = (np.linalg.norm(p[3] - p[0]) + np.linalg.norm(p[2] - p[1])) / 2
    destino = np.array([[0, 0], [ancho, 0], [ancho, alto], [0, alto]], np.float32)
    matriz = cv2.getPerspectiveTransform(p, destino)
    plano = cv2.warpPerspective(np.asarray(im), matriz, (round(ancho), round(alto)), flags=cv2.INTER_CUBIC)
    return Image.fromarray(plano).convert("RGBA")


def enderezar(rgba, caja):
    """Si la caja se ve de frente y quedó torcida, la nivela.

    Solo cuando la silueta es casi un rectángulo: una caja vista en tres
    cuartos no tiene un «abajo» recto, y girarla la empeora.
    """
    contornos, _ = cv2.findContours(caja, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contorno = max(contornos, key=cv2.contourArea)
    rect = cv2.minAreaRect(contorno)
    (_, _), (rw, rh), _ = rect
    if rw * rh == 0 or cv2.contourArea(contorno) / (rw * rh) < 0.93:
        return rgba
    puntos = cv2.boxPoints(rect)
    lados = [(puntos[i], puntos[(i + 1) % 4]) for i in range(4)]
    angulos = []
    for a, b in lados:
        ang = math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
        while ang > 45:
            ang -= 90
        while ang <= -45:
            ang += 90
        angulos.append(ang)
    angulo = float(np.median(angulos))
    if abs(angulo) < 0.6 or abs(angulo) > 20:
        return rgba
    return rgba.rotate(angulo, resample=Image.BICUBIC, expand=True)


def producto(im, escala, sesion, opciones):
    if opciones.get("esquinas"):
        rgba = de_esquinas(im, opciones["esquinas"], escala)
    else:
        alfa, caja = mascara(im, sesion)
        rgb = np.asarray(im).copy()
        rgb, alfa, caja = rellenar_mordidas(rgb, alfa, caja)
        if opciones.get("tapar_rojo"):
            rgb = tapar_rojo(rgb, caja)
        rgba = Image.fromarray(rgb).convert("RGBA")
        rgba.putalpha(Image.fromarray((alfa * 255).astype(np.uint8)))
        rgba = enderezar(rgba, caja)
        rgba = rgba.crop(rgba.getbbox())
    if opciones.get("girar"):
        rgba = rgba.rotate(opciones["girar"], expand=True)
    if opciones.get("tapar_marcador"):
        rgba = tapar_marcador(rgba, opciones["tapar_marcador"])

    # Un poco de vida: la luz del local es plana y amarillenta.
    rgb, a = rgba.convert("RGB"), rgba.getchannel("A")
    rgb = ImageEnhance.Contrast(rgb).enhance(1.07)
    rgb = ImageEnhance.Color(rgb).enhance(1.06)
    rgba = rgb.convert("RGBA")
    rgba.putalpha(a)
    return rgba


# --------------------------------------------------------------------------
# Estudio
# --------------------------------------------------------------------------
def fondo():
    """Grafito con un brillo azul de marca (#0a5cff) detrás del producto."""
    y, x = np.mgrid[0:LADO, 0:LADO].astype(np.float32) / LADO
    arriba, abajo = np.array([16, 24, 42], np.float32), np.array([5, 8, 15], np.float32)
    base = arriba * (1 - y[..., None]) + abajo * y[..., None]

    d = np.sqrt((x - 0.5) ** 2 + ((y - 0.46) * 1.15) ** 2)
    brillo = np.clip(1 - d / 0.55, 0, 1) ** 2
    base += brillo[..., None] * np.array([10, 60, 170], np.float32) * 0.42

    # El piso: una franja apenas más clara donde apoya el producto.
    piso = np.exp(-((y - 0.84) / 0.07) ** 2) * np.clip(1 - np.abs(x - 0.5) / 0.5, 0, 1)
    base += piso[..., None] * np.array([30, 45, 80], np.float32) * 0.35

    ruido = np.random.default_rng(7).normal(0, 1.3, base.shape)  # sin bandas en el degradé
    return Image.fromarray(np.clip(base + ruido, 0, 255).astype(np.uint8)).convert("RGBA")


def componer(prod):
    ancho_max, alto_max = LADO * 0.74, LADO * 0.66
    escala = min(ancho_max / prod.width, alto_max / prod.height)
    prod = prod.resize((round(prod.width * escala), round(prod.height * escala)), Image.LANCZOS)
    rgb, a = prod.convert("RGB"), prod.getchannel("A")
    rgb = rgb.filter(ImageFilter.UnsharpMask(radius=1.4, percent=60, threshold=2))
    prod = rgb.convert("RGBA")
    prod.putalpha(a)

    lienzo = fondo()
    x = (LADO - prod.width) // 2
    pie = round(LADO * 0.84)
    y = pie - prod.height

    # Sombra de apoyo: una elipse oscura y difusa bajo la base.
    sombra = Image.new("L", (LADO, LADO), 0)
    s = np.zeros((LADO, LADO), np.uint8)
    cv2.ellipse(s, (LADO // 2, pie), (int(prod.width * 0.46), max(12, int(prod.height * 0.035))), 0, 0, 360, 190, -1)
    sombra = Image.fromarray(s).filter(ImageFilter.GaussianBlur(22))
    negro = Image.new("RGBA", (LADO, LADO), (0, 0, 0, 255))
    negro.putalpha(sombra)
    lienzo.alpha_composite(negro)

    # Reflejo tenue en el piso.
    reflejo = ImageOps.flip(prod)
    degrade = np.linspace(0.16, 0, reflejo.height, dtype=np.float32)[:, None]
    ra = (np.asarray(reflejo.getchannel("A"), np.float32) * degrade).astype(np.uint8)
    reflejo.putalpha(Image.fromarray(ra))
    reflejo = reflejo.filter(ImageFilter.GaussianBlur(2))
    lienzo.alpha_composite(reflejo, (x, pie + 2))

    lienzo.alpha_composite(prod, (x, y))
    return lienzo.convert("RGB")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--origen", required=True, type=Path, help="Carpeta con los IMG_xxxx")
    parser.add_argument("--destino", type=Path, default=DESTINO)
    parser.add_argument("--solo", nargs="*", help="Solo estos nombres de salida")
    args = parser.parse_args()

    from rembg import new_session

    sesion = new_session("birefnet-general")
    args.destino.mkdir(parents=True, exist_ok=True)
    for slug, fotos in FOTOS.items():
        for foto in fotos:
            numero, salida = foto[0], foto[1]
            opciones = foto[2] if len(foto) > 2 else {}
            if args.solo and salida not in args.solo:
                continue
            im, escala = abrir(args.origen, numero)
            final = componer(producto(im, escala, sesion, opciones))
            ruta = args.destino / (salida + ".webp")
            final.save(ruta, "WEBP", quality=86, method=6)
            print("{:<22} IMG_{}  {:>4} KB".format(salida, numero, ruta.stat().st_size // 1024))


if __name__ == "__main__":
    main()
