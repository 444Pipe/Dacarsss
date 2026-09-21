"""El catálogo público."""

from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Marca, Producto, Variante


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

    def test_un_producto_sin_variantes_no_se_publica(self):
        # No tiene precio: publicarlo solo consigue que pregunten por algo que
        # no se les puede vender.
        huerfano = Producto.objects.create(nombre="Snorkel sin cargar", categoria=self.categoria)
        r = self.client.get(reverse("catalogo:lista"))
        self.assertNotContains(r, "Snorkel sin cargar")
        self.assertNotIn(huerfano, r.context["pagina"].object_list)

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
