# -*- coding: utf-8 -*-
"""
Mete el video en index.html:
  - fondo de video en el hero (con poster y respaldo)
  - galeria de reels dentro de la seccion Trabajos
  - testimonio de cliente en video, como seccion propia

Idempotente: se puede correr varias veces sin duplicar nada.
"""

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "index.html")
WA = "573112629406"

# (slug, etiqueta, titulo, pagina de servicio, texto del enlace)
CLIPS = [
    ("ppf-sportage", "PPF", "Full PPF mate en un Sportage 2025",
     "ppf-villavicencio.html", "PPF en Villavicencio"),
    ("led-4x4", "Iluminación", "Exploradoras LED para 4x4",
     "iluminacion-para-carros-villavicencio.html", "Iluminación en Villavicencio"),
    ("hummer-ev", "Lujos", "Hummer EV: barra LED, faros y rines",
     "lujos-y-accesorios-villavicencio.html", "Lujos en Villavicencio"),
    ("volante-gr", "Interior", "Volante deportivo en fibra de carbono",
     "lujos-y-accesorios-villavicencio.html", "Accesorios en Villavicencio"),
]


def bloque_clips():
    filas = []
    for slug, tag, titulo, pagina, enlace in CLIPS:
        filas.append(
            '      <article class="clip" data-reveal>\n'
            '        <div class="clip__media">\n'
            '          <video class="clip__v" src="statics/video/reel-%s.mp4"\n'
            '                 poster="statics/video/reel-%s.jpg"\n'
            '                 preload="none" playsinline loop\n'
            '                 aria-label="%s — DACARS Villavicencio"></video>\n'
            '          <span class="clip__tag">%s</span>\n'
            '          <button class="clip__btn" type="button" aria-label="Reproducir: %s"></button>\n'
            '        </div>\n'
            '        <div class="clip__meta">\n'
            '          <h3>%s</h3>\n'
            '          <a href="%s">%s &rarr;</a>\n'
            '        </div>\n'
            '      </article>' % (slug, slug, titulo, tag, titulo, titulo, pagina, enlace)
        )
    return "\n".join(filas)


SECCION_CLIPS = """
    <div class="clips">
@@CLIPS@@
    </div>

    <p class="clips__nota" data-reveal>
      <svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M10.2 8.4 15.8 12l-5.6 3.6Z" fill="currentColor" stroke="none"/></svg>
      Los videos tienen audio. Toca el botón de play para escucharlos.
    </p>
"""

SECCION_TESTIMONIO = """
<!-- ============ TESTIMONIO ============ -->
<section class="sec" id="testimonio">
  <div class="wrap testi">
    <div class="testi__media" data-reveal>
      <div class="clip">
        <div class="clip__media">
          <video class="clip__v" src="statics/video/reel-testimonio-cubierta.mp4"
                 poster="statics/video/reel-testimonio-cubierta.jpg"
                 preload="none" playsinline loop
                 aria-label="Testimonio de un cliente de DACARS Villavicencio"></video>
          <span class="clip__tag">Testimonio</span>
          <button class="clip__btn" type="button" aria-label="Reproducir el testimonio del cliente"></button>
        </div>
      </div>
    </div>

    <div class="testi__copy">
      <p class="tag" data-reveal>05 &mdash; Testimonio</p>
      <h2 class="sec__title chrome" data-reveal>Que lo cuente quien ya pasó por el taller</h2>
      <p data-reveal>Un cliente nos dejó su testimonio en video, parado junto a su camioneta,
        contando cómo le quedó la cubierta de platón que le instalamos.</p>
      <p data-reveal>Dale play &mdash;tiene audio&mdash; y escúchalo de primera mano.
        Es la mejor forma que tenemos de mostrarte cómo trabajamos.</p>
      <span class="testi__pie" data-reveal>Accesorios 4x4 &middot; <b>Cubierta de platón</b></span>
    </div>
  </div>
</section>
"""


def main():
    html = io.open(IDX, encoding="utf-8").read()

    # ---------- 1. Fondo de video en el hero ----------
    if 'id="heroVideo"' not in html:
        viejo = """  <div class="hero__bg" aria-hidden="true">
    <span class="grid"></span>
    <span class="glow glow--a"></span>
    <span class="glow glow--b"></span>
  </div>"""
        nuevo = """  <div class="hero__bg" aria-hidden="true">
    <!-- El video lo enciende js/app.js: elige 16:9 o 3:4 según la pantalla y
         no lo descarga si el visitante pidió menos movimiento o ahorro de datos. -->
    <video class="hero__video" id="heroVideo"
           poster="statics/video/hero-poster-16x9.jpg"
           data-src-ancho="statics/video/hero-16x9.mp4"
           data-src-alto="statics/video/hero-3x4.mp4"
           muted loop playsinline preload="none" disablepictureinpicture></video>
    <span class="hero__veil"></span>
    <span class="grid"></span>
    <span class="glow glow--a"></span>
    <span class="glow glow--b"></span>
  </div>"""
        assert viejo in html, "no encontre el fondo del hero"
        html = html.replace(viejo, nuevo, 1)

    # ---------- 2. Galería de reels dentro de Trabajos ----------
    if 'class="clips"' not in html:
        ancla = ('<p class="sec__lead" data-reveal>Publicamos cada proyecto en Instagram: '
                 'antes y después, procesos y detalles de instalación.</p>\n    </header>')
        assert ancla in html, "no encontre el encabezado de Trabajos"
        html = html.replace(
            ancla,
            '<p class="sec__lead" data-reveal>Estos son trabajos reales que salieron del taller. '
            'Dale play a cualquiera y míralo completo, con audio.</p>\n    </header>\n'
            + SECCION_CLIPS.replace("@@CLIPS@@", bloque_clips()), 1)

    # ---------- 3. Testimonio ----------
    if 'id="testimonio"' not in html:
        ancla = "\n<!-- ============ NOSOTROS ============ -->"
        assert ancla in html, "no encontre la seccion Nosotros"
        html = html.replace(ancla, SECCION_TESTIMONIO + ancla, 1)

        # renumerar las etiquetas de las secciones que siguen
        for viejo, nuevo in [("05 &mdash; Nosotros", "06 &mdash; Nosotros"),
                             ("06 &mdash; Cobertura", "07 &mdash; Cobertura"),
                             ("07 &mdash; Preguntas", "08 &mdash; Preguntas"),
                             ("08 &mdash; Contacto", "09 &mdash; Contacto")]:
            html = html.replace(viejo, nuevo, 1)

    # ---------- 4. Enlace en la navegación ----------
    if 'href="#testimonio"' not in html:
        html = html.replace('      <a href="#trabajos">Trabajos</a>',
                            '      <a href="#trabajos">Trabajos</a>\n'
                            '      <a href="#testimonio">Testimonio</a>', 1)

    # ---------- 5. Precarga del poster del hero ----------
    if 'as="image"' not in html:
        html = html.replace(
            '<link rel="stylesheet" href="css/style.css">',
            '<link rel="preload" as="image" href="statics/video/hero-poster-16x9.jpg" '
            'media="(min-width: 861px)">\n'
            '<link rel="preload" as="image" href="statics/video/hero-poster-3x4.jpg" '
            'media="(max-width: 860px)">\n'
            '<link rel="stylesheet" href="css/style.css">', 1)

    io.open(IDX, "w", encoding="utf-8", newline="\n").write(html)
    print("index.html: hero en video + %d reels + testimonio" % len(CLIPS))


if __name__ == "__main__":
    main()
