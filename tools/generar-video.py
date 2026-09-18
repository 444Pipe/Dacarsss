# -*- coding: utf-8 -*-
"""
Procesa los reels de DACARS para la web.

1. Arma el fondo de video del hero: 12 de las mejores tomas de los 5 reels,
   intercaladas, con disolvencias, en dos formatos (16:9 escritorio, 3:4 movil).
2. Reencoda los 5 reels completos para la galeria de video, con su poster.

    python tools/generar-video.py            # todo
    python tools/generar-video.py hero       # solo el hero
    python tools/generar-video.py reels      # solo la galeria

Requiere ffmpeg en el PATH.

NOTA SOBRE LOS RECORTES
Los reels traen subtitulos quemados y la marca de agua DACARS. Cada recorte
esta calculado para dejarlos fuera de cuadro:
  - v1/v2/v3/v4 -> subtitulos y marca viven debajo del 83% de la altura
  - v5 (Hummer) -> los subtitulos van a media altura (~57%), por eso su
    recorte es mas alto y se reescala.
Si cambias los tiempos, revisa el encuadre antes de publicar.
"""

import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(ROOT, "statics", "hero video")
SALIDA = os.path.join(ROOT, "statics", "video")
TMP = os.path.join(SALIDA, "_tmp")

DUR = 2.2      # duracion de cada toma del hero
FADE = 0.35    # disolvencia entre tomas


def sh(args):
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        print("\n".join(r.stderr.strip().splitlines()[-12:]))
        raise SystemExit("fallo ffmpeg: " + " ".join(args[:6]) + " ...")


def fuentes():
    vs = sorted(f for f in os.listdir(FUENTES) if f.lower().endswith(".mp4"))
    if len(vs) != 5:
        raise SystemExit("esperaba 5 mp4 en '%s', encontre %d" % (FUENTES, len(vs)))
    return [os.path.join(FUENTES, v) for v in vs]


# ---------------------------------------------------------------
#  Los 5 reels (el orden es alfabetico, igual que ls)
# ---------------------------------------------------------------
REELS = [
    dict(n=1, slug="volante-gr", titulo="Volante deportivo GR",
         servicio="Lujos y accesorios", pagina="lujos-y-accesorios-villavicencio.html",
         desc="Volante deportivo en fibra de carbono instalado sobre Toyota.",
         poster=42.2),
    dict(n=2, slug="ppf-sportage", titulo="Full PPF mate — Kia Sportage",
         servicio="PPF", pagina="ppf-villavicencio.html",
         desc="Instalacion de PPF mate completo sobre un Kia Sportage 2025.",
         poster=23.8),
    dict(n=3, slug="led-4x4", titulo="Exploradoras LED 4x4",
         servicio="Iluminación", pagina="iluminacion-para-carros-villavicencio.html",
         desc="Exploradoras LED para camioneta 4x4, montaje e iluminacion.",
         poster=27.4),
    dict(n=4, slug="testimonio-cubierta", titulo="Testimonio de cliente",
         servicio="Accesorios 4x4", pagina="accesorios-4x4-villavicencio.html",
         desc="Un cliente cuenta como quedo la cubierta de platón de su camioneta.",
         poster=12.0),
    dict(n=5, slug="hummer-ev", titulo="Hummer EV — luces y rines",
         servicio="Lujos y accesorios", pagina="lujos-y-accesorios-villavicencio.html",
         desc="Personalizacion de una Hummer EV: barra LED, faros y rines.",
         poster=32.8),
]

# ---------------------------------------------------------------
#  Secuencia del hero: (reel, segundo de inicio)
#  Intercalada a proposito: nunca dos tomas seguidas del mismo reel.
# ---------------------------------------------------------------
SECUENCIA = [
    # Rotacion pareja V2 -> V3 -> V5 -> V1, tres vueltas. Nunca dos tomas
    # seguidas del mismo reel, y cierra oscuro para que el loop no se note.
    (2, 23.4),   # Sportage mate bajo el techo hexagonal
    (3, 27.0),   # pods LED ambar encendidos
    (5, 22.2),   # rin de la Hummer
    (1, 11.0),   # textura de la fibra de carbono
    (2, 8.9, 1.5),  # manos aplicando el PPF con la espatula. Ventana corta
                    # a proposito: antes de 8.9 entra un primer plano de la
                    # cara del operario y despues de 10.4 cruza su uniforme.
    (5, 25.0),   # barra LED + techo hexagonal
    (3, 7.0),    # glow ambar sobre el logo SC
    (1, 4.9),    # volante GR, luz calida
    (2, 28.4),   # lateral del Sportage
    (5, 32.8),   # frontal de la Hummer con la barra encendida
    (3, 16.0),   # capo negro con acento rojo
    (1, 42.0),   # volante Toyota en penumbra (cierre)
]

