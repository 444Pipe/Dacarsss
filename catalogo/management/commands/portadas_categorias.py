"""Carga la imagen de portada de cada categoría del catálogo.

Las portadas viven en catalogo/portadas/, un webp cuadrado por categoría,
nombrado con el slug (iluminacion.webp, tapetes.webp…). Sin portada propia,
la tarjeta de categoría cae a la foto del primer producto —una caja sobre
fondo blanco— o queda vacía si ninguno tiene foto.

Es idempotente: solo llena las categorías que no tienen imagen, así que
correrlo en cada arranque no repite subidas a Cloudinary ni pisa una imagen
que el comercio haya cargado desde el panel. Con --forzar las pisa todas,
para cuando se rehagan las portadas.

    python manage.py portadas_categorias
    python manage.py portadas_categorias --forzar
"""

from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import DatabaseError

from catalogo.models import Categoria

CARPETA = Path(settings.BASE_DIR) / "catalogo" / "portadas"


class Command(BaseCommand):
    help = "Asigna las portadas de catalogo/portadas/ a las categorías por slug."

    def add_arguments(self, parser):
        parser.add_argument(
            "--forzar",
            action="store_true",
            help="Reemplaza también las categorías que ya tienen imagen.",
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
            categoria = categorias.get(ruta.stem)
            if categoria is None:
                self.stdout.write("  ? {} (no hay categoría con ese slug)".format(ruta.name))
                continue
            if categoria.imagen and not opciones["forzar"]:
                self.stdout.write("  = {} (ya tiene imagen, no se tocó)".format(categoria.nombre))
                continue
            with ruta.open("rb") as archivo:
                categoria.imagen.save(ruta.name, File(archivo), save=True)
            puestas += 1
            self.stdout.write(self.style.SUCCESS("  + " + categoria.nombre))

        self.stdout.write("")
        if puestas:
            self.stdout.write(self.style.SUCCESS("{} portada(s) asignada(s).".format(puestas)))
        else:
            self.stdout.write("Nada que hacer: las portadas ya estaban.")
