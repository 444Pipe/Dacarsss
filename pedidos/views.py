"""Carrito y pedido.

El pedido se crea dentro de una transacción que también reserva el inventario.
Si entre que el cliente llenó el formulario y le dio enviar alguien más se
llevó la última unidad, la reserva falla, la transacción se deshace entera y el
cliente vuelve al carrito con el aviso. Nunca queda un pedido por mercancía que
no existe.
"""

from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from catalogo.models import Variante
from inventario.servicios import SinStock
from pedidos.carrito import Carrito
from pedidos.forms import FormPedido
from pedidos.models import ItemPedido, Pedido


def _volver(request, por_defecto="pedidos:carrito"):
    """Vuelve a donde estaba el cliente, si el origen es de este sitio."""
    destino = request.POST.get("volver") or request.META.get("HTTP_REFERER")
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return HttpResponseRedirect(destino)
    return redirect(por_defecto)


def ver(request):
    bolsa = Carrito(request)
    lineas, avisos = bolsa.lineas()
    for aviso in avisos:
        messages.warning(request, aviso)
    return render(
        request,
        "pedidos/carrito.html",
        {
            "titulo": "Tu carrito | DACARS Villavicencio",
            "robots": "noindex, follow",
            "seccion": "catalogo",
            "lineas": lineas,
            "total": sum((l["subtotal"] for l in lineas), 0),
            "unidades": sum(l["cantidad"] for l in lineas),
        },
    )


@require_POST
def agregar(request):
    variante = get_object_or_404(
        Variante, sku=request.POST.get("sku", ""), activa=True, producto__activo=True
    )
    try:
        cantidad = int(request.POST.get("cantidad", "1"))
    except ValueError:
        cantidad = 1

    if variante.disponible <= 0:
        messages.error(request, "{} está agotado por ahora.".format(variante))
        return _volver(request)

    puestas = Carrito(request).agregar(variante, cantidad)
    if puestas < cantidad:
        messages.warning(
            request,
            "Solo quedan {} unidad(es) de {}. Eso fue lo que agregamos.".format(
                puestas, variante
            ),
        )
    else:
        messages.success(request, "{} va en el carrito.".format(variante))

    if request.POST.get("ir") == "carrito":
        return redirect("pedidos:carrito")
    return _volver(request)


@require_POST
def actualizar(request):
    bolsa = Carrito(request)
    variante = get_object_or_404(Variante, sku=request.POST.get("sku", ""))

    # Los botones + y − mandan `delta`; la casilla manda `cantidad`.
    if "delta" in request.POST:
        try:
            paso = int(request.POST["delta"])
        except ValueError:
            paso = 0
        cantidad = bolsa.items.get(variante.sku, 0) + paso
    else:
        try:
            cantidad = int(request.POST.get("cantidad", "1"))
        except ValueError:
            cantidad = 1

    if cantidad <= 0:
        bolsa.quitar(variante.sku)
    else:
        bolsa.agregar(variante, cantidad, reemplazar=True)
    return redirect("pedidos:carrito")


@require_POST
def quitar(request):
    Carrito(request).quitar(request.POST.get("sku", ""))
    return redirect("pedidos:carrito")


def checkout(request):
    bolsa = Carrito(request)
    lineas, avisos = bolsa.lineas()
    for aviso in avisos:
        messages.warning(request, aviso)

    if not lineas:
        messages.info(request, "Tu carrito está vacío.")
        return redirect("catalogo:lista")

    form = FormPedido(request.POST or None)

    if request.method == "POST" and form.is_valid():
        try:
            pedido = _crear_pedido(form, lineas)
        except SinStock as falta:
            messages.error(
                request,
                "Justo se nos acabó: de {} quedan {}. Ajustá la cantidad y "
                "volvé a intentar.".format(falta.variante, falta.disponible),
            )
            return redirect("pedidos:carrito")

        bolsa.vaciar()
        request.session["ultimo_pedido"] = pedido.numero
        return redirect("pedidos:gracias", numero=pedido.numero)

    return render(
        request,
        "pedidos/checkout.html",
        {
            "titulo": "Confirmar el pedido | DACARS Villavicencio",
            "robots": "noindex, nofollow",
            "seccion": "catalogo",
            "form": form,
            "lineas": lineas,
            "total": sum((l["subtotal"] for l in lineas), 0),
        },
    )


@transaction.atomic
def _crear_pedido(form, lineas):
    pedido = form.save(commit=False)
    if not pedido.ciudad:
        pedido.ciudad = "Villavicencio"
    pedido.save()

    ItemPedido.objects.bulk_create(
        [
            ItemPedido(
                pedido=pedido,
                variante=linea["variante"],
                descripcion=str(linea["variante"])[:220],
                sku=linea["variante"].sku,
                precio=linea["precio"],
                costo=linea["variante"].costo,
                cantidad=linea["cantidad"],
            )
            for linea in lineas
        ]
    )
    # Si esta reserva falla, la transacción se lleva el pedido y las líneas.
    pedido.reservar_stock()
    pedido.recalcular_total()
    return pedido


def gracias(request, numero):
    pedido = get_object_or_404(Pedido, numero=numero)
    # El número de pedido es un consecutivo corto y adivinable, así que la
    # pantalla solo se abre para quien acaba de hacerlo (queda en su sesión)
    # o para el equipo. Los datos del cliente no quedan a la vista de nadie.
    propio = request.session.get("ultimo_pedido") == pedido.numero
    if not propio and not request.user.is_staff:
        messages.info(request, "Ese pedido no está en esta sesión.")
        return redirect("catalogo:lista")
    return render(
        request,
        "pedidos/gracias.html",
        {
            "titulo": "Pedido " + pedido.numero + " | DACARS",
            "robots": "noindex, nofollow",
            "seccion": "catalogo",
            "pedido": pedido,
        },
    )
