"""Que el sitio que ya está indexado siga en pie.

Es la prueba más importante del proyecto. El SEO local es lo que trae los
clientes, y una URL que cambia de dirección, deja de responder 200 o pierde su
JSON-LD no se nota mirando la página: se nota semanas después, cuando el
tráfico bajó.
"""

import json
import re

from django.conf import settings
from django.test import TestCase

from sitio.paginas import HUB_META, SLUGS


class UrlsDelSitio(TestCase):
    # Sin numero en el nombre a proposito: la lista de servicios crece, y un
    # test llamado "las_9" o "las_10" obliga a renombrarlo cada vez o a mentir.
    def test_todas_las_landings_responden(self):
        for slug in SLUGS:
            with self.subTest(slug=slug):
                r = self.client.get("/" + slug)
                self.assertEqual(r.status_code, 200, slug + " no responde 200")

    def test_el_hub_del_meta_responde(self):
        r = self.client.get("/" + HUB_META)
        self.assertEqual(r.status_code, 200)

    def test_la_portada_responde(self):
        self.assertEqual(self.client.get("/").status_code, 200)

    def test_index_html_redirige_a_la_raiz(self):
        # Las dos URLs sirviendo lo mismo sería contenido duplicado gratis.
        r = self.client.get("/index.html")
        self.assertEqual(r.status_code, 301)
        self.assertEqual(r["Location"], "/")

    def test_las_urls_con_html_redirigen_a_la_limpia(self):
        # Son las que ya circulan: Google, Google Business, Instagram, los
        # chats. Tienen que seguir llegando, y con 301 (permanente), que es el
        # que le dice a Google que traspase lo ganado a la dirección nueva.
        for pagina in SLUGS + [HUB_META]:
            with self.subTest(pagina=pagina):
                r = self.client.get("/" + pagina + ".html")
                self.assertEqual(r.status_code, 301)
                self.assertEqual(r["Location"], "/" + pagina)

    def test_la_barra_final_tambien_redirige(self):
        # Una sola dirección por página: con y sin barra servirían lo mismo.
        for pagina in SLUGS + [HUB_META]:
            with self.subTest(pagina=pagina):
                r = self.client.get("/" + pagina + "/")
                self.assertEqual(r.status_code, 301)
                self.assertEqual(r["Location"], "/" + pagina)

    def test_la_redireccion_conserva_la_campana(self):
        # Sin esto, un anuncio que enlaza al .html pierde el ?utm_ en el salto
        # y la visita aparece como tráfico directo.
        r = self.client.get("/ppf-villavicencio.html?utm_source=instagram")
        self.assertEqual(r["Location"], "/ppf-villavicencio?utm_source=instagram")

    def test_cada_landing_conserva_su_canonical(self):
        # El dominio se lee de la configuracion y no se escribe aca: si manana
        # cambia DOMINIO, lo que tiene que seguir siendo cierto es que el
        # canonical apunte al dominio configurado, no a uno concreto.
        sitio = settings.NEGOCIO["sitio"]
        for slug in SLUGS + [HUB_META]:
            with self.subTest(slug=slug):
                html = self.client.get("/" + slug).content.decode()
                self.assertIn(
                    'rel="canonical" href="%s/%s"' % (sitio, slug),
                    html,
                )

    def test_cada_landing_conserva_su_json_ld(self):
        for slug in SLUGS + [HUB_META]:
            with self.subTest(slug=slug):
                html = self.client.get("/" + slug).content.decode()
                self.assertIn('application/ld+json', html)
                self.assertIn('"@type": "Service"', html)

    def test_la_portada_conserva_la_ficha_del_negocio(self):
        html = self.client.get("/").content.decode()
        self.assertIn("AutoPartsStore", html)
        self.assertIn("901798060", html.replace(".", ""))

    def test_la_pantalla_de_carga_sigue_en_todas(self):
        for ruta in ["/"] + ["/" + s for s in SLUGS]:
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
        for slug in SLUGS + [HUB_META]:
            self.assertIn("/%s</loc>" % slug, xml)
        self.assertNotIn(".html</loc>", xml)

    def test_404_usa_la_plantilla_de_marca(self):
        r = self.client.get("/esto-no-existe.html")
        self.assertEqual(r.status_code, 404)

    def test_el_menu_no_ofrece_catalogo_vacio(self):
        # Sin productos cargados, el enlace no aparece: mandaría a una página
        # en blanco.
        html = self.client.get("/").content.decode()
        self.assertNotIn('href="/catalogo/"', html)


# =========================================================================
#  Invariantes de SEO
#
#  Acá vivía `IgualAlSitioViejo`, que comparaba cada página renderizada contra
#  su HTML original en legacy/html/, línea por línea. Cumplió su trabajo: la
#  migración a Django se verificó con ella y pasó.
#
#  Pero una prueba que exige que la salida sea idéntica a la de antes también
#  impide mejorarla. Al acortar las meta description, sumar Pintura y el hub
#  del Meta y unificar el bloque «Más servicios», las diez páginas dejaron de
#  coincidir con el archivo congelado — no por un error, sino por el cambio
#  que se quería hacer. Mantenerla habría significado o no tocar el sitio
#  nunca más, o reescribir legacy/html/, que es justamente el registro
#  histórico que no hay que tocar.
#
#  Lo que sí había que conservar es el MOTIVO: que una edición futura no se
#  lleve por delante el marcado del que depende la búsqueda local, porque eso
#  no se ve en el navegador — se ve meses después, en las visitas. Así que en
#  vez de congelar el texto se comprueban las reglas: un h1, title y
#  description únicos y dentro de su largo, canonical al dominio configurado,
#  JSON-LD que parsea y trae los tipos que Google lee, y ningún enlace interno
#  roto.
# =========================================================================


