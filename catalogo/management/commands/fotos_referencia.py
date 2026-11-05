"""Carga las imágenes de referencia de los productos que no tienen foto.

Viven en catalogo/fotos-referencia/, un webp cuadrado por producto, nombrado
con el slug (bombillo-h4-p43-12v-60-55w-standar.webp). Son imágenes generadas
a partir de la referencia del producto, no fotos de la unidad del local: por
eso se cargan con `referencia=True`, y la ficha las marca «Imagen de
referencia».

Reglas, para no pisar nunca una foto real:

- Un producto sin fotos recibe la de referencia.
- Un producto cuya única foto es una de referencia de esta carpeta (se
  reconoce por el nombre: slug más huella) se actualiza si el webp cambió.
- Un producto con fotos cargadas a mano desde el panel no se toca. El día
  que el comercio sube la foto real, conviene borrar la de referencia desde
  el panel; este comando no la vuelve a poner mientras haya otra foto.

Es idempotente: cada arranque del contenedor lo corre y solo sube lo que
falta o cambió.

    python manage.py fotos_referencia
"""

import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from catalogo.models import ImagenProducto, Producto

CARPETA = Path(settings.BASE_DIR) / "catalogo" / "fotos-referencia"


def _huella(datos):
    return hashlib.sha1(datos).hexdigest()[:8]


def _es_nuestra(imagen, slug):
    base = Path(imagen.imagen.name).name
    patron = r"^%s-[0-9a-f]{8}(_[A-Za-z0-9]+)?(\.webp)?$" % re.escape(slug)
    return re.match(patron, base) is not None


class Command(BaseCommand):
    help = "Asigna las imágenes de referencia de catalogo/fotos-referencia/ por slug."

    def handle(self, *args, **opciones):
        if not CARPETA.is_dir():
            self.stdout.write("No hay carpeta catalogo/fotos-referencia/. Nada que hacer.")
            return

        try:
            productos = {p.slug: p for p in Producto.objects.prefetch_related("imagenes")}
        except DatabaseError:
            return

        puestas = 0
        for ruta in sorted(CARPETA.glob("*.webp")):
            slug = ruta.stem
            producto = productos.get(slug)
            if producto is None:
                self.stdout.write("  ? {} (no hay producto con ese slug)".format(ruta.name))
                continue

            datos = ruta.read_bytes()
            huella = _huella(datos)
            imagenes = list(producto.imagenes.all())
            nuestra = next((i for i in imagenes if _es_nuestra(i, slug)), None)
            reales = [i for i in imagenes if i is not nuestra]

            if reales:
                self.stdout.write("  = {} (tiene fotos propias, no se tocó)".format(producto.nombre))
                continue
            if nuestra is not None and huella in nuestra.imagen.name:
                self.stdout.write("  = {} (al día)".format(producto.nombre))
                continue

            if nuestra is None:
                nuestra = ImagenProducto(
                    producto=producto,
                    tipo=ImagenProducto.PRODUCTO,
                    referencia=True,
                    alt="{} — imagen de referencia".format(producto.nombre)[:160],
                    orden=0,
                )
            with ruta.open("rb") as archivo:
                nuestra.imagen.save("{}-{}.webp".format(slug, huella), File(archivo), save=True)
            puestas += 1
            self.stdout.write(self.style.SUCCESS("  + " + producto.nombre))

        self.stdout.write("")
        if puestas:
            self.stdout.write(self.style.SUCCESS("{} imagen(es) de referencia cargada(s).".format(puestas)))
        else:
            self.stdout.write("Nada que hacer: las imágenes de referencia ya estaban.")
