"""El catálogo público."""

import io
import json
import shutil
import tempfile

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from catalogo.management.commands.catalogo_inicial import SEMILLAS
from catalogo.models import Categoria, ImagenProducto, Marca, Producto, Variante


class Base(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(
            nombre="Iluminación", servicio="iluminacion-para-carros-villavicencio"
        )
        self.marca = Marca.objects.create(nombre="Osram")
        self.producto = Producto.objects.create(
            nombre="Barra LED 22 pulgadas",
            categoria=self.categoria,
            marca=self.marca,
            resumen="Para la vía al Llano de noche.",
            descripcion="Primer párrafo.\n\nSegundo párrafo.",
            caracteristicas="120 W\nIP67\n6000 K",
            compatibilidad="Hilux, Ranger, Amarok",
        )
        self.variante = Variante.objects.create(
            producto=self.producto, precio=480000, stock=6, stock_minimo=2
        )


class QueSePublica(Base):
    def test_el_catalogo_lista_el_producto(self):
        r = self.client.get(reverse("catalogo:lista"))
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Barra LED 22 pulgadas")

    def test_un_producto_sin_variantes_sale_a_cotizar(self):
        # Sin precio se publica igual, con el botón de WhatsApp en vez del
        # carrito: así es como DACARS muestra hoy su catálogo.
        snorkel = Producto.objects.create(nombre="Snorkel Safari", categoria=self.categoria)
        self.assertTrue(snorkel.a_cotizar)
        r = self.client.get(reverse("catalogo:lista"))
        self.assertIn(snorkel, r.context["pagina"].object_list)
        self.assertContains(r, "Cotizar Snorkel Safari por WhatsApp")

    def test_la_ficha_a_cotizar_no_ofrece_carrito(self):
        snorkel = Producto.objects.create(nombre="Snorkel Safari", categoria=self.categoria)
        html = self.client.get(snorkel.get_absolute_url()).content.decode()
        self.assertIn("Cotizar por WhatsApp", html)
        self.assertNotIn('id="form-compra"', html)
        # El mensaje lleva el nombre y el enlace de la ficha.
        self.assertIn("quiero%20cotizar%3A%20Snorkel%20Safari", html)
        self.assertIn("producto/snorkel-safari/", html)

    def test_la_ficha_a_cotizar_no_publica_un_product_sin_precio(self):
        # Google exige offers con precio en un Product: sin él, Search Console
        # marca error en cada ficha. Las migas sí salen.
        snorkel = Producto.objects.create(nombre="Snorkel Safari", categoria=self.categoria)
        html = self.client.get(snorkel.get_absolute_url()).content.decode()
        self.assertNotIn('"@type": "Product"', html)
        self.assertIn('"@type": "BreadcrumbList"', html)

    def test_a_cotizar_no_es_agotado(self):
        snorkel = Producto.objects.create(nombre="Snorkel Safari", categoria=self.categoria)
        self.assertFalse(snorkel.agotado)

    def test_con_precio_deja_de_estar_a_cotizar(self):
        snorkel = Producto.objects.create(nombre="Snorkel Safari", categoria=self.categoria)
        Variante.objects.create(producto=snorkel, precio=950000, stock=1)
        self.assertFalse(Producto.objects.get(pk=snorkel.pk).a_cotizar)

    def test_un_producto_desactivado_no_se_publica(self):
        self.producto.activo = False
        self.producto.save()
        self.assertNotContains(self.client.get(reverse("catalogo:lista")), "Barra LED")

    def test_una_categoria_desactivada_esconde_sus_productos(self):
        self.categoria.activa = False
        self.categoria.save()
        self.assertNotContains(self.client.get(reverse("catalogo:lista")), "Barra LED")

    def test_la_ficha_del_producto_abre(self):
        r = self.client.get(self.producto.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertContains(r, "Barra LED 22 pulgadas")
        self.assertContains(r, "Hilux, Ranger, Amarok")
        self.assertContains(r, "IP67")

    def test_la_ficha_lleva_su_json_ld_de_producto(self):
        html = self.client.get(self.producto.get_absolute_url()).content.decode()
        self.assertIn('"@type": "Product"', html)
        self.assertIn('"priceCurrency": "COP"', html)
        self.assertIn("schema.org/InStock", html)

    def test_un_agotado_se_marca_como_tal_en_el_json_ld(self):
        self.variante.stock = 0
        self.variante.save()
        html = self.client.get(self.producto.get_absolute_url()).content.decode()
        self.assertIn("schema.org/OutOfStock", html)


class Filtros(Base):
    def setUp(self):
        super().setUp()
        self.otra = Categoria.objects.create(nombre="Llantas y rines")
        self.llanta = Producto.objects.create(nombre="Llanta Grabber AT", categoria=self.otra)
        Variante.objects.create(producto=self.llanta, nombre="265/65R17", precio=850000, stock=0)

    def test_filtrar_por_categoria(self):
        r = self.client.get(self.otra.get_absolute_url())
        self.assertContains(r, "Llanta Grabber")
        self.assertNotContains(r, "Barra LED")

    def test_buscar_por_medida(self):
        r = self.client.get(reverse("catalogo:lista"), {"q": "265/65R17"})
        self.assertContains(r, "Llanta Grabber")
        self.assertNotContains(r, "Barra LED")

    def test_solo_lo_que_hay_esconde_los_agotados(self):
        r = self.client.get(reverse("catalogo:lista"), {"hay": "1"})
        self.assertContains(r, "Barra LED")
        self.assertNotContains(r, "Llanta Grabber")

    def test_los_filtros_no_se_indexan(self):
        # Los mismos productos recortados de otra forma son contenido
        # duplicado para Google.
        limpio = self.client.get(reverse("catalogo:lista"))
        self.assertEqual(limpio.context["robots"], "index, follow, max-snippet:-1, max-image-preview:large")

        filtrado = self.client.get(reverse("catalogo:lista"), {"q": "led"})
        self.assertEqual(filtrado.context["robots"], "noindex, follow")
        self.assertEqual(filtrado.context["canonical"], "/catalogo/")


class Categorias(Base):
    def test_el_selector_no_ofrece_categorias_vacias(self):
        Categoria.objects.create(nombre="Polarizados")
        r = self.client.get(reverse("catalogo:lista"))
        nombres = [c.nombre for c in r.context["categorias"]]
        self.assertIn("Iluminación", nombres)
        self.assertNotIn("Polarizados", nombres)

    def test_la_entrada_muestra_las_categorias_en_grande(self):
        otra = Categoria.objects.create(nombre="Pitos y alarmas")
        Producto.objects.create(nombre="Pito caracol", categoria=otra)
        r = self.client.get(reverse("catalogo:lista"))
        self.assertEqual(len(r.context["portadas"]), 2)
        # Con un filtro puesto, lo que se busca son productos.
        r = self.client.get(reverse("catalogo:lista"), {"q": "pito"})
        self.assertEqual(r.context["portadas"], [])


class Fotos(Base):
    def test_la_tarjeta_muestra_la_foto_instalada_al_pasar(self):
        ImagenProducto.objects.create(producto=self.producto, imagen="p/barra.webp", orden=0)
        ImagenProducto.objects.create(
            producto=self.producto, imagen="p/barra-en-hilux.webp", orden=1,
            tipo=ImagenProducto.INSTALADO, referencia=True,
        )
        html = self.client.get(reverse("catalogo:lista")).content.decode()
        self.assertIn("prod--doble", html)
        self.assertIn("barra-en-hilux.webp", html)

    def test_la_imagen_de_referencia_se_etiqueta_en_la_ficha(self):
        ImagenProducto.objects.create(
            producto=self.producto, imagen="p/barra-en-hilux.webp", orden=0,
            tipo=ImagenProducto.INSTALADO, referencia=True,
        )
        html = self.client.get(self.producto.get_absolute_url()).content.decode()
        self.assertIn("Imagen de referencia", html)
        self.assertNotIn('id="foto-nota" hidden', html)


class Precios(Base):
    def test_producto_de_una_sola_variante(self):
        self.assertFalse(self.producto.rango_de_precios)
        self.assertEqual(self.producto.precio_desde, 480000)

    def test_producto_con_varias_medidas_muestra_rango(self):
        Variante.objects.create(producto=self.producto, nombre="32 pulgadas", precio=690000, stock=2)
        self.producto.refresh_from_db()
        self.assertTrue(self.producto.rango_de_precios)
        self.assertEqual(self.producto.precio_desde, 480000)
        self.assertEqual(self.producto.precio_hasta, 690000)

    def test_el_sku_se_genera_solo_y_no_se_repite(self):
        otra = Variante.objects.create(producto=self.producto, nombre="32 pulgadas", precio=690000)
        self.assertTrue(self.variante.sku)
        self.assertNotEqual(self.variante.sku, otra.sku)

    def test_el_descuento_sale_del_precio_anterior(self):
        self.variante.precio_antes = 600000
        self.variante.precio = 480000
        self.variante.save()
        self.assertEqual(self.variante.descuento, 20)


class EnlaceConElSitio(Base):
    def test_la_landing_muestra_los_productos_de_su_categoria(self):
        r = self.client.get("/iluminacion-para-carros-villavicencio")
        self.assertEqual(r.status_code, 200)
        self.assertIn(self.producto, r.context["productos_del_servicio"])

    def test_con_productos_cargados_aparece_el_catalogo_en_el_menu(self):
        html = self.client.get("/").content.decode()
        self.assertIn('href="/catalogo/"', html)

    def test_el_sitemap_suma_los_productos(self):
        xml = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(self.producto.get_absolute_url(), xml)
        self.assertIn(self.categoria.get_absolute_url(), xml)


class CatalogoInicial(TestCase):
    """El comando que carga los productos fotografiados en el local."""

    def setUp(self):
        media = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, media, ignore_errors=True)
        ajuste = self.settings(
            MEDIA_ROOT=media,
            STORAGES={
                "default": {
                    "BACKEND": "django.core.files.storage.FileSystemStorage",
                    "OPTIONS": {"location": media},
                },
                "staticfiles": {
                    "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
                },
            },
        )
        ajuste.enable()
        self.addCleanup(ajuste.disable)
        self.datos = json.loads((SEMILLAS / "catalogo.json").read_text(encoding="utf-8"))

    def cargar(self, *args):
        call_command("catalogo_inicial", *args, stdout=io.StringIO())

    def test_las_semillas_estan_completas(self):
        categorias = {c["nombre"] for c in self.datos["categorias"]}
        slugs = [p["slug"] for p in self.datos["productos"]]
        self.assertEqual(len(slugs), len(set(slugs)))
        for p in self.datos["productos"]:
            self.assertIn(p["categoria"], categorias, p["slug"])
            self.assertLessEqual(len(p["seo_titulo"]), 70, p["slug"])
            self.assertTrue(p["fotos"], p["slug"])
            for f in p["fotos"]:
                self.assertTrue((SEMILLAS / "fotos" / f["archivo"]).exists(), f["archivo"])

    def test_carga_los_productos_con_sus_fotos(self):
        self.cargar()
        productos = self.datos["productos"]
        self.assertEqual(Producto.objects.count(), len(productos))
        self.assertEqual(ImagenProducto.objects.count(), sum(len(p["fotos"]) for p in productos))
        # Entran todos publicados y a cotizar.
        self.assertEqual(Producto.objects.publicados().count(), len(productos))
        self.assertTrue(all(p.a_cotizar for p in Producto.objects.all()))

    def test_correrlo_dos_veces_no_duplica(self):
        self.cargar()
        antes = (Producto.objects.count(), ImagenProducto.objects.count(), Categoria.objects.count())
        self.cargar()
        despues = (Producto.objects.count(), ImagenProducto.objects.count(), Categoria.objects.count())
        self.assertEqual(antes, despues)

    def test_en_el_arranque_no_toca_un_catalogo_con_productos(self):
        # Así un producto borrado a propósito no reaparece en el siguiente
        # despliegue.
        cat = Categoria.objects.create(nombre="Iluminación")
        Producto.objects.create(nombre="Barra LED", categoria=cat)
        self.cargar("--si-vacio")
        self.assertEqual(Producto.objects.count(), 1)
