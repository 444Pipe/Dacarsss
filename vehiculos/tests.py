"""Carros en venta: qué se ve, qué no, y que la carga inicial no pise al panel."""

import tempfile
from io import StringIO

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from vehiculos.models import Vehiculo


def _carro(**datos):
    base = {"marca": "Toyota", "modelo": "Prado", "version": "TX.L", "anio": 2017}
    base.update(datos)
    return Vehiculo.objects.create(**base)


class ModeloTests(TestCase):
    def test_el_nombre_y_el_slug_se_arman_solos(self):
        carro = _carro()
        self.assertEqual(carro.nombre, "Toyota Prado TX.L 2017")
        self.assertEqual(carro.slug, "toyota-prado-txl-2017")

    def test_dos_carros_iguales_no_chocan_de_slug(self):
        uno, dos = _carro(), _carro()
        self.assertNotEqual(uno.slug, dos.slug)

    def test_los_datos_vacios_no_salen_en_la_ficha(self):
        carro = _carro(anio=None, kilometraje=170377, transmision="automatica")
        self.assertEqual(
            carro.datos, [("Kilometraje", "170.377 km"), ("Transmisión", "Automática")]
        )


class PaginasTests(TestCase):
    def test_la_lista_muestra_los_publicados_y_esconde_el_resto(self):
        _carro()
        _carro(marca="Nissan", modelo="Frontier", version="", anio=None, publicado=False)
        respuesta = self.client.get(reverse("vehiculos:lista"))
        self.assertContains(respuesta, "Toyota Prado TX.L 2017")
        self.assertNotContains(respuesta, "Nissan Frontier")

    def test_la_lista_vacia_no_se_le_ofrece_a_google(self):
        respuesta = self.client.get(reverse("vehiculos:lista"))
        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "noindex")

    def test_sin_precio_la_ficha_dice_consultar(self):
        carro = _carro()
        respuesta = self.client.get(carro.get_absolute_url())
        self.assertContains(respuesta, "Consultar precio")
        self.assertContains(respuesta, "wa.me/")

    def test_con_precio_la_ficha_lo_muestra_en_pesos(self):
        carro = _carro(precio=185000000)
        self.assertContains(self.client.get(carro.get_absolute_url()), "$185.000.000")

    def test_un_carro_vendido_no_ofrece_whatsapp(self):
        carro = _carro(estado=Vehiculo.VENDIDO)
        respuesta = self.client.get(carro.get_absolute_url())
        self.assertContains(respuesta, "Este carro ya se vendió")
        self.assertNotContains(respuesta, "Preguntar por este carro")

    def test_un_carro_despublicado_da_404(self):
        carro = _carro(publicado=False)
        self.assertEqual(self.client.get(carro.get_absolute_url()).status_code, 404)

    def test_el_menu_y_la_portada_solo_lo_anuncian_si_hay_carros(self):
        self.assertNotContains(self.client.get("/"), "Carros en venta")
        _carro()
        portada = self.client.get("/")
        self.assertContains(portada, 'id="carros-en-venta"')
        self.assertContains(portada, reverse("vehiculos:lista"))

    def test_el_sitemap_incluye_la_ficha(self):
        carro = _carro()
        self.assertContains(self.client.get("/sitemap.xml"), carro.get_absolute_url())


class CargaInicialTests(TestCase):
    def test_crea_los_carros_una_vez_y_no_pisa_lo_editado(self):
        with tempfile.TemporaryDirectory() as media, override_settings(MEDIA_ROOT=media):
            call_command("vehiculos_iniciales", stdout=StringIO())
            total = Vehiculo.objects.count()
            self.assertGreaterEqual(total, 2)
            frontier = Vehiculo.objects.get(slug="nissan-frontier-le-4x4")
            self.assertEqual(frontier.kilometraje, 170377)
            self.assertGreater(frontier.fotos.count(), 5)

            frontier.precio = 150000000
            frontier.save()
            call_command("vehiculos_iniciales", stdout=StringIO())
            self.assertEqual(Vehiculo.objects.count(), total)
            frontier.refresh_from_db()
            self.assertEqual(frontier.precio, 150000000)
