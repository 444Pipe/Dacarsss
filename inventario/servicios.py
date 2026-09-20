"""Las únicas funciones que tienen permiso de tocar las existencias.

Nada más en el proyecto escribe `variante.stock = ...`. Todo pasa por acá, que
bloquea la fila, hace la cuenta y deja el movimiento. Así el número y su
historia no se pueden separar.

Ciclo de un pedido:

    creado      -> reservar()    sube `reservado`, no toca `stock`
    confirmado  -> vender()      baja `stock` y `reservado`, deja movimiento
    cancelado   -> liberar()     baja `reservado` (si todavía no se vendió)
                   devolver()    sube `stock` (si ya se había vendido)
"""

from django.db import transaction

from catalogo.models import Variante
from inventario.models import Movimiento


class SinStock(Exception):
    """No alcanzan las unidades disponibles para lo que se pidió."""

    def __init__(self, variante, pedido, disponible):
        self.variante = variante
        self.pedido = pedido
        self.disponible = disponible
        super().__init__(
            "No hay suficiente {}: se pidieron {} y quedan {}.".format(
                variante, pedido, disponible
            )
        )


def _bloquear(variante):
    """Relee la variante con la fila bloqueada, para que dos pedidos simultáneos
    no lean el mismo stock antes de escribirlo."""
    return Variante.objects.select_for_update().get(pk=variante.pk)


def _anotar(variante, tipo, cantidad, antes, despues, motivo, usuario, pedido):
    return Movimiento.objects.create(
        variante=variante,
        tipo=tipo,
        cantidad=cantidad,
        stock_antes=antes,
        stock_despues=despues,
        motivo=motivo,
        usuario=usuario if (usuario and usuario.is_authenticated) else None,
        pedido=pedido,
    )


# ---------------------------------------------------------------------------
# Entradas y salidas de mostrador
# ---------------------------------------------------------------------------
@transaction.atomic
def entrada(variante, cantidad, motivo="", usuario=None):
    """Llegó mercancía."""
    v = _bloquear(variante)
    antes = v.stock
    v.stock = antes + cantidad
    v.save(update_fields=["stock", "actualizado"])
    return _anotar(v, Movimiento.ENTRADA, cantidad, antes, v.stock, motivo, usuario, None)


@transaction.atomic
def salida(variante, cantidad, motivo="", usuario=None):
    """Salió mercancía por fuera de un pedido: se instaló, se dañó, se regaló."""
    v = _bloquear(variante)
    if cantidad > v.stock:
        raise SinStock(v, cantidad, v.stock)
    antes = v.stock
    v.stock = antes - cantidad
    v.save(update_fields=["stock", "actualizado"])
    return _anotar(v, Movimiento.SALIDA, cantidad, antes, v.stock, motivo, usuario, None)


@transaction.atomic
def ajustar(variante, stock_real, motivo="", usuario=None):
    """El conteo físico dio otra cosa. `stock_real` es lo que hay de verdad."""
    v = _bloquear(variante)
    antes = v.stock
    if antes == stock_real:
        return None
    v.stock = stock_real
    v.save(update_fields=["stock", "actualizado"])
    return _anotar(
        v,
        Movimiento.AJUSTE,
        abs(stock_real - antes),
        antes,
        stock_real,
        motivo or "Ajuste por conteo",
        usuario,
        None,
    )


# ---------------------------------------------------------------------------
# Ciclo del pedido
# ---------------------------------------------------------------------------
@transaction.atomic
def reservar(variante, cantidad):
    """Compromete unidades para un pedido que todavía nadie confirmó.

    No mueve el stock físico: la mercancía sigue en el local. Solo deja de
    ofrecerse en la web.
    """
    v = _bloquear(variante)
    if cantidad > v.disponible:
        raise SinStock(v, cantidad, v.disponible)
    v.reservado = v.reservado + cantidad
    v.save(update_fields=["reservado", "actualizado"])
    return v


@transaction.atomic
def liberar(variante, cantidad):
    """Suelta una reserva: el pedido se canceló antes de confirmarse."""
    v = _bloquear(variante)
    v.reservado = max(v.reservado - cantidad, 0)
    v.save(update_fields=["reservado", "actualizado"])
    return v


@transaction.atomic
def vender(variante, cantidad, pedido=None, usuario=None):
    """El pedido se confirmó: la mercancía sale de verdad."""
    v = _bloquear(variante)
    reservado_ahora = min(cantidad, v.reservado)
    antes = v.stock
    v.stock = max(antes - cantidad, 0)
    v.reservado = v.reservado - reservado_ahora
    v.save(update_fields=["stock", "reservado", "actualizado"])
    motivo = "Pedido " + pedido.numero if pedido else ""
    return _anotar(v, Movimiento.VENTA, cantidad, antes, v.stock, motivo, usuario, pedido)


@transaction.atomic
def devolver(variante, cantidad, pedido=None, usuario=None):
    """Un pedido ya confirmado se canceló: la mercancía vuelve al inventario."""
    v = _bloquear(variante)
    antes = v.stock
    v.stock = antes + cantidad
    v.save(update_fields=["stock", "actualizado"])
    motivo = "Cancelación del pedido " + pedido.numero if pedido else ""
    return _anotar(
        v, Movimiento.DEVOLUCION, cantidad, antes, v.stock, motivo, usuario, pedido
    )
