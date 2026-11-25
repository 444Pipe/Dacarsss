"""Actualiza las fotos del catálogo inicial cuando cambian en el repositorio.

`catalogo_inicial` carga los productos fotografiados en el local una sola vez
(solo si la base está vacía). Si después se rehacen esas fotos —en noviembre
de 2026 pasaron del fondo de estudio oscuro al fondo blanco de tienda—, la
base de producción se queda con las viejas. Este comando las reemplaza.

Recorre catalogo/semillas/catalogo.json y, para cada foto, busca la imagen
del producto que salió de ese archivo (se reconoce por el nombre). La vuelve
a subir con una huella del contenido en el nombre (xuda-1-3f9a1c2b.webp): si
la huella ya está, no hace nada, así que puede correr en cada arranque.

No toca fotos subidas desde el panel ni productos borrados: si la imagen de
la semilla ya no existe en la base, se la salta.

    python manage.py refrescar_fotos
"""

import hashlib
import json
import re
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from catalogo.models import ImagenProducto

SEMILLAS = Path(__file__).resolve().parents[2] / "semillas"


class Command(BaseCommand):
    help = "Reemplaza las fotos del catálogo inicial que cambiaron en el repositorio."

    def handle(self, *args, **opciones):
        try:
            datos = json.loads((SEMILLAS / "catalogo.json").read_text(encoding="utf-8"))
            existentes = list(ImagenProducto.objects.select_related("producto"))
        except (OSError, DatabaseError):
            return

        por_producto = {}
        for imagen in existentes:
            por_producto.setdefault(imagen.producto.slug, []).append(imagen)

        cambiadas = 0
        for producto in datos.get("productos", []):
            for foto in producto.get("fotos", []):
                ruta = SEMILLAS / "fotos" / foto["archivo"]
                if not ruta.is_file():
                    continue
                base = ruta.stem
                patron = re.compile(
                    r"^%s(-[0-9a-f]{8})?(_[A-Za-z0-9]+)?(\.webp)?$" % re.escape(base)
                )
                imagen = next(
                    (
                        i
                        for i in por_producto.get(producto["slug"], [])
                        if patron.match(Path(i.imagen.name).name)
                    ),
                    None,
                )
                if imagen is None:
                    continue
                contenido = ruta.read_bytes()
                huella = hashlib.sha1(contenido).hexdigest()[:8]
                if huella in imagen.imagen.name:
                    continue
                with ruta.open("rb") as archivo:
                    imagen.imagen.save("{}-{}.webp".format(base, huella), File(archivo), save=True)
                cambiadas += 1
                self.stdout.write(self.style.SUCCESS("  + " + foto["archivo"]))

        if cambiadas:
            self.stdout.write(self.style.SUCCESS("{} foto(s) actualizada(s).".format(cambiadas)))
        else:
            self.stdout.write("Nada que hacer: las fotos ya estaban al día.")
