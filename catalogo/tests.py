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
        ImagenProducto.objects.create(producto=self.producto, imagen="p/barra.webp")
        html = self.client.get(self.producto.get_absolute_url()).content.decode()
        self.assertIn('"@type": "Product"', html)
        self.assertIn('"priceCurrency": "COP"', html)
        self.assertIn("schema.org/InStock", html)

    def test_sin_foto_no_hay_product_en_el_json_ld(self):
        # Google exige image en el Product: sin foto, cada ficha saldría como
        # error en Search Console. La página se indexa igual; el resultado
        # enriquecido espera a la foto.
        html = self.client.get(self.producto.get_absolute_url()).content.decode()
        self.assertNotIn('"@type": "Product"', html)
        self.assertIn('"@type": "BreadcrumbList"', html)

    def test_un_agotado_se_marca_como_tal_en_el_json_ld(self):
        ImagenProducto.objects.create(producto=self.producto, imagen="p/barra.webp")
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

    def test_una_categoria_vacia_no_va_al_sitemap(self):
        # Una página sin productos es contenido pobre para Google (soft 404):
        # no se le invita con el sitemap ni se deja indexar hasta que tenga
        # su primer producto.
        vacia = Categoria.objects.create(nombre="Polarizados")
        xml = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(self.categoria.get_absolute_url(), xml)
        self.assertNotIn(vacia.get_absolute_url(), xml)

    def test_una_categoria_vacia_no_se_indexa(self):
        vacia = Categoria.objects.create(nombre="Polarizados")
        r = self.client.get(vacia.get_absolute_url())
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.context["robots"], "noindex, follow")
        # Con productos, la misma página vuelve a indexarse sola.
        con_algo = self.client.get(self.categoria.get_absolute_url())
        self.assertEqual(
            con_algo.context["robots"],
            "index, follow, max-snippet:-1, max-image-preview:large",
        )

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


class FeedGoogle(Base):
    """El feed de Google Merchant Center: /feed-productos.xml."""

    def setUp(self):
        super().setUp()
        ImagenProducto.objects.create(producto=self.producto, imagen="p/barra.webp")

    def feed(self):
        r = self.client.get("/feed-productos.xml")
        self.assertEqual(r.status_code, 200)
        return r.content.decode()

    def test_el_producto_con_precio_y_foto_sale_en_el_feed(self):
        xml = self.feed()
        self.assertIn("<g:id>" + self.variante.sku + "</g:id>", xml)
        self.assertIn("<g:price>480000 COP</g:price>", xml)
        self.assertIn("in_stock", xml)
        self.assertIn(self.producto.get_absolute_url(), xml)
        # Que parsee: un feed roto es un feed que Google rechaza entero.
        import xml.etree.ElementTree as ET
        ET.fromstring(xml)

    def test_sin_foto_no_entra(self):
        # Google exige imagen por producto: sin foto el item invalidaría el
        # feed. Queda afuera y entra solo cuando le carguen una.
        ImagenProducto.objects.all().delete()
        self.assertNotIn(self.variante.sku, self.feed())

    def test_a_cotizar_no_entra(self):
        snorkel = Producto.objects.create(nombre="Snorkel Safari", categoria=self.categoria)
        ImagenProducto.objects.create(producto=snorkel, imagen="p/snorkel.webp")
        self.assertNotIn("Snorkel Safari", self.feed())

    def test_agotado_sale_como_out_of_stock(self):
        self.variante.stock = 0
        self.variante.save()
        self.assertIn("out_of_stock", self.feed())

    def test_la_rebaja_sale_como_sale_price(self):
        self.variante.precio_antes = 600000
        self.variante.save()
        xml = self.feed()
        self.assertIn("<g:price>600000 COP</g:price>", xml)
        self.assertIn("<g:sale_price>480000 COP</g:sale_price>", xml)


class InventarioMasivo(TestCase):
    """El comando que carga el inventario del comercio (semillas/inventario.json)."""

    def setUp(self):
        self.datos = json.loads((SEMILLAS / "inventario.json").read_text(encoding="utf-8"))

    def cargar(self, *args):
        call_command("inventario_masivo", *args, stdout=io.StringIO())

    def test_la_semilla_esta_sana(self):
        productos = self.datos["productos"]
        slugs = [p["slug"] for p in productos]
        self.assertEqual(len(slugs), len(set(slugs)))
        skus = [p["variante"]["sku"] for p in productos if p.get("variante")]
        self.assertEqual(len(skus), len(set(skus)))
        for p in productos:
            self.assertLessEqual(len(p["seo_titulo"]), 70, p["slug"])
            self.assertLessEqual(len(p["seo_descripcion"]), 160, p["slug"])
            if p.get("variante"):
                self.assertGreater(p["variante"]["precio"], 0, p["slug"])
                # El costo de compra no puede estar acá: el repo es público.
                self.assertNotIn("costo", p["variante"], p["slug"])

    def test_carga_los_productos_con_sus_variantes(self):
        self.cargar()
        productos = self.datos["productos"]
        self.assertEqual(Producto.objects.count(), len(productos))
        con_precio = [p for p in productos if p.get("variante")]
        self.assertEqual(Variante.objects.count(), len(con_precio))
        # Los que tienen precio se venden con carrito; el resto, a cotizar.
        self.assertEqual(
            Producto.objects.publicados().count(), len(productos)
        )

    def test_correrlo_dos_veces_no_duplica(self):
        self.cargar()
        antes = (Producto.objects.count(), Variante.objects.count())
        self.cargar()
        self.assertEqual(antes, (Producto.objects.count(), Variante.objects.count()))

    def test_si_falta_no_toca_una_base_ya_sembrada(self):
        self.cargar()
        Producto.objects.first().delete()
        antes = Producto.objects.count()
        self.cargar("--si-falta")
        # El producto borrado a propósito no reaparece.
        self.assertEqual(Producto.objects.count(), antes)


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


