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
    (2, 5.4),    # manos aplicando el PPF
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

# Recorte por reel y formato. El origen siempre es 720x1280.
RECORTES = {
    "16x9": {1: "crop=720:405:0:340", 2: "crop=720:405:0:320",
             3: "crop=720:405:0:300", 4: "crop=720:405:0:300",
             5: "crop=720:405:0:285"},
    "3x4":  {1: "crop=720:960:0:50", 2: "crop=720:960:0:60",
             3: "crop=720:960:0:60", 4: "crop=720:960:0:60",
             5: "crop=720:700:0:0,scale=987:960,crop=720:960:133:0"},
}

DESTINO = {
    # lanczos + microenfoque: el 16:9 nace de una franja de 405 px y se
    # amplia 1,78x, sin esto llega blando a las pantallas grandes
    "16x9": "scale=1280:720:flags=lanczos,unsharp=5:5:0.45:5:5:0",
    "3x4": "scale=720:960:flags=lanczos",
}


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
        sh(["ffmpeg", "-y", "-v", "error",
            "-ss", str(inicio), "-t", str(d), "-i", vs[reel - 1],
            "-vf", RECORTES[formato][reel] + "," + DESTINO[formato] +
                   ",setsar=1,fps=30,"
                   "eq=contrast=1.05:saturation=1.12:brightness=0.02,"
                   # Levanta sombras y medios para que el video se lea debajo
                   # del velo del hero. El techo queda en 0.96 (no en blanco
                   # puro) para que el titular conserve contraste.
                   "curves=all='0/0.02 0.20/0.27 0.45/0.57 0.72/0.82 1/0.96'",
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
        montaje("3x4")
        if os.path.isdir(TMP) and not os.listdir(TMP):
            os.rmdir(TMP)

    if que in ("todo", "reels"):
        print("\nGaleria de video (5 reels completos):")
        galeria()

    print("\nListo -> statics/video/")


if __name__ == "__main__":
    main()
