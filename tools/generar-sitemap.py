# -*- coding: utf-8 -*-
"""
Genera sitemap.xml a partir de las paginas que existen de verdad.

    python tools/generar-sitemap.py

Antes el sitemap se editaba a mano y por eso se quedaba viejo: listaba 10 URLs
con un lastmod congelado en la fecha en que alguien se acordo de tocarlo. Al
sumar una landing nueva habia que acordarse de agregarla, y nadie se acuerda.

SOBRE lastmod, que es la parte con miga
  Poner la fecha de hoy en cada build seria mentir: el pipeline regenera las
  11 paginas en cada corrida, aunque no haya cambiado una coma. Un sitemap que
  dice «todo cambio hoy» todos los dias es un sitemap que Google deja de creer,
  y entonces deja de usar lastmod para priorizar el rastreo.

  Asi que se guarda la huella del contenido de cada pagina en
  tools/sitemap-fechas.json y la fecha solo se mueve cuando la huella cambia.

POR ESO IMPORTA EL ORDEN EN EL PIPELINE (ver tools/build.py)
  Corre DESPUES de los generadores y parcheadores, para que la huella sea la
  del HTML definitivo; y ANTES de usar-cloudinary.py y versionar-assets.py,
  que reescriben las paginas con URLs y hashes que cambian por su cuenta. Si
  corriera al final, cada resubida de un asset a Cloudinary moveria la fecha
  de las 11 paginas sin que el contenido hubiera cambiado.

  usar-cloudinary.py tambien toca este archivo: convierte el <image:loc> a la
  URL del CDN. Por eso aca se emite la ruta local.
"""

import hashlib
import io
import json
import os
import re
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = "https://www.dacarslujos.com"
ESTADO = os.path.join(ROOT, "tools", "sitemap-fechas.json")
IMAGEN = SITE + "/statics/og-image.jpg"

# (archivo, prioridad, frecuencia). El orden es el del sitemap.
# La portada y las landings de los servicios que mas se buscan van arriba.
PAGINAS = [
    ("index.html", "1.0", "monthly"),
    ("ppf-villavicencio.html", "0.9", "monthly"),
    ("polarizados-villavicencio.html", "0.9", "monthly"),
    ("detailing-villavicencio.html", "0.9", "monthly"),
    ("pintura-automotriz-villavicencio.html", "0.9", "monthly"),
    ("accesorios-4x4-villavicencio.html", "0.9", "monthly"),
    ("lujos-y-accesorios-villavicencio.html", "0.9", "monthly"),
    ("personalizacion-de-vehiculos-meta.html", "0.9", "monthly"),
    ("iluminacion-para-carros-villavicencio.html", "0.8", "monthly"),
    ("sonido-para-carros-villavicencio.html", "0.8", "monthly"),
    ("llantas-villavicencio.html", "0.8", "monthly"),
    ("pdr-desabolladura-sin-pintura-villavicencio.html", "0.8", "monthly"),
]

# Ruido que cambia sin que cambie el contenido: no debe mover el lastmod.
RUIDO = [
    re.compile(r'\?v=[0-9a-f]+'),              # huella de versionar-assets.py
    re.compile(r'/v\d{10}/'),                  # version de un asset en Cloudinary
    re.compile(r'<span id="year">\d{4}</span>'),
]


def huella(archivo):
    texto = io.open(os.path.join(ROOT, archivo), encoding="utf-8").read()
    for pat in RUIDO:
        texto = pat.sub("", texto)
    return hashlib.sha1(texto.encode("utf-8")).hexdigest()[:12]


def cargar_estado():
    if os.path.exists(ESTADO):
        return json.load(io.open(ESTADO, encoding="utf-8"))
    return {}


def main():
    estado = cargar_estado()
    hoy = date.today().isoformat()
    cambiadas = 0
    faltantes = []
    filas = []

    for archivo, prioridad, frecuencia in PAGINAS:
        if not os.path.exists(os.path.join(ROOT, archivo)):
            faltantes.append(archivo)
            continue

        h = huella(archivo)
        previo = estado.get(archivo)
        if previo is None or previo.get("huella") != h:
            estado[archivo] = {"huella": h, "fecha": hoy}
            cambiadas += 1
        fecha = estado[archivo]["fecha"]

        loc = SITE + "/" if archivo == "index.html" else SITE + "/" + archivo
        filas.append(
            "  <url>\n"
            "    <loc>%s</loc>\n"
            "    <lastmod>%s</lastmod>\n"
            "    <changefreq>%s</changefreq>\n"
            "    <priority>%s</priority>\n"
            "    <image:image>\n"
            "      <image:loc>%s</image:loc>\n"
            "      <image:title>DACARS — personalizacion de vehiculos en Villavicencio, Meta</image:title>\n"
            "    </image:image>\n"
            "  </url>" % (loc, fecha, frecuencia, prioridad, IMAGEN)
        )

    # Se limpian las paginas que ya no existen para que el archivo de estado
    # no crezca con fantasmas.
    vivos = {a for a, _, _ in PAGINAS}
    for muerto in [k for k in estado if k not in vivos]:
        del estado[muerto]

    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"\n'
           '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n'
           + "\n".join(filas) + "\n</urlset>\n")

    io.open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8", newline="\n").write(xml)
    json.dump(estado, io.open(ESTADO, "w", encoding="utf-8", newline="\n"),
              ensure_ascii=False, indent=2, sort_keys=True)

    print("sitemap.xml con %d URLs (%d con lastmod nuevo)" % (len(filas), cambiadas))
    if faltantes:
        print("OJO, falta generar: " + ", ".join(faltantes))


if __name__ == "__main__":
    main()
