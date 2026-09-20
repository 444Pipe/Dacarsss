"""Pedidos.

No hay pasarela de pago: el cliente arma el carrito, deja sus datos y el pedido
queda en el panel. El pago se acuerda por WhatsApp, como se venía haciendo.

Lo que sí hace el pedido es mover el inventario, y ahí está todo el cuidado:

    nuevo       las unidades quedan **reservadas** (no se ofrecen más en la web,
                pero siguen en el local)
    confirmado  salen de verdad del stock
    entregado   igual que confirmado, es solo seguimiento
    cancelado   vuelven: se libera la reserva, o se devuelven al stock si ya
                se habían descontado

`stock_descontado` es el que decide cuál de las dos vueltas corresponde. Sin
ese campo habría que adivinarlo a partir del estado, y el día que alguien sume
un estado nuevo la cuenta se rompe en silencio.
"""

from urllib.parse import quote

from django.conf import settings
from django.db import models, transaction
from django.urls import reverse
from django.utils import timezone


class Pedido(models.Model):
    NUEVO = "nuevo"
    CONFIRMADO = "confirmado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"

    ESTADOS = [
        (NUEVO, "Nuevo — sin responder"),
        (CONFIRMADO, "Confirmado — se descontó del inventario"),
        (ENTREGADO, "Entregado"),
        (CANCELADO, "Cancelado"),
    ]

    numero = models.CharField(max_length=12, unique=True, editable=False, blank=True)
    estado = models.CharField(max_length=12, choices=ESTADOS, default=NUEVO)

    nombre = models.CharField(max_length=120, verbose_name="nombre del cliente")
    telefono = models.CharField(max_length=30, verbose_name="teléfono")
    email = models.EmailField(blank=True, verbose_name="correo")
    ciudad = models.CharField(max_length=80, default="Villavicencio")
    direccion = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="dirección",
        help_text="Solo si lo quieren enviado. Vacío = pasa a recogerlo.",
    )
    vehiculo = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="vehículo",
        help_text="Ej: Toyota Hilux 2022. Sirve para confirmar que el repuesto le sirve.",
    )
    notas = models.TextField(blank=True, verbose_name="notas del cliente")
    notas_internas = models.TextField(
        blank=True, help_text="No lo ve el cliente. Para el equipo."
    )

    total = models.DecimalField(max_digits=12, decimal_places=0, default=0, editable=False)
    stock_descontado = models.BooleanField(default=False, editable=False)

    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)
    confirmado_en = models.DateTimeField(null=True, blank=True, editable=False)

    class Meta:
        ordering = ["-creado"]
        indexes = [models.Index(fields=["estado", "-creado"])]

    def __str__(self):
        return "{} — {}".format(self.numero or "sin número", self.nombre)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # El número sale del pk, así no hay dos pedidos peleando por el mismo
        # consecutivo. Cuesta un UPDATE extra, solo en la creación.
        if not self.numero:
            self.numero = "DC-{:04d}".format(self.pk)
            super().save(update_fields=["numero"])

    def get_absolute_url(self):
        return reverse("pedidos:gracias", args=[self.numero])

    # -- Plata --------------------------------------------------------------
    def recalcular_total(self, guardar=True):
        self.total = sum((i.subtotal for i in self.items.all()), 0)
        if guardar:
            super().save(update_fields=["total", "actualizado"])
        return self.total

    @property
    def unidades(self):
        return sum(i.cantidad for i in self.items.all())

    # -- Estados ------------------------------------------------------------
    @property
    def abierto(self):
        return self.estado in (self.NUEVO, self.CONFIRMADO)

    @transaction.atomic
    def confirmar(self, usuario=None):
        """Sale la mercancía del inventario."""
        from inventario import servicios

        if self.stock_descontado or self.estado == self.CANCELADO:
            return False
        for item in self.items.select_related("variante"):
            servicios.vender(item.variante, item.cantidad, pedido=self, usuario=usuario)
        self.estado = self.CONFIRMADO
        self.stock_descontado = True
        self.confirmado_en = timezone.now()
        super().save(update_fields=["estado", "stock_descontado", "confirmado_en", "actualizado"])
        return True

    @transaction.atomic
    def entregar(self, usuario=None):
        if self.estado == self.CANCELADO:
            return False
        if not self.stock_descontado:
            self.confirmar(usuario=usuario)
        self.estado = self.ENTREGADO
        super().save(update_fields=["estado", "actualizado"])
        return True

    @transaction.atomic
    def cancelar(self, usuario=None):
        """Devuelve lo que corresponda según si ya se había descontado."""
        from inventario import servicios

        if self.estado == self.CANCELADO:
            return False
        for item in self.items.select_related("variante"):
            if self.stock_descontado:
                servicios.devolver(item.variante, item.cantidad, pedido=self, usuario=usuario)
            else:
                servicios.liberar(item.variante, item.cantidad)
        self.estado = self.CANCELADO
        self.stock_descontado = False
        super().save(update_fields=["estado", "stock_descontado", "actualizado"])
        return True

    @transaction.atomic
    def reservar_stock(self):
        """Compromete las unidades al crear el pedido."""
        from inventario import servicios

        for item in self.items.select_related("variante"):
            servicios.reservar(item.variante, item.cantidad)

    # -- WhatsApp -----------------------------------------------------------
    @property
    def resumen_texto(self):
        lineas = ["Hola DACARS, acabo de hacer el pedido " + self.numero + ".", ""]
        for item in self.items.all():
            lineas.append("• {} x{} — ${:,.0f}".format(
                item.descripcion, item.cantidad, item.subtotal
            ).replace(",", "."))
        lineas.append("")
        lineas.append("Total: ${:,.0f}".format(self.total).replace(",", "."))
        if self.vehiculo:
            lineas.append("Vehículo: " + self.vehiculo)
        lineas.append("A nombre de: " + self.nombre)
        if self.direccion:
            lineas.append("Dirección: " + self.direccion + ", " + self.ciudad)
        else:
            lineas.append("Paso a recogerlo al taller.")
        return "\n".join(lineas)

    @property
    def url_whatsapp(self):
        return "https://wa.me/{}?text={}".format(
            settings.NEGOCIO["whatsapp"], quote(self.resumen_texto)
        )


class ItemPedido(models.Model):
    """Una línea del pedido.

    Guarda el precio y la descripción **copiados** al momento de comprar. Si
    mañana suben el precio o le cambian el nombre al producto, el pedido viejo
    tiene que seguir diciendo lo que el cliente aceptó.
    """

    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="items")
    variante = models.ForeignKey(
        "catalogo.Variante", on_delete=models.PROTECT, related_name="items_pedido"
    )
    descripcion = models.CharField(max_length=220, verbose_name="descripción")
    sku = models.CharField(max_length=40)
    precio = models.DecimalField(max_digits=12, decimal_places=0)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "producto del pedido"
        verbose_name_plural = "productos del pedido"

    def __str__(self):
        return "{} x{}".format(self.descripcion, self.cantidad)

    @property
    def subtotal(self):
        return self.precio * self.cantidad