class Ganancia(Base):
    """El costo es opcional, así que hay que distinguir «vacío» de «cero»."""

    def test_sin_costo_no_se_inventa_una_ganancia(self):
        self.assertIsNone(self.variante.costo)
        self.assertIsNone(self.variante.ganancia)
        self.assertIsNone(self.variante.margen)

    def test_con_costo_calcula_ganancia_y_margen(self):
        self.variante.costo = 300000
        self.variante.save()
        self.assertEqual(self.variante.ganancia, 180000)
        self.assertEqual(self.variante.margen, 38)  # 180000 / 480000

    def test_un_costo_de_cero_no_es_lo_mismo_que_no_tenerlo(self):
        self.variante.costo = 0
        self.variante.save()
        self.assertEqual(self.variante.ganancia, 480000)
        self.assertEqual(self.variante.margen, 100)


class AltaDeProducto(Base):
    """El formulario de alta: pocos campos, y la ficha completa al editar."""

    def setUp(self):
        super().setUp()
        from django.contrib.auth import get_user_model

        User = get_user_model()
        self.jefa = User.objects.create_superuser("jefa", "jefa@dacars.co", "clave-larga-123")
        self.client.force_login(self.jefa)

    def test_el_alta_pide_lo_minimo_y_la_ficha_completa_aparece_al_editar(self):
        alta = self.client.get(reverse("admin:catalogo_producto_add")).content.decode()
        # Lo que no se pregunta todavía.
        for campo in ("seo_titulo", "compatibilidad", "caracteristicas"):
            self.assertNotIn('name="{}"'.format(campo), alta, campo)
        # Lo que sí.
        for campo in ("nombre", "categoria", "resumen"):
            self.assertIn('name="{}"'.format(campo), alta, campo)
        # Y el costo, en la primera fila de precios ya abierta.
        self.assertIn("variantes-0-costo", alta)

        ficha = self.client.get(
            reverse("admin:catalogo_producto_change", args=[self.producto.pk])
        ).content.decode()
        for campo in ("seo_titulo", "compatibilidad", "caracteristicas", "slug"):
            self.assertIn('name="{}"'.format(campo), ficha, campo)

    def test_crear_un_producto_deja_su_precio_y_su_costo(self):
        respuesta = self.client.post(
            reverse("admin:catalogo_producto_add"),
            {
                "nombre": "Exploradora LED 7 pulgadas",
                "categoria": self.categoria.pk,
                "marca": "",
                "resumen": "Redonda, para bumper.",
                "variantes-TOTAL_FORMS": "1",
                "variantes-INITIAL_FORMS": "0",
                "variantes-MIN_NUM_FORMS": "0",
                "variantes-MAX_NUM_FORMS": "1000",
                "variantes-0-nombre": "",
                "variantes-0-costo": "120000",
                "variantes-0-precio": "195000",
                "variantes-0-stock": "4",
                "variantes-0-stock_minimo": "1",
                "imagenes-TOTAL_FORMS": "0",
                "imagenes-INITIAL_FORMS": "0",
                "imagenes-MIN_NUM_FORMS": "0",
                "imagenes-MAX_NUM_FORMS": "1000",
            },
        )
        nuevo = Producto.objects.get(nombre="Exploradora LED 7 pulgadas")
        # Se queda en la ficha, que es donde está lo que falta completar.
        self.assertRedirects(
            respuesta,
            reverse("admin:catalogo_producto_change", args=[nuevo.pk]),
        )
        self.assertTrue(nuevo.slug, "el slug se arma solo aunque no se muestre")

        variante = nuevo.variantes.get()
        self.assertEqual(variante.costo, 120000)
        self.assertEqual(variante.precio, 195000)
        self.assertEqual(variante.ganancia, 75000)
        # El stock inicial entró por inventario, no escrito a mano.
        self.assertEqual(variante.stock, 4)
        self.assertEqual(variante.movimientos.count(), 1)

    def test_la_categoria_se_puede_crear_desde_el_alta(self):
        # Es el «+ Nueva» que está al lado del selector: una ventana emergente
        # sobre el formulario de categorías.
        emergente = self.client.get(reverse("admin:catalogo_categoria_add") + "?_popup=1")
        self.assertEqual(emergente.status_code, 200)
        html = emergente.content.decode()
        self.assertIn('name="nombre"', html)
        self.assertNotIn('name="servicio"', html)  # eso se ajusta después

        self.client.post(
            reverse("admin:catalogo_categoria_add") + "?_popup=1",
            {"nombre": "Cámaras y sensores", "descripcion": "", "_popup": "1"},
        )
        creada = Categoria.objects.get(nombre="Cámaras y sensores")
        self.assertEqual(creada.slug, "camaras-y-sensores")
