"""Que el proyecto arranque aunque una variable de entorno venga mal.

Esto existe por un incidente real: se pegó mal `CLOUDINARY_URL` en el panel de
Railway y el contenedor no llegó ni a levantar. El paquete `cloudinary` lee esa
variable apenas se importa y revienta si no empieza con `cloudinary://`, así
que una credencial mal copiada se llevó puesto el sitio entero — incluidas las
11 landings, que no tienen nada que ver con subir fotos.

Se prueba en un proceso aparte porque es justo lo que hay que verificar: que
`python manage.py` **arranque**. Dentro del proceso de pruebas los settings ya
están cargados y no se puede reproducir.
"""

import os
import subprocess
import sys
from pathlib import Path

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase

RAIZ = Path(__file__).resolve().parent.parent


def _arrancar(**variables):
    """Corre `manage.py check` con estas variables. Devuelve (código, salida)."""
    entorno = dict(os.environ)
    entorno.pop("CLOUDINARY_URL", None)
    entorno.update({"SECRET_KEY": "x" * 60, "DEBUG": "0"})
    entorno.update(variables)
    proceso = subprocess.run(
        [sys.executable, "manage.py", "check"],
        cwd=RAIZ,
        env=entorno,
        capture_output=True,
        text=True,
        timeout=120,
    )
    return proceso.returncode, proceso.stdout + proceso.stderr


class ArranqueConVariablesMalas(SimpleTestCase):
    def test_cloudinary_con_el_texto_de_relleno(self):
        # El caso real: se pegó la instrucción en vez del valor.
        codigo, salida = _arrancar(CLOUDINARY_URL="<pega aca tu valor>")
        self.assertEqual(codigo, 0, "el proyecto no arrancó:\n" + salida)
        self.assertIn("CLOUDINARY_URL", salida)

    def test_cloudinary_con_la_linea_entera(self):
        codigo, salida = _arrancar(
            CLOUDINARY_URL="CLOUDINARY_URL=cloudinary://1:2@nube"
        )
        self.assertEqual(codigo, 0, "el proyecto no arrancó:\n" + salida)

    def test_cloudinary_entre_comillas_se_limpia(self):
        # Pegar con comillas es común y no debería romper nada.
        codigo, salida = _arrancar(CLOUDINARY_URL='"cloudinary://1:2@nube"')
        self.assertEqual(codigo, 0, "el proyecto no arrancó:\n" + salida)
        self.assertNotIn("mal escrita", salida)

    def test_sin_cloudinary(self):
        codigo, salida = _arrancar()
        self.assertEqual(codigo, 0, "el proyecto no arrancó:\n" + salida)

    def test_sin_secret_key_no_usa_la_de_desarrollo(self):
        codigo, salida = _arrancar(SECRET_KEY="")
        self.assertEqual(codigo, 0, "el proyecto no arrancó:\n" + salida)
        self.assertIn("SECRET_KEY", salida)


