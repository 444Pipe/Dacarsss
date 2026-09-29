"""Carga el inventario masivo del comercio: los ~260 productos del local.

Los datos viven en `catalogo/semillas/inventario.json`, que se genera con
`tools/inventario-a-semillas.py` a partir del Excel del sistema contable
(la hoja INVENTARIO NUEVO PROGRAMA es el inventario real; las otras dos
hojas solo aportan precios y categorías). Un producto con precio entra con
su variante y se vende con carrito; sin precio entra «a cotizar», con el
botón de WhatsApp.

    python manage.py inventario_masivo             # crea los que falten
    python manage.py inventario_masivo --si-falta  # solo si ninguno está

`--si-falta` es el modo del arranque del contenedor: si ya hay algún
producto de esta semilla en la base, no toca nada. Así un producto borrado
o editado desde el panel no reaparece ni se pisa en el siguiente
despliegue. A un producto existente jamás lo modifica, ni en el modo
manual: el panel es la fuente de verdad después de la primera carga.

Ninguna foto se sube acá: estos productos entran sin imagen y la ficha
muestra «Foto en camino». El feed de Google Merchant los deja afuera hasta
que tengan foto (Google exige imagen), así que cargarles fotos desde el
panel los va metiendo al feed solos.
"""

import json

from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from catalogo.management.commands.catalogo_inicial import SEMILLAS
from catalogo.models import Categoria, Marca, Producto, Variante


class Command(BaseCommand):
    help = "Carga los productos del inventario del comercio (semillas/inventario.json)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--si-falta",
            action="store_true",
            help="No hace nada si algún producto de la semilla ya está en la "
            "base. Es el modo del arranque.",
        )

    def handle(self, *args, **opciones):
        si_falta = opciones["si_falta"]
        datos = json.loads((SEMILLAS / "inventario.json").read_text(encoding="utf-8"))

        if si_falta:
            try:
                slugs = [p["slug"] for p in datos["productos"]]
                if Producto.objects.filter(slug__in=slugs).exists():
                    return
            except DatabaseError:
                # Las migraciones todavía no corrieron: no es motivo para que
                # el contenedor no arranque.
                return

        try:
            with transaction.atomic():
                creados = self._cargar(datos)
        except Exception as error:  # noqa: BLE001 — en el arranque nada puede tumbar el sitio
            if not si_falta:
                raise
            self.stderr.write(
                "inventario_masivo: no se pudo cargar el inventario ({}: {}). "
                "No quedó nada a medias; se reintenta en el próximo arranque.".format(
                    type(error).__name__, error
                )
            )
            return

        if creados:
            self.stdout.write(
                self.style.SUCCESS("{} producto(s) del inventario cargado(s).".format(creados))
            )
        else:
            self.stdout.write("Nada que hacer: el inventario ya estaba cargado.")

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
                continue
            variante = p.get("variante")
            if variante and Variante.objects.filter(sku=variante["sku"]).exists():
                continue

            nombre_cat = p["categoria"]
            if nombre_cat not in categorias:
                categorias[nombre_cat], _ = Categoria.objects.get_or_create(
                    nombre=nombre_cat
                )

            marca = None
            if p.get("marca"):
                if p["marca"] not in marcas:
                    marcas[p["marca"]], _ = Marca.objects.get_or_create(nombre=p["marca"])
                marca = marcas[p["marca"]]

            producto = Producto.objects.create(
                nombre=p["nombre"],
                slug=p["slug"],
                categoria=categorias[nombre_cat],
                marca=marca,
                compatibilidad=p.get("compatibilidad", ""),
                instalacion=p.get("instalacion", True),
                seo_titulo=p.get("seo_titulo", ""),
                seo_descripcion=p.get("seo_descripcion", ""),
            )
            if variante:
                # Sin costo a propósito: la semilla es pública (el repo lo
                # es) y los costos de compra no salen del panel.
                Variante.objects.create(
                    producto=producto,
                    sku=variante["sku"],
                    precio=variante["precio"],
                    stock=variante.get("stock", 0),
                )
            creados += 1
        return creados
