"""El inventario y el pedido.

Acá está lo que de verdad puede costar plata si se rompe: vender algo que no
hay, o que el número del panel deje de coincidir con lo que está en el local.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from catalogo.models import Categoria, Producto, Variante
from inventario.models import Movimiento
from inventario.servicios import SinStock, reservar
from pedidos.models import ItemPedido, Pedido


class Base(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Llantas y rines")
        self.producto = Producto.objects.create(
            nombre="Llanta todoterreno Grabber",
            categoria=self.categoria,
            resumen="Para trocha y carretera.",
        )
        self.v1 = Variante.objects.create(
            producto=self.producto, nombre="265/65R17", precio=850000, stock=4,
            stock_minimo=2,
        )
        self.v2 = Variante.objects.create(
            producto=self.producto, nombre="235/75R15", precio=620000, stock=1,
            stock_minimo=2,
        )

    def pedir(self, variante, cantidad=1):
        """Un pedido armado a mano, como el que deja el checkout."""
        pedido = Pedido.objects.create(nombre="Andrés Gómez", telefono="3112629406")
        ItemPedido.objects.create(
            pedido=pedido,
            variante=variante,
            descripcion=str(variante),
            sku=variante.sku,
            precio=variante.precio,
            cantidad=cantidad,
        )
        pedido.reservar_stock()
        pedido.recalcular_total()
        return pedido


class CicloDelPedido(Base):
    def test_al_crear_el_pedido_se_reserva_sin_mover_el_stock(self):
        self.pedir(self.v1, 2)
        self.v1.refresh_from_db()

        # La mercancía sigue en el local...
        self.assertEqual(self.v1.stock, 4)
        # ...pero ya no se le ofrece a nadie más.
        self.assertEqual(self.v1.reservado, 2)
        self.assertEqual(self.v1.disponible, 2)
        # Nada salió, así que no hay movimiento de inventario.
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_confirmar_descuenta_y_deja_movimiento(self):
        pedido = self.pedir(self.v1, 2)
        pedido.confirmar()
        self.v1.refresh_from_db()

        self.assertEqual(self.v1.stock, 2)
        self.assertEqual(self.v1.reservado, 0)

        movimiento = Movimiento.objects.get()
        self.assertEqual(movimiento.tipo, Movimiento.VENTA)
        self.assertEqual(movimiento.cantidad, 2)
        self.assertEqual(movimiento.stock_antes, 4)
        self.assertEqual(movimiento.stock_despues, 2)
        self.assertEqual(movimiento.pedido, pedido)

    def test_cancelar_antes_de_confirmar_solo_libera(self):
        pedido = self.pedir(self.v1, 2)
        pedido.cancelar()
        self.v1.refresh_from_db()

        self.assertEqual(self.v1.stock, 4)
        self.assertEqual(self.v1.reservado, 0)
        self.assertEqual(self.v1.disponible, 4)
        # Nunca salió del local: no corresponde anotar nada.
        self.assertEqual(Movimiento.objects.count(), 0)

    def test_cancelar_despues_de_confirmar_devuelve_la_mercancia(self):
        pedido = self.pedir(self.v1, 2)
        pedido.confirmar()
        pedido.cancelar()
        self.v1.refresh_from_db()

        self.assertEqual(self.v1.stock, 4)
        self.assertEqual(self.v1.reservado, 0)
        tipos = list(Movimiento.objects.values_list("tipo", flat=True))
        self.assertEqual(sorted(tipos), [Movimiento.DEVOLUCION, Movimiento.VENTA])

    def test_confirmar_dos_veces_no_descuenta_dos_veces(self):
        pedido = self.pedir(self.v1, 2)
        pedido.confirmar()
        self.assertFalse(pedido.confirmar())
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.stock, 2)

    def test_entregar_descuenta_si_nadie_habia_confirmado(self):
        pedido = self.pedir(self.v1, 1)
        pedido.entregar()
        self.v1.refresh_from_db()
        self.assertEqual(self.v1.stock, 3)
        self.assertEqual(pedido.estado, Pedido.ENTREGADO)


class NoSeVendeLoQueNoHay(Base):
    def test_no_se_puede_reservar_mas_de_lo_disponible(self):
        with self.assertRaises(SinStock):
            reservar(self.v2, 2)  # solo hay 1

    def test_dos_pedidos_no_se_llevan_la_misma_ultima_unidad(self):
        self.pedir(self.v2, 1)
        with self.assertRaises(SinStock):
            self.pedir(self.v2, 1)

    def test_lo_reservado_no_se_ofrece(self):
        self.pedir(self.v2, 1)
        self.v2.refresh_from_db()
        self.assertEqual(self.v2.disponible, 0)
        self.assertTrue(self.v2.agotada)


class PreciosCongelados(Base):
    def test_subir_el_precio_no_cambia_un_pedido_viejo(self):
        pedido = self.pedir(self.v1, 2)
        total = pedido.total

        self.v1.precio = 990000
        self.v1.save()

        pedido.refresh_from_db()
        self.assertEqual(pedido.total, total)
        self.assertEqual(pedido.items.get().precio, 850000)

    def test_el_pedido_recibe_numero(self):
        pedido = self.pedir(self.v1)
        self.assertTrue(pedido.numero.startswith("DC-"))
        self.assertEqual(Pedido.objects.filter(numero=pedido.numero).count(), 1)


class CompraPorLaWeb(Base):
    """El recorrido completo, como lo hace un cliente."""

    def test_agregar_ver_y_confirmar(self):
        agregado = self.client.post(
            reverse("pedidos:agregar"),
            {"sku": self.v1.sku, "cantidad": "2", "volver": self.producto.get_absolute_url()},
        )
        self.assertEqual(agregado.status_code, 302)

        carrito = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(carrito.status_code, 200)
        self.assertContains(carrito, self.producto.nombre)

        respuesta = self.client.post(
            reverse("pedidos:checkout"),
            {
                "nombre": "Andrés Gómez",
                "telefono": "311 262 9406",
                "ciudad": "Villavicencio",
                "entrega": "recoger",
            },
        )
        self.assertEqual(respuesta.status_code, 302)

        pedido = Pedido.objects.get()
        self.assertEqual(pedido.estado, Pedido.NUEVO)
        self.assertEqual(pedido.total, 1700000)

        self.v1.refresh_from_db()
        self.assertEqual(self.v1.reservado, 2)
        self.assertEqual(self.v1.stock, 4)

        # Y el carrito queda vacío, no repetido.
        self.assertEqual(self.client.get(reverse("pedidos:carrito")).context["unidades"], 0)

    def test_el_carrito_no_deja_pedir_mas_de_lo_que_hay(self):
        self.client.post(reverse("pedidos:agregar"), {"sku": self.v2.sku, "cantidad": "5"})
        carrito = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(carrito.context["unidades"], 1)  # solo había 1

    def test_el_carrito_suelta_lo_que_se_dio_de_baja(self):
        self.client.post(reverse("pedidos:agregar"), {"sku": self.v1.sku, "cantidad": "1"})
        self.v1.activa = False
        self.v1.save()

        carrito = self.client.get(reverse("pedidos:carrito"))
        self.assertEqual(carrito.context["unidades"], 0)

    def test_pedir_con_envio_exige_direccion(self):
        self.client.post(reverse("pedidos:agregar"), {"sku": self.v1.sku, "cantidad": "1"})
        respuesta = self.client.post(
            reverse("pedidos:checkout"),
            {"nombre": "Ana", "telefono": "3112629406", "ciudad": "Acacías", "entrega": "enviar"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertFormError(respuesta.context["form"], "direccion", "Necesitamos la dirección para poder enviártelo.")
        self.assertEqual(Pedido.objects.count(), 0)

    def test_telefono_incompleto_no_pasa(self):
        self.client.post(reverse("pedidos:agregar"), {"sku": self.v1.sku, "cantidad": "1"})
        respuesta = self.client.post(
            reverse("pedidos:checkout"),
            {"nombre": "Ana", "telefono": "311", "ciudad": "Villavicencio", "entrega": "recoger"},
        )
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_el_pedido_ajeno_no_se_puede_espiar(self):
        pedido = self.pedir(self.v1)
        # Sesión distinta: nunca hizo ese pedido.
        respuesta = self.client.get(reverse("pedidos:gracias", args=[pedido.numero]))
        self.assertEqual(respuesta.status_code, 302)

    def test_el_equipo_si_puede_verlo(self):
        pedido = self.pedir(self.v1)
        User.objects.create_user("taller", password="x", is_staff=True)
        self.client.login(username="taller", password="x")
        respuesta = self.client.get(reverse("pedidos:gracias", args=[pedido.numero]))
        self.assertEqual(respuesta.status_code, 200)
