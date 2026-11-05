"""Carga la imagen de portada de cada categoría del catálogo.

Las portadas viven en catalogo/portadas/, un webp cuadrado por categoría,
nombrado con el slug (iluminacion.webp, tapetes.webp…). Sin portada propia,
la tarjeta de categoría cae a la foto del primer producto —una caja sobre
fondo blanco— o queda vacía si ninguno tiene foto.

Es idempotente y detecta cambios. El archivo se sube con una huella de su
contenido en el nombre (iluminacion-3f9a1c2b.webp): si la categoría ya tiene
una imagen con esa huella, no se toca; si el webp del repositorio cambió
—se rehicieron las portadas—, la huella es otra y se vuelve a subir en el
siguiente arranque, sin que nadie tenga que acordarse de forzar nada.

Una imagen cargada a mano desde el panel no lleva el nombre del slug y por
eso no se pisa, salvo con --forzar.

    python manage.py portadas_categorias
    python manage.py portadas_categorias --forzar
"""

import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from catalogo.models import Categoria

CARPETA = Path(settings.BASE_DIR) / "catalogo" / "portadas"


def _huella(datos):
    return hashlib.sha1(datos).hexdigest()[:8]


def _es_nuestra(categoria, slug):
    """Si la imagen actual la subió este comando (con o sin huella).

    Cloudinary puede agregarle un sufijo aleatorio al nombre y omitir la
    extensión; el almacenamiento local la conserva. Se acepta cualquiera.
    """
    if not categoria.imagen:
        return False
    base = Path(categoria.imagen.name).name
    patron = r"^%s(-[0-9a-f]{8})?(_[A-Za-z0-9]+)?(\.webp)?$" % re.escape(slug)
    return re.match(patron, base) is not None


class Command(BaseCommand):
    help = "Asigna las portadas de catalogo/portadas/ a las categorías por slug."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Reemplaza también las categorías con imagen cargada a mano.",
        )

    def handle(self, *args, **opciones):
        if not CARPETA.is_dir():
            self.stdout.write("No hay carpeta catalogo/portadas/. Nada que hacer.")
            return

        try:
            categorias = {c.slug: c for c in Categoria.objects.all()}
        except DatabaseError:
            # Las migraciones todavía no corrieron. No es motivo para que
            # el contenedor no arranque.
            return

        puestas = 0
        for ruta in sorted(CARPETA.glob("*.webp")):
            slug = ruta.stem
            categoria = categorias.get(slug)
            if categoria is None:
                self.stdout.write("  ? {} (no hay categoría con ese slug)".format(ruta.name))
                continue

            datos = ruta.read_bytes()
            huella = _huella(datos)
            actual = categoria.imagen.name if categoria.imagen else ""

            if actual and huella in actual:
                self.stdout.write("  = {} (al día)".format(categoria.nombre))
                continue
            if actual and not _es_nuestra(categoria, slug) and not opciones["forzar"]:
                self.stdout.write(
                    "  = {} (tiene una imagen cargada a mano, no se tocó)".format(categoria.nombre)
                )
                continue

            with ruta.open("rb") as archivo:
                categoria.imagen.save(
                    "{}-{}.webp".format(slug, huella), File(archivo), save=True
                )
            puestas += 1
            self.stdout.write(self.style.SUCCESS("  + " + categoria.nombre))

        self.stdout.write("")
        if puestas:
            self.stdout.write(self.style.SUCCESS("{} portada(s) asignada(s).".format(puestas)))
        else:
            self.stdout.write("Nada que hacer: las portadas ya estaban.")
