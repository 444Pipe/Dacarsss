"""Carga el catálogo inicial: los productos fotografiados en el local.

Los datos viven en `catalogo/semillas/`: `catalogo.json` con el texto de cada
producto y `fotos/` con las imágenes ya tratadas (fondo de estudio y, cuando
hay, el producto instalado). Este comando los pasa a la base y sube las fotos
al almacenamiento configurado: Cloudinary en producción, `media/` en local.

Entran todos "a cotizar", sin variantes: la ficha muestra el botón de
WhatsApp en vez de precio. Cuando se le carga una variante con precio desde el
panel, el producto pasa solo a venderse con carrito.

    python manage.py catalogo_inicial              # crea los que falten
    python manage.py catalogo_inicial --si-vacio   # solo si no hay ningún producto

`--si-vacio` es el modo del arranque del contenedor. La base de producción
vive en Railway y no es alcanzable desde afuera, así que la carga tiene que
correr adentro. Corre una vez: apenas hay un producto se calla, y un producto
borrado a propósito no reaparece en el siguiente despliegue.

Es todo o nada. Si una foto no sube (Cloudinary caído, credencial mal puesta)
no queda ningún producto a medias: se deshace todo y el próximo arranque lo
vuelve a intentar entero.
"""

import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from catalogo.models import Categoria, ImagenProducto, Marca, Producto

SEMILLAS = Path(__file__).resolve().parents[2] / "semillas"


class Command(BaseCommand):
    help = "Carga los productos del catálogo inicial, con sus fotos."

    def add_arguments(self, parser):
        parser.add_argument(
            "--si-vacio",
            action="store_true",
            help="No hace nada si ya hay productos. Es el modo del arranque.",
        )

    def handle(self, *args, **opciones):
        si_vacio = opciones["si_vacio"]
        if si_vacio:
            try:
                if Producto.objects.exists():
                    return
            except DatabaseError:
                # Las migraciones todavía no corrieron: no es motivo para que
                # el contenedor no arranque.
                return

        datos = json.loads((SEMILLAS / "catalogo.json").read_text(encoding="utf-8"))

        try:
            with transaction.atomic():
                creados = self._cargar(datos)
        except Exception as error:  # noqa: BLE001 — en el arranque nada puede tumbar el sitio
            if not si_vacio:
                raise
            self.stderr.write(
                "catalogo_inicial: no se pudo cargar el catálogo ({}: {}). "
                "No quedó nada a medias; se reintenta en el próximo arranque.".format(
                    type(error).__name__, error
                )
            )
            return

        if creados:
            self.stdout.write(
                self.style.SUCCESS("{} producto(s) cargado(s) en el catálogo.".format(creados))
            )
        else:
            self.stdout.write("Nada que hacer: los productos ya estaban.")

    def _cargar(self, datos):
        categorias = {}
        for c in datos["categorias"]:
            categoria, nueva = Categoria.objects.get_or_create(
                nombre=c["nombre"],
                defaults={
                    "descripcion": c.get("descripcion", ""),
                    "servicio": c.get("servicio", ""),
                    "orden": c.get("orden", 100),
                },
            )
            categorias[c["nombre"]] = categoria
            if nueva:
                self.stdout.write("  + categoría " + categoria.nombre)

        marcas = {}
        creados = 0
        for p in datos["productos"]:
            if Producto.objects.filter(slug=p["slug"]).exists():
                self.stdout.write("  = " + p["nombre"] + " (ya estaba, no se tocó)")
                continue

            marca = None
            if p.get("marca"):
                if p["marca"] not in marcas:
                    marcas[p["marca"]], _ = Marca.objects.get_or_create(nombre=p["marca"])
                marca = marcas[p["marca"]]

            producto = Producto.objects.create(
                nombre=p["nombre"],
                slug=p["slug"],
                categoria=categorias[p["categoria"]],
                marca=marca,
                resumen=p.get("resumen", ""),
                descripcion=p.get("descripcion", ""),
                caracteristicas="\n".join(p.get("caracteristicas", [])),
                compatibilidad=p.get("compatibilidad", ""),
                instalacion=p.get("instalacion", True),
                destacado=p.get("destacado", False),
                orden=p.get("orden", 100),
                seo_titulo=p.get("seo_titulo", ""),
                seo_descripcion=p.get("seo_descripcion", ""),
            )

            for n, f in enumerate(p.get("fotos", [])):
                ruta = SEMILLAS / "fotos" / f["archivo"]
                imagen = ImagenProducto(
                    producto=producto,
                    tipo=f.get("tipo", ImagenProducto.PRODUCTO),
                    referencia=f.get("referencia", False),
                    alt=f.get("alt", ""),
                    orden=n,
                )
                with ruta.open("rb") as archivo:
                    imagen.imagen.save(ruta.name, File(archivo), save=True)

            creados += 1
            self.stdout.write("  + " + producto.nombre)
        return creados
