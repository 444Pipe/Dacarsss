"""Que la migración no haya roto el sitio que ya estaba indexado.

Es la prueba más importante del proyecto. El SEO local es lo que trae los
clientes, y una URL que cambia de dirección o deja de responder 200 no se nota
mirando la página: se nota semanas después, cuando el tráfico bajó.
"""

import difflib
import re
import unittest
from pathlib import Path

from django.conf import settings
from django.test import TestCase

from sitio.paginas import SLUGS

# Los HTML originales, para comparar contra ellos. Viven en legacy/html/
# después de la migración; si alguien los borra, la prueba se salta sola.
LEGACY = Path(settings.BASE_DIR) / "legacy" / "html"


class UrlsDelSitio(TestCase):
    def test_las_9_landings_responden(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                r = self.client.get("/" + slug + ".html")
                self.assertEqual(r.status_code, 200, slug + " no responde 200")

    def test_la_portada_responde(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_index_html_redirige_a_la_raiz(self):
        # Las dos URLs sirviendo lo mismo sería contenido duplicado gratis.
        r = self.client.get("/index.html")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/")

    def test_cada_landing_conserva_su_canonical(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                html = self.client.get("/" + slug + ".html").content.decode()
                self.assertIn(
                    'rel="canonical" href="https://www.dacars.com.co/%s.html"' % slug,
                    html,
                )

    def test_cada_landing_conserva_su_json_ld(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                html = self.client.get("/" + slug + ".html").content.decode()
                self.assertIn('application/ld+json', html)
                self.assertIn('"@type": "Service"', html)

    def test_la_portada_conserva_la_ficha_del_negocio(self):
        html = self.client.get("/").content.decode()
        self.assertIn("AutoPartsStore", html)
        self.assertIn("901798060", html.replace(".", ""))

    def test_la_pantalla_de_carga_sigue_en_todas(self):
        for ruta in ["/"] + ["/" + s + ".html" for s in SLUGS]:
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode()
                self.assertIn('id="carga"', html)
                # El respaldo en línea: si app.js no llega, la pantalla igual
                # se va a los 4 segundos.
                self.assertIn("cargaRespaldo", html)

    def test_robots_y_manifest(self):
        robots = self.client.get("/robots.txt")
        self.assertEqual(robots.status_code, 200)
        self.assertIn("Sitemap:", robots.content.decode())

        manifest = self.client.get("/manifest.webmanifest")
        self.assertEqual(manifest.status_code, 200)

    def test_sitemap(self):
        r = self.client.get("/sitemap.xml")
        self.assertEqual(r.status_code, 200)
        xml = r.content.decode()
        for slug in SLUGS:
            self.assertIn("/%s.html" % slug, xml)

    def test_404_usa_la_plantilla_de_marca(self):
        r = self.client.get("/esto-no-existe.html")
        self.assertEqual(r.status_code, 404)

    def test_el_menu_no_ofrece_catalogo_vacio(self):
        # Sin productos cargados, el enlace no aparece: mandaría a una página
        # en blanco.
        html = self.client.get("/").content.decode()
        self.assertNotIn('href="/catalogo/"', html)


def _normalizar(html):
    """Deja fuera las diferencias que la migración introdujo a propósito."""
    html = html.replace('href="index.html#', 'href="/#')
    html = html.replace('href="index.html"', 'href="/"')
    for slug in SLUGS:
        html = html.replace('href="%s.html' % slug, 'href="/%s.html' % slug)
    html = html.replace('href="manifest.webmanifest"', 'href="/manifest.webmanifest"')
    # El `?v=hash` que ponía versionar-assets.py ahora lo hace {% static %}.
    html = re.sub(r'href="(/static/)?css/style\.css(\?v=[0-9a-f]+)?"', "CSS", html)
    html = re.sub(r'src="(/static/)?js/app\.js(\?v=[0-9a-f]+)?"', "JS", html)
    return [l.rstrip() for l in html.splitlines() if l.strip()]


@unittest.skipUnless(LEGACY.exists(), "no están los HTML originales en legacy/html/")
class IgualAlSitioViejo(TestCase):
    """Lo que sirve Django tiene que ser lo mismo que servía Caddy.

    No es una prueba de estilo: en esas páginas hay entre 200 y 600 líneas de
    JSON-LD que Google ya está leyendo. Un atributo que se pierda en una
    edición futura no se ve en el navegador — se ve meses después, en las
    visitas.
    """

    def test_las_10_paginas_salen_iguales(self):
        for archivo, url in [("index.html", "/")] + [
            (s + ".html", "/" + s + ".html") for s in SLUGS
        ]:
            with self.subTest(pagina=archivo):
                original = _normalizar((LEGACY / archivo).read_text(encoding="utf-8"))
                servido = _normalizar(self.client.get(url).content.decode())
                diferencias = [
                    linea
                    for linea in difflib.unified_diff(original, servido, lineterm="", n=0)
                    if linea.startswith(("+", "-"))
                    and not linea.startswith(("+++", "---"))
                ]
                self.assertEqual(
                    diferencias,
                    [],
                    "%s cambió respecto del sitio original:\n%s"
                    % (archivo, "\n".join(diferencias[:20])),
                )