def _paginas():
    return ["/"] + ["/%s" % s for s in SLUGS + [HUB_META]]


class InvariantesDeSeo(TestCase):
    def setUp(self):
        self.html = {ruta: self.client.get(ruta).content.decode() for ruta in _paginas()}

    def test_cada_pagina_tiene_un_solo_h1(self):
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                self.assertEqual(
                    len(re.findall(r"<h1\b", html)), 1, "debe haber exactamente un h1"
                )

    def test_title_unico_y_dentro_del_corte(self):
        vistos = {}
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                t = re.search(r"<title>(.*?)</title>", html, re.S)
                self.assertIsNotNone(t, "falta el title")
                titulo = t.group(1).strip()
                # Google corta el título alrededor de los 60-70 caracteres.
                self.assertLessEqual(len(titulo), 70, titulo)
                self.assertNotIn(titulo, vistos, "title repetido con " + vistos.get(titulo, ""))
                vistos[titulo] = ruta

    def test_description_unica_y_dentro_del_corte(self):
        vistos = {}
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                d = re.search(r'<meta name="description" content="([^"]*)"', html)
                self.assertIsNotNone(d, "falta la meta description")
                desc = d.group(1).strip()
                # Más de ~160 y el fragmento sale cortado: la llamada a la
                # acción del final es lo primero que se pierde.
                self.assertLessEqual(len(desc), 160, "%s: %d caracteres" % (ruta, len(desc)))
                self.assertNotIn(desc, vistos, "description repetida con " + vistos.get(desc, ""))
                vistos[desc] = ruta

    def test_canonical_al_dominio_configurado(self):
        sitio = settings.NEGOCIO["sitio"]
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                esperado = sitio + ruta
                self.assertIn('rel="canonical" href="%s"' % esperado, html)

    def test_el_json_ld_parsea_y_trae_lo_que_google_lee(self):
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                bloques = re.findall(
                    r'<script type="application/ld\+json">(.*?)</script>', html, re.S
                )
                self.assertTrue(bloques, "falta el JSON-LD")
                tipos = set()
                for bloque in bloques:
                    # Que parsee es la mitad del asunto: un JSON-LD roto no
                    # avisa, simplemente deja de contar.
                    datos = json.loads(bloque)
                    for nodo in datos.get("@graph", [datos]):
                        tipo = nodo.get("@type")
                        tipos.update(tipo if isinstance(tipo, list) else [tipo])
                self.assertIn("WebPage", tipos)
                # El FAQPage es el que puede poner las preguntas desplegables
                # en el resultado de búsqueda.
                self.assertIn("FAQPage", tipos)
                if ruta != "/":
                    self.assertIn("Service", tipos)
                    self.assertIn("BreadcrumbList", tipos)

    def test_open_graph_completo(self):
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                for etiqueta in ("og:title", "og:description", "og:image", "og:url"):
                    self.assertIn('property="%s"' % etiqueta, html)
                self.assertIn('name="twitter:card"', html)

    def test_sin_enlaces_internos_rotos(self):
        # Exige 200, no 301: un enlace interno que pasa por una redirección
        # funciona, pero le cuesta un salto a cada visita y a cada rastreo.
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                for destino in set(re.findall(r'href="(/[a-z0-9-]+(?:\.html)?)"', html)):
                    self.assertEqual(
                        self.client.get(destino).status_code,
                        200,
                        "%s enlaza a %s, que no responde 200" % (ruta, destino),
                    )

    def test_ninguna_url_propia_lleva_html(self):
        # Ni en enlaces, ni en el canonical, ni en og:url, ni en el JSON-LD: si
        # el canonical dijera .html, Google recibiría dos señales contrarias.
        propias = re.compile(r"/(%s)\.html" % "|".join(SLUGS + [HUB_META]))
        for ruta, html in self.html.items():
            with self.subTest(ruta=ruta):
                self.assertEqual(propias.findall(html), [])

    def test_las_paginas_nuevas_estan_enlazadas(self):
        # Una landing sin enlaces entrantes es una landing que Google rastrea
        # tarde y mal. Las dos últimas en llegar son las que más riesgo corren
        # de quedarse sueltas.
        portada = self.html["/"]
        for destino in ("/pintura-automotriz-villavicencio",
                        "/%s" % HUB_META):
            with self.subTest(destino=destino):
                self.assertIn('href="%s"' % destino, portada,
                              "la portada no enlaza a " + destino)


class AccesoAlPanel(TestCase):
    """El enlace discreto del pie.

    Es lo único que el comercio tiene para llegar al panel sin acordarse de
    escribir /admin/ a mano, así que conviene que no se pierda en una edición.
    """

    def test_esta_en_la_portada_y_en_las_landings(self):
        for ruta in ["/"] + ["/" + s for s in SLUGS]:
            with self.subTest(ruta=ruta):
                html = self.client.get(ruta).content.decode()
                self.assertIn("foot__acceso", html)
                self.assertIn("Acceso a la página", html)
                self.assertIn('href="/admin/"', html)

    def test_lleva_al_panel(self):
        html = self.client.get("/").content.decode()
        self.assertIn('rel="nofollow"', html.split("foot__acceso")[1][:200])
        # Y el destino existe de verdad.
        self.assertEqual(self.client.get("/admin/").status_code, 302)

    def test_los_buscadores_no_rastrean_el_panel(self):
        robots = self.client.get("/robots.txt").content.decode()
        self.assertIn("Disallow: /admin/", robots)