# El reel 4 (testimonio) no entra al fondo: solo tiene ~1,2 s de plano limpio
# antes de fundir a negro. Va destacado como testimonio en la pagina, que es
# donde ese material rinde.

# ---------------------------------------------------------------
#  ENCUADRE
#
#  El material es vertical (720x1280) y el hero es ancho. Recortar una
#  franja 16:9 a ancho completo solo deja 405 px de alto: el 32% de la
#  escena, que en pantalla se lee como un zoom enorme.
#
#  En vez de eso, de cada reel se toma una VENTANA alta, se centra en el
#  lienzo a su tamano y el sobrante se rellena con una copia ampliada y
#  desenfocada del mismo fotograma. Se ve mas del doble de escena y el
#  sujeto queda casi a tamano natural. Bajo el velo del hero los bordes
#  difuminados no se leen como bordes.
# ---------------------------------------------------------------

LIENZO = {"16x9": (1280, 720), "9x16": (720, 1280)}

# Alto que ocupa la zona nitida dentro del lienzo. En 16:9 llena el alto
# completo; en 9:16 se deja una banda difuminada arriba y abajo, que cae
# justo donde el velo ya es mas oscuro (header y paso al marquee).
ALTO_NITIDO = {"16x9": 720, "9x16": 880}

# Ventana tomada del original, por reel y formato: (alto, desplazamiento).
# El tope de cada reel lo marcan los subtitulos y la marca de agua quemados
# (ver NOTA SOBRE LOS RECORTES): reel 1 hasta 79%, reel 2 y 3 hasta 80%,
# reel 5 solo hasta 55%.
VENTANAS = {
    "16x9": {1: (660, 212), 2: (660, 192), 3: (660, 172),
             4: (660, 180), 5: (660, 20)},
    "9x16": {1: (880, 90), 2: (880, 100), 3: (880, 100),
             4: (880, 100), 5: (700, 0)},
}

BLUR = {"16x9": 26, "9x16": 22}   # sigma del relleno
BORDE = 56                        # px de degradado entre la zona nitida y el relleno

# Eje sobre el que se funde la zona nitida con el relleno: en 16:9 el relleno
# esta a los lados, en 9:16 arriba y abajo.
EJE = {"16x9": r"X\,W-1-X", "9x16": r"Y\,H-1-Y"}


def par(n):
    """libx264 necesita dimensiones pares."""
    n = int(round(n))
    return n if n % 2 == 0 else n + 1


def encuadre(formato, reel):
    """Ventana centrada sobre un relleno desenfocado del mismo fotograma."""
    lw, lh = LIENZO[formato]
    alto, desp = VENTANAS[formato][reel]
    nitido = ALTO_NITIDO[formato]

    # La zona nitida se escala por alto; si se pasa de ancho, se recorta al centro.
    k = nitido / float(alto)
    cw = par(720 * k)
    recorte = ",crop=%d:%d" % (lw, nitido) if cw > lw else ""

    # El relleno cubre el lienzo entero: se escala por el lado que falte.
    kf = max(lw / 720.0, lh / float(alto))

    return (
        "[0:v]crop=720:%d:0:%d,setsar=1,fps=30,split=2[n][f];"
        "[f]scale=%d:%d:flags=bilinear,crop=%d:%d,gblur=sigma=%d,"
        "eq=brightness=-0.05:saturation=0.82[relleno];"
        # El borde se funde con un degradado de alfa: sin esto la union entre
        # la zona nitida y el relleno se lee como una linea recta.
        "[n]scale=%d:%d:flags=lanczos,unsharp=5:5:0.35:5:5:0%s,format=yuva420p,"
        r"geq=lum='p(X\,Y)':cb='cb(X\,Y)':cr='cr(X\,Y)':"
        r"a='255*min(1\,min(%s)/%d)'[zona];"
        "[relleno][zona]overlay=(W-w)/2:(H-h)/2"
    ) % (alto, desp,
         par(720 * kf), par(alto * kf), lw, lh, BLUR[formato],
         cw, nitido, recorte, EJE[formato], BORDE)


