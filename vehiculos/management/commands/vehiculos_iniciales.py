"""Carga los carros en venta de vehiculos/semillas/ con sus fotos.

La base de producción vive solo en la nube: esta es la forma de que un carro
cuyas fotos llegaron al repositorio aparezca en el sitio sin cargarlo a mano
desde el panel.

Cada carro de vehiculos.json se crea una sola vez, la primera vez que su slug
no existe. Después el dueño es el panel: precio, kilometraje, textos y fotos
se editan ahí y este comando no los pisa.

Por eso un carro vendido **no se borra**: se marca «Vendido» o se despublica.
Si se borra, el próximo despliegue lo vuelve a crear. Para sacarlo del todo
hay que quitarlo también de vehiculos.json.

    python manage.py vehiculos_iniciales
"""

import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import DatabaseError, transaction

from vehiculos.models import FotoVehiculo, Vehiculo

SEMILLAS = Path(__file__).resolve().parents[2] / "semillas"

CAMPOS = (
    "marca",
    "modelo",
    "version",
    "anio",
    "kilometraje",
    "precio",
    "transmision",
    "combustible",
    "traccion",
    "motor",
    "color",
    "resumen",
    "descripcion",
    "orden",
)


class Command(BaseCommand):
    help = "Crea los carros en venta de vehiculos/semillas/ que todavía no existan."

    def handle(self, *args, **opciones):
        try:
            datos = json.loads((SEMILLAS / "vehiculos.json").read_text(encoding="utf-8"))
            existentes = set(Vehiculo.objects.values_list("slug", flat=True))
        except (OSError, ValueError, DatabaseError) as error:
            self.stdout.write("No se pudieron cargar los carros: {}".format(error))
            return

        creados = 0
        for item in datos.get("vehiculos", []):
            if item["slug"] in existentes:
                self.stdout.write("  = {} (ya estaba)".format(item["slug"]))
                continue
            try:
                # Atómico por carro: si una foto falla al subir, no queda un
                # carro a medias que el próximo arranque ya no completaría.
                with transaction.atomic():
                    carro = Vehiculo(slug=item["slug"])
                    for campo in CAMPOS:
                        if item.get(campo) not in (None, ""):
                            setattr(carro, campo, item[campo])
                    carro.caracteristicas = "\n".join(item.get("caracteristicas", []))
                    carro.save()
                    for n, foto in enumerate(item.get("fotos", [])):
                        ruta = SEMILLAS / "fotos" / foto["archivo"]
                        nueva = FotoVehiculo(
                            vehiculo=carro, alt=foto.get("alt", "")[:160], orden=n
                        )
                        with ruta.open("rb") as archivo:
                            nueva.imagen.save(foto["archivo"], File(archivo), save=True)
            except Exception as error:  # noqa: BLE001 — nunca tumba el arranque
                self.stdout.write(self.style.ERROR("  ! {}: {}".format(item["slug"], error)))
                continue
            creados += 1
            self.stdout.write(self.style.SUCCESS("  + " + carro.nombre))

        if creados:
            self.stdout.write(self.style.SUCCESS("{} carro(s) cargado(s).".format(creados)))
        else:
            self.stdout.write("Nada que hacer: los carros ya estaban.")
