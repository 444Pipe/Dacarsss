"""Movimientos de inventario.

Existe por una razón concreta: con carrito, el stock baja solo. Si el número
cambia sin dejar rastro, el día que falten tres llantas nadie puede explicar
por qué. Cada cambio de existencias pasa por `inventario.servicios` y deja un
renglón acá, con quién lo hizo, cuándo y contra qué pedido.

El campo `stock_antes` / `stock_despues` se guarda aunque sea derivable: es lo
que permite auditar un conteo físico meses después, cuando la variante ya pasó
por veinte movimientos más.
"""

from django.conf import settings
from django.db import models


class Movimiento(models.Model):
    ENTRADA = "entrada"
    SALIDA = "salida"
    VENTA = "venta"
    DEVOLUCION = "devolucion"
    AJUSTE = "ajuste"

    TIPOS = [
        (ENTRADA, "Entrada — llegó mercancía"),
        (VENTA, "Venta — salió por un pedido"),
        (SALIDA, "Salida — se usó o se dañó"),
        (DEVOLUCION, "Devolución — volvió al inventario"),
        (AJUSTE, "Ajuste — corrección por conteo físico"),
    ]

    # Los que suman unidades al stock.
    SUMAN = (ENTRADA, DEVOLUCION)

    variante = models.ForeignKey(
        "catalogo.Variante", on_delete=models.PROTECT, related_name="movimientos"
    )
    tipo = models.CharField(max_length=12, choices=TIPOS)
    cantidad = models.PositiveIntegerField(
        help_text="Siempre en positivo. El signo lo da el tipo de movimiento."
    )
    stock_antes = models.PositiveIntegerField(editable=False)
    stock_despues = models.PositiveIntegerField(editable=False)
    motivo = models.CharField(
        max_length=200,
        blank=True,
        help_text="Opcional, pero muy útil dentro de seis meses. "
        "Ej: conteo del 30/09, llegó pedido a proveedor, se dañó al instalar.",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="movimientos_inventario",
    )
    pedido = models.ForeignKey(
        "pedidos.Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="movimientos",
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-creado", "-id"]
        verbose_name = "movimiento de inventario"
        verbose_name_plural = "movimientos de inventario"
        indexes = [models.Index(fields=["variante", "-creado"])]

    def __str__(self):
        return "{} {} x{}".format(self.get_tipo_display(), self.variante, self.cantidad)

    @property
    def signo(self):
        return 1 if self.tipo in self.SUMAN else -1

    @property
    def delta(self):
        """Cuánto movió el stock, con signo. Es lo que se lee en la lista."""
        if self.tipo == self.AJUSTE:
            return self.stock_despues - self.stock_antes
        return self.signo * self.cantidad