def montaje(formato):
    """Corta las 12 tomas, las encadena con disolvencias y codifica."""
    vs = fuentes()
    os.makedirs(TMP, exist_ok=True)
    piezas, duraciones = [], []

    for i, toma in enumerate(SECUENCIA):
        reel, inicio = toma[0], toma[1]
        d = toma[2] if len(toma) > 2 else DUR
        duraciones.append(d)
        pieza = os.path.join(TMP, "%s_%02d.mp4" % (formato, i))
        # El grading va al final, sobre la composicion ya armada, para que la
        # zona nitida y el relleno queden con el mismo tono. Levanta sombras y
        # medios para que el video se lea debajo del velo del hero; el techo
        # queda en 0.96 (no en blanco puro) para que el titular no pierda
        # contraste sobre las tomas mas claras.
        grado = ("eq=contrast=1.05:saturation=1.12:brightness=0.02,"
                 "curves=all='0/0.02 0.20/0.27 0.45/0.57 0.72/0.82 1/0.96'")

        sh(["ffmpeg", "-y", "-v", "error",
            "-ss", str(inicio), "-t", str(d), "-i", vs[reel - 1],
            "-filter_complex", encuadre(formato, reel) + "," + grado + "[v]",
            "-map", "[v]",
            "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
            "-pix_fmt", "yuv420p", pieza])
        piezas.append(pieza)

    # cadena de xfade: el desplazamiento k-esimo es k*(DUR-FADE)
    entradas = []
    for p in piezas:
        entradas += ["-i", p]

    filtro, etiqueta = [], "[0:v]"
    largo = duraciones[0]
    for k in range(1, len(piezas)):
        salida = "[x%d]" % k
        filtro.append("%s[%d:v]xfade=transition=fade:duration=%s:offset=%s%s"
                      % (etiqueta, k, FADE, round(largo - FADE, 3), salida))
        largo += duraciones[k] - FADE
        etiqueta = salida

    total = round(largo, 3)
    # fundido desde y hacia negro: el punto de repeticion del loop queda invisible
    filtro.append("%sfade=t=in:st=0:d=0.5,fade=t=out:st=%s:d=0.5[v]"
                  % (etiqueta, round(total - 0.5, 3)))

    destino = os.path.join(SALIDA, "hero-%s.mp4" % formato)
    sh(["ffmpeg", "-y", "-v", "error"] + entradas +
       ["-filter_complex", ";".join(filtro), "-map", "[v]", "-an",
        "-c:v", "libx264", "-preset", "slow",
        "-crf", "26" if formato == "16x9" else "27",
        "-profile:v", "main", "-level", "4.0", "-pix_fmt", "yuv420p",
        "-g", "60", "-movflags", "+faststart", destino])

    # poster: el primer fotograma ya visible, no el negro del fundido
    poster = os.path.join(SALIDA, "hero-poster-%s.jpg" % formato)
    sh(["ffmpeg", "-y", "-v", "error", "-ss", "0.9", "-i", destino,
        "-frames:v", "1", "-q:v", "4", poster])

    for p in piezas:
        os.remove(p)

    kb = os.path.getsize(destino) // 1024
    print("  hero-%-5s  %5.1f s   %4d KB   poster %d KB"
          % (formato, total, kb, os.path.getsize(poster) // 1024))
    return destino


def galeria():
    """Reencoda los 5 reels completos para la galeria + poster de cada uno."""
    vs = fuentes()
    for r in REELS:
        origen = vs[r["n"] - 1]
        destino = os.path.join(SALIDA, "reel-%s.mp4" % r["slug"])
        sh(["ffmpeg", "-y", "-v", "error", "-i", origen,
            "-vf", "scale=608:1080,setsar=1",
            "-c:v", "libx264", "-preset", "slow", "-crf", "29",
            "-profile:v", "main", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "80k", "-ac", "2",
            "-movflags", "+faststart", destino])

        poster = os.path.join(SALIDA, "reel-%s.jpg" % r["slug"])
        sh(["ffmpeg", "-y", "-v", "error", "-ss", str(r["poster"]), "-i", origen,
            "-vf", "scale=608:1080", "-frames:v", "1", "-q:v", "5", poster])

        print("  reel-%-20s %5d KB   poster %3d KB   %s"
              % (r["slug"], os.path.getsize(destino) // 1024,
                 os.path.getsize(poster) // 1024, r["titulo"]))


def main():
    que = sys.argv[1] if len(sys.argv) > 1 else "todo"
    os.makedirs(SALIDA, exist_ok=True)

    if que in ("todo", "hero"):
        print("Fondo de video del hero (12 tomas, %s s cada una):" % DUR)
        montaje("16x9")
        montaje("9x16")
        if os.path.isdir(TMP) and not os.listdir(TMP):
            os.rmdir(TMP)

    if que in ("todo", "reels"):
        print("\nGaleria de video (5 reels completos):")
        galeria()

    print("\nListo -> statics/video/")


if __name__ == "__main__":
    main()
