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

from django.test import SimpleTestCase

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