class ElPanelSeDibuja(TestCase):
    """Que cada pantalla del panel renderice, con datos en todos sus estados.

    Las columnas de colores se arman con `format_html` desde Python, y ahí un
    hueco sin argumento o un nombre mal escrito no lo ve nadie hasta que
    alguien abre la lista. Esta clase abre todas.
    """

    def setUp(self):
        from catalogo.models import Categoria, Producto, Variante
        from inventario import servicios
        from pedidos.models import ItemPedido, Pedido

        self.jefe = User.objects.create_superuser("jefa", "jefa@dacars.co", "clave-larga-123")
        self.client.force_login(self.jefe)

        categoria = Categoria.objects.create(nombre="Llantas y rines")

        # Un producto de cada situación, para tocar todas las ramas.
        completo = Producto.objects.create(nombre="Llanta con stock", categoria=categoria)
        Variante.objects.create(producto=completo, nombre="265/65R17", precio=850000, stock=9)

        bajo = Producto.objects.create(nombre="Llanta bajo minimo", categoria=categoria)
        Variante.objects.create(producto=bajo, precio=620000, stock=1, stock_minimo=3)

        agotado = Producto.objects.create(nombre="Llanta agotada", categoria=categoria)
        self.agotada = Variante.objects.create(producto=agotado, precio=700000, stock=0)

        # Sin variantes: no tiene precio ni existencias que mostrar.
        Producto.objects.create(nombre="Producto a medio cargar", categoria=categoria)

        # Un rango de precios, y una variante con unidades reservadas.
        rango = Producto.objects.create(nombre="Llanta con medidas", categoria=categoria)
        reservada = Variante.objects.create(producto=rango, nombre="chica", precio=400000, stock=8)
        Variante.objects.create(producto=rango, nombre="grande", precio=900000, stock=4)
        servicios.reservar(reservada, 3)

        # Un pedido en cada estado, y movimientos de inventario.
        for estado in ("nuevo", "confirmado", "entregado", "cancelado"):
            pedido = Pedido.objects.create(nombre="Cliente " + estado, telefono="3112629406")
            ItemPedido.objects.create(
                pedido=pedido, variante=self.agotada, descripcion="x",
                sku=self.agotada.sku, precio=700000, cantidad=1,
            )
            pedido.recalcular_total()
            pedido.estado = estado
            pedido.save()

        servicios.entrada(self.agotada, 4, motivo="Llegó mercancía", usuario=self.jefe)
        servicios.salida(self.agotada, 2, motivo="Se dañó", usuario=self.jefe)
        servicios.ajustar(self.agotada, 5, motivo="Conteo", usuario=self.jefe)

    def test_todas_las_pantallas_abren(self):
        from django.urls import reverse

        pantallas = [
            ("tablero", reverse("admin:index")),
            ("productos", reverse("admin:catalogo_producto_changelist")),
            ("productos sin foto", reverse("admin:catalogo_producto_changelist") + "?completitud=sin_foto"),
            ("productos sin variante", reverse("admin:catalogo_producto_changelist") + "?completitud=sin_variante"),
            ("existencias", reverse("admin:catalogo_variante_changelist")),
            ("existencias bajas", reverse("admin:catalogo_variante_changelist") + "?situacion=bajas"),
            ("existencias agotadas", reverse("admin:catalogo_variante_changelist") + "?situacion=agotadas"),
            ("existencias reservadas", reverse("admin:catalogo_variante_changelist") + "?situacion=reservadas"),
            ("categorías", reverse("admin:catalogo_categoria_changelist")),
            ("pedidos", reverse("admin:pedidos_pedido_changelist")),
            ("movimientos", reverse("admin:inventario_movimiento_changelist")),
            ("cargar mercancía", reverse("admin:inventario_movimiento_add")),
            ("producto nuevo", reverse("admin:catalogo_producto_add")),
        ]
        for nombre, url in pantallas:
            with self.subTest(pantalla=nombre):
                respuesta = self.client.get(url)
                self.assertEqual(respuesta.status_code, 200, nombre + " no abrió")

    def test_la_ficha_de_un_pedido_abre(self):
        from django.urls import reverse
        from pedidos.models import Pedido

        for pedido in Pedido.objects.all():
            with self.subTest(estado=pedido.estado):
                url = reverse("admin:pedidos_pedido_change", args=[pedido.pk])
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_el_panel_lleva_la_marca(self):
        from django.urls import reverse

        html = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("css/panel.css", html)
        self.assertIn("logo-wordmark", html)
        self.assertIn("Qué hay para hoy", html)


class LaEntradaAlPanel(TestCase):
    def test_la_pantalla_de_entrada_es_la_de_dacars(self):
        respuesta = self.client.get("/admin/login/")
        self.assertEqual(respuesta.status_code, 200)
        html = respuesta.content.decode()
        self.assertIn("Panel administrativo", html)
        self.assertIn("logo-wordmark", html)
        self.assertIn("Volver al sitio", html)
        self.assertIn("css/panel.css", html)
        # Sin la barra de encabezado del admin: acá todavía no hay dónde ir.
        self.assertNotIn('id="header"', html)

    def test_una_clave_mala_avisa_sin_romper(self):
        User.objects.create_superuser("jefa", "jefa@dacars.co", "clave-larga-123")
        respuesta = self.client.post(
            "/admin/login/", {"username": "jefa", "password": "equivocada"}
        )
        self.assertEqual(respuesta.status_code, 200)
        # El texto lo pone Django, y conviene: distingue "clave incorrecta" de
        # "cuenta desactivada", que son dos problemas distintos. La plantilla
        # solo pone el suyo cuando Django no dice nada.
        self.assertContains(respuesta, "dc-entrar__error")
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_con_la_clave_correcta_entra(self):
        User.objects.create_superuser("jefa", "jefa@dacars.co", "clave-larga-123")
        respuesta = self.client.post(
            "/admin/login/",
            {"username": "jefa", "password": "clave-larga-123", "next": "/admin/"},
        )
        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(respuesta["Location"], "/admin/")
