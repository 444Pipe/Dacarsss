"""El historial de inventario.

La regla que se prueba acá: **las existencias no cambian sin dejar rastro**.
Incluye el atajo que más se va a usar — escribir el número a mano en el panel —
porque es justo el que podría haber quedado por fuera del registro.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Producto, Variante
from inventario import servicios
from inventario.models import Movimiento


class Base(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Iluminación")
        self.producto = Producto.objects.create(nombre="Barra LED 22 pulgadas", categoria=self.categoria)
        self.variante = Variante.objects.create(
            producto=self.producto, precio=480000, stock=10, stock_minimo=3
        )
        self.jefe = User.objects.create_superuser("jefe", "jefe@dacars.co", "clave-larga-123")


class Movimientos(Base):
    def test_entrada_suma_y_anota(self):
        servicios.entrada(self.variante, 5, motivo="Llegó pedido al proveedor", usuario=self.jefe)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 15)

        m = Movimiento.objects.get()
        self.assertEqual(m.tipo, Movimiento.ENTRADA)
        self.assertEqual((m.stock_antes, m.stock_despues), (10, 15))
        self.assertEqual(m.delta, 5)
        self.assertEqual(m.usuario, self.jefe)

    def test_salida_resta(self):
        servicios.salida(self.variante, 3, motivo="Se dañó al instalar", usuario=self.jefe)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 7)
        self.assertEqual(Movimiento.objects.get().delta, -3)

    def test_no_se_puede_sacar_mas_de_lo_que_hay(self):
        with self.assertRaises(servicios.SinStock):
            servicios.salida(self.variante, 99)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 10)

    def test_ajuste_por_conteo(self):
        servicios.ajustar(self.variante, 8, motivo="Conteo del 30/09", usuario=self.jefe)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 8)

        m = Movimiento.objects.get()
        self.assertEqual(m.tipo, Movimiento.AJUSTE)
        self.assertEqual(m.delta, -2)

    def test_ajuste_sin_diferencia_no_ensucia_el_historial(self):
        self.assertIsNone(servicios.ajustar(self.variante, 10))
        self.assertEqual(Movimiento.objects.count(), 0)


class Alertas(Base):
    def test_una_variante_bajo_el_minimo_aparece_en_la_lista(self):
        self.assertEqual(Variante.bajo_minimo(), [])

        servicios.salida(self.variante, 8)  # quedan 2, el mínimo es 3
        bajas = Variante.bajo_minimo()
        self.assertEqual(len(bajas), 1)
        self.assertEqual(bajas[0].pk, self.variante.pk)

    def test_lo_reservado_cuenta_para_la_alerta(self):
        # Quedan 10 físicas, pero 8 ya están comprometidas: para vender hay 2.
        servicios.reservar(self.variante, 8)
        self.assertEqual(len(Variante.bajo_minimo()), 1)

    def test_una_variante_despublicada_no_alerta(self):
        servicios.salida(self.variante, 9)
        self.variante.activa = False
        self.variante.save()
        self.assertEqual(Variante.bajo_minimo(), [])


class ElPanelNoRompeElHistorial(Base):
    """El comercio va a escribir las existencias a mano. Tiene que quedar anotado."""

    def setUp(self):
        super().setUp()
        self.client.force_login(self.jefe)

    def test_editar_las_existencias_desde_el_panel_deja_un_ajuste(self):
        url = reverse("admin:catalogo_variante_change", args=[self.variante.pk])
        datos = {
            "producto": self.producto.pk,
            "nombre": "",
            "sku": self.variante.sku,
            "activa": "on",
            "orden": 0,
            "precio": 480000,
            "precio_antes": "",
            "stock": 25,
            "stock_minimo": 3,
        }
        respuesta = self.client.post(url, datos)
        self.assertEqual(respuesta.status_code, 302)

        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 25)

        m = Movimiento.objects.get()
        self.assertEqual(m.tipo, Movimiento.AJUSTE)
        self.assertEqual((m.stock_antes, m.stock_despues), (10, 25))
        self.assertEqual(m.usuario, self.jefe)

    def test_editar_solo_el_precio_no_inventa_movimientos(self):
        url = reverse("admin:catalogo_variante_change", args=[self.variante.pk])
        self.client.post(
            url,
            {
                "producto": self.producto.pk,
                "nombre": "",
                "sku": self.variante.sku,
                "activa": "on",
                "orden": 0,
                "precio": 520000,
                "precio_antes": "",
                "stock": 10,
                "stock_minimo": 3,
            },
        )
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.precio, 520000)
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_cargar_mercancia_desde_el_panel(self):
        respuesta = self.client.post(
            reverse("admin:inventario_movimiento_add"),
            {
                "variante": self.variante.pk,
                "tipo": Movimiento.ENTRADA,
                "cantidad": 12,
                "motivo": "Llegó el pedido del proveedor",
            },
        )
        self.assertEqual(respuesta.status_code, 302)
        self.variante.refresh_from_db()
        self.assertEqual(self.variante.stock, 22)
        self.assertEqual(Movimiento.objects.count(), 1)

    def test_el_historial_se_puede_mirar_pero_no_editar(self):
        servicios.entrada(self.variante, 1, motivo="Entrada de prueba")
        m = Movimiento.objects.get()
        url = reverse("admin:inventario_movimiento_change", args=[m.pk])

        # Se abre para consultarlo...
        self.assertEqual(self.client.get(url).status_code, 200)
        # ...pero guardar encima no está permitido.
        self.assertEqual(self.client.post(url, {"cantidad": 999}).status_code, 403)

        m.refresh_from_db()
        self.assertEqual(m.cantidad, 1)

    def test_el_historial_no_se_borra(self):
        servicios.entrada(self.variante, 1)
        m = Movimiento.objects.get()
        respuesta = self.client.get(reverse("admin:inventario_movimiento_delete", args=[m.pk]))
        self.assertEqual(respuesta.status_code, 403)

    def test_el_tablero_muestra_lo_que_hay_que_atender(self):
        servicios.salida(self.variante, 9)  # queda 1, bajo el mínimo
        panel = self.client.get(reverse("admin:index"))
        self.assertEqual(panel.status_code, 200)

        alertas = panel.context["alertas"]
        self.assertTrue(alertas["hay_algo"])
        # La ficha de reposición lleva al listado ya filtrado por las que
        # están bajo el mínimo, con la cuenta de cuántas son.
        reponer = [f for f in alertas["fichas"] if "situacion=bajas" in f["url"]]
        self.assertEqual([f["cuantos"] for f in reponer], [1])
