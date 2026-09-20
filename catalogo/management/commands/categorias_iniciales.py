"""Crea las categorías del catálogo a partir de los 9 servicios del sitio.

Se corre una vez, al empezar. Deja el catálogo listo para que el comercio
entre a cargar productos sin tener que inventar la estructura, y cada
categoría queda enlazada con su landing: el catálogo y el SEO se alimentan
entre sí en vez de competir.

Es idempotente: correrlo de nuevo no duplica nada ni pisa lo que hayan editado.

    python manage.py categorias_iniciales
"""

from django.core.management.base import BaseCommand
from django.db import DatabaseError

from catalogo.models import Categoria

CATEGORIAS = [
    (
        "Lujos y accesorios",
        "lujos-y-accesorios-villavicencio",
        "Estribos, barras, cocuyos, forros, tapetes y todo lo que le cambia la "
        "cara a tu carro. Lo que está en existencia sale del local el mismo día.",
        10,
    ),
    (
        "Accesorios 4x4",
        "accesorios-4x4-villavicencio",
        "Snorkel, bumpers, winches, rieles y protección para el carro que de "
        "verdad sale de la carretera. Pensado para la trocha del Meta.",
        20,
    ),
    (
        "Iluminación",
        "iluminacion-para-carros-villavicencio",
        "Barras LED, exploradoras, luces de cortesía y bombillos. Más luz en la "
        "vía al Llano, que de noche no perdona.",
        30,
    ),
    (
        "Sonido",
        "sonido-para-carros-villavicencio",
        "Pantallas, parlantes, amplificadores y bajos. Desde cambiar los "
        "parlantes de fábrica hasta un equipo completo.",
        40,
    ),
    (
        "Llantas y rines",
        "llantas-villavicencio",
        "Llantas por medida, para calle y para trocha. Si no tenemos tu medida "
        "en el local, la conseguimos.",
        50,
    ),
    (
        "Polarizados",
        "polarizados-villavicencio",
        "Películas de seguridad y control solar, por porcentaje. Menos calor "
        "adentro, que en Villavicencio se agradece.",
        60,
    ),
    (
        "PPF y protección de pintura",
        "ppf-villavicencio",
        "Película de poliuretano que protege la pintura de la grava y la arena. "
        "Se cotiza por zona del vehículo.",
        70,
    ),
    (
        "Detailing",
        "detailing-villavicencio",
        "Ceras, selladores, cerámicos y productos de mantenimiento para dejar "
        "el carro como recién entregado.",
        80,
    ),
]


class Command(BaseCommand):
    help = "Crea las categorías iniciales del catálogo, enlazadas a los servicios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--si-vacio",
            action="store_true",
            help="No hace nada si ya hay categorías. Es el modo con el que "
            "corre en el arranque del contenedor: siembra la primera vez y "
            "después se calla, así una categoría borrada a propósito no "
            "reaparece en el siguiente despliegue.",
        )

    def handle(self, *args, **opciones):
        if opciones["si_vacio"]:
            try:
                if Categoria.objects.exists():
                    return
            except DatabaseError:
                # Las migraciones todavía no corrieron. No es motivo para que
                # el contenedor no arranque.
                return

        creadas = 0
        for nombre, servicio, descripcion, orden in CATEGORIAS:
            categoria, nueva = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "descripcion": descripcion,
                    "servicio": servicio,
                    "orden": orden,
                },
            )
            if nueva:
                creadas += 1
                self.stdout.write(self.style.SUCCESS("  + " + nombre))
            else:
                self.stdout.write("  = " + nombre + " (ya estaba, no se tocó)")

        self.stdout.write("")
        if creadas:
            self.stdout.write(
                self.style.SUCCESS(
                    "{} categoría(s) creada(s). Ya se pueden cargar productos "
                    "desde /admin/.".format(creadas)
                )
            )
        else:
            self.stdout.write("Nada que hacer: las categorías ya existían.")
