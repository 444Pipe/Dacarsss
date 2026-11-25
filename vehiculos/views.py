"""Carros en venta: la lista y la ficha de cada uno."""

from django.db import DatabaseError
from django.shortcuts import get_object_or_404, render

from sitio.templatetags.dacars import foto
from vehiculos.models import Vehiculo


def en_vitrina(cuantos=None):
    """Los carros publicados con sus fotos; los vendidos al final."""
    carros = list(Vehiculo.objects.publicados().prefetch_related("fotos"))
    carros.sort(key=lambda c: c.vendido)  # estable: respeta el orden del modelo
    return carros[:cuantos] if cuantos else carros


def menu(request):
    """Context processor: el enlace «Carros en venta» solo sale si hay alguno."""
    try:
        hay = Vehiculo.objects.publicados().exists()
    except DatabaseError:
        # Las migraciones todavía no corrieron (primer arranque).
        hay = False
    return {"hay_vehiculos": hay}


def lista(request):
    carros = en_vitrina()
    contexto = {
        "carros": carros,
        "titulo": "Carros en venta en Villavicencio | DACARS",
        "descripcion": "Carros y camionetas usados en venta en Villavicencio, Meta. "
        "Míralos en el local de DACARS o pide información por WhatsApp.",
    }
    if not carros:
        # Sin carros, la página existe pero no se le ofrece a Google.
        contexto["robots"] = "noindex, follow"
    return render(request, "vehiculos/lista.html", contexto)


def detalle(request, slug):
    carro = get_object_or_404(
        Vehiculo.objects.publicados().prefetch_related("fotos"), slug=slug
    )
    contexto = {
        "carro": carro,
        "fotos": list(carro.fotos.all()),
        "otros": [c for c in en_vitrina() if c.pk != carro.pk and not c.vendido][:3],
        "titulo": "{} en venta en Villavicencio | DACARS".format(carro.nombre),
        "descripcion": carro.descripcion_seo,
    }
    principal = carro.foto_principal
    if principal:
        contexto["og_imagen"] = foto(principal.imagen, 1200)
    return render(request, "vehiculos/detalle.html", contexto)
