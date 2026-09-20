"""El arranque del contenedor.

La base vive solo en la nube y no es alcanzable desde afuera, así que el primer
usuario del panel se crea desde adentro, en el arranque. Eso pone dos comandos
en la línea de la que depende que el sitio levante: si alguno se cae con una
variable mal puesta, el contenedor no arranca y el sitio se va con él. Por eso
lo que más se prueba acá es que **no fallen**.
"""

from unittest import mock

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from catalogo.models import Categoria

Usuario = get_user_model()


def con_variables(**variables):
    """Corre con estas variables de entorno y las deja como estaban."""
    return mock.patch.dict("os.environ", variables, clear=False)


class CrearElAdminDesdeLasVariables(TestCase):
    def test_sin_variables_no_hace_nada(self):
        call_command("crear_admin")
        self.assertEqual(Usuario.objects.count(), 0)

    def test_con_las_dos_crea_el_superusuario(self):
        with con_variables(
            ADMIN_USUARIO="jefa",
            ADMIN_CLAVE="clave-larga-de-verdad",
            ADMIN_EMAIL="jefa@dacars.co",
        ):
            call_command("crear_admin")

        cuenta = Usuario.objects.get(username="jefa")
        self.assertTrue(cuenta.is_staff)
        self.assertTrue(cuenta.is_superuser)
        self.assertTrue(cuenta.is_active)
        self.assertTrue(cuenta.check_password("clave-larga-de-verdad"))
        self.assertEqual(cuenta.email, "jefa@dacars.co")

    def test_correrlo_de_nuevo_actualiza_la_clave_sin_duplicar(self):
        Usuario.objects.create_user("jefa", password="vieja")

        with con_variables(ADMIN_USUARIO="jefa", ADMIN_CLAVE="nueva-clave-larga"):
            call_command("crear_admin")

        self.assertEqual(Usuario.objects.filter(username="jefa").count(), 1)
        cuenta = Usuario.objects.get(username="jefa")
        self.assertTrue(cuenta.check_password("nueva-clave-larga"))
        # Un usuario que ya existía y no era del equipo queda habilitado.
        self.assertTrue(cuenta.is_staff)

    def test_con_una_sola_variable_avisa_pero_no_revienta(self):
        # Esto corre en la línea de arranque del contenedor: si lanzara una
        # excepción, el sitio no levantaría por una variable a medio poner.
        with con_variables(ADMIN_USUARIO="jefa"):
            call_command("crear_admin")
        self.assertEqual(Usuario.objects.count(), 0)


class SembrarLasCategorias(TestCase):
    def test_si_vacio_siembra_la_primera_vez(self):
        self.assertEqual(Categoria.objects.count(), 0)
        call_command("categorias_iniciales", "--si-vacio")
        self.assertEqual(Categoria.objects.count(), 8)

    def test_si_vacio_no_repone_lo_que_se_borro(self):
        call_command("categorias_iniciales", "--si-vacio")
        Categoria.objects.filter(nombre="Detailing").delete()

        # El siguiente despliegue no la tiene que traer de vuelta: si la
        # borraron, fue a propósito.
        call_command("categorias_iniciales", "--si-vacio")
        self.assertEqual(Categoria.objects.count(), 7)
        self.assertFalse(Categoria.objects.filter(nombre="Detailing").exists())

    def test_sin_la_bandera_completa_lo_que_falte(self):
        call_command("categorias_iniciales")
        Categoria.objects.filter(nombre="Detailing").delete()
        call_command("categorias_iniciales")
        self.assertEqual(Categoria.objects.count(), 8)

    def test_no_pisa_lo_que_editaron(self):
        call_command("categorias_iniciales")
        categoria = Categoria.objects.get(nombre="Sonido")
        categoria.descripcion = "Texto propio del comercio"
        categoria.save()

        call_command("categorias_iniciales")
        categoria.refresh_from_db()
        self.assertEqual(categoria.descripcion, "Texto propio del comercio")
