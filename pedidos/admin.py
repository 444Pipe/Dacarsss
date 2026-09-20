"""Los pedidos, vistos desde el panel.

Las líneas del pedido son de solo lectura. No es pereza: el precio y la
descripción quedaron congelados al momento de la compra, y las unidades ya
están reservadas o descontadas del inventario. Editar una línea a mano
desincronizaría el stock sin dejar rastro. Si un pedido cambia, se cancela
(la mercancía vuelve sola) y se arma de nuevo.
"""

from django.contrib import admin, messages
from django.utils.html import format_html

from pedidos.models import ItemPedido, Pedido


class ItemInline(admin.TabularInline):
    model = ItemPedido
    extra = 0
    can_delete = False
    fields = ("descripcion", "sku", "precio", "cantidad", "subtotal_pesos")
    readonly_fields = fields
    verbose_name_plural = "Productos del pedido (congelados al momento de la compra)"

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description="subtotal")
    def subtotal_pesos(self, obj):
        return "${:,.0f}".format(obj.subtotal).replace(",", ".")


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ("numero", "creado", "nombre", "contacto", "unidades_pedidas", "total_pesos", "senal")
    list_filter = ("estado", "creado", "ciudad")
    search_fields = ("numero", "nombre", "telefono", "email", "items__sku", "items__descripcion")
    date_hierarchy = "creado"
    inlines = [ItemInline]
    list_per_page = 40
    save_on_top = True
    actions = ("accion_confirmar", "accion_entregar", "accion_cancelar")

    readonly_fields = (
        "numero",
        "total_pesos",
        "creado",
        "actualizado",
        "confirmado_en",
        "stock_descontado",
        "boton_whatsapp",
    )
    fieldsets = (
        (
            None,
            {
                "fields": ("numero", "estado", "total_pesos", "boton_whatsapp"),
                "description": "Confirmar el pedido descuenta la mercancía del "
                "inventario. Cancelarlo la devuelve.",
            },
        ),
        (
            "Cliente",
            {"fields": ("nombre", "telefono", "email", "ciudad", "direccion", "vehiculo")},
        ),
        ("Mensajes", {"fields": ("notas", "notas_internas")}),
        (
            "Trazas",
            {
                "classes": ("collapse",),
                "fields": ("stock_descontado", "creado", "confirmado_en", "actualizado"),
            },
        ),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("items")

    # -- Columnas -----------------------------------------------------------
    @admin.display(description="contacto")
    def contacto(self, obj):
        return format_html(
            '<a href="https://wa.me/{}" target="_blank" rel="noopener">{}</a>',
            "57" + "".join(c for c in obj.telefono if c.isdigit())[-10:],
            obj.telefono,
        )

    @admin.display(description="unidades")
    def unidades_pedidas(self, obj):
        return obj.unidades

    @admin.display(description="total", ordering="total")
    def total_pesos(self, obj):
        return "${:,.0f}".format(obj.total).replace(",", ".")

    @admin.display(description="estado", ordering="estado")
    def senal(self, obj):
        colores = {
            Pedido.NUEVO: ("#b45309", "NUEVO"),
            Pedido.CONFIRMADO: ("#1d4ed8", "confirmado"),
            Pedido.ENTREGADO: ("#15803d", "entregado"),
            Pedido.CANCELADO: ("#6b7280", "cancelado"),
        }
        color, texto = colores.get(obj.estado, ("#6b7280", obj.estado))
        return format_html('<b style="color:{}">{}</b>', color, texto)

    @admin.display(description="Escribirle al cliente")
    def boton_whatsapp(self, obj):
        if not obj.pk:
            return "—"
        numero = "57" + "".join(c for c in obj.telefono if c.isdigit())[-10:]
        return format_html(
            '<a class="button" href="https://wa.me/{}" target="_blank" rel="noopener">'
            "Abrir WhatsApp con {}</a>",
            numero,
            obj.nombre,
        )

    # -- Acciones -----------------------------------------------------------
    @admin.action(description="Confirmar (descuenta del inventario)")
    def accion_confirmar(self, request, queryset):
        hechos = 0
        for pedido in queryset:
            if pedido.confirmar(usuario=request.user):
                hechos += 1
        self.message_user(
            request,
            "{} pedido(s) confirmado(s) y descontado(s) del inventario.".format(hechos),
            messages.SUCCESS if hechos else messages.WARNING,
        )

    @admin.action(description="Marcar como entregado")
    def accion_entregar(self, request, queryset):
        hechos = sum(1 for p in queryset if p.entregar(usuario=request.user))
        self.message_user(request, "{} pedido(s) entregado(s).".format(hechos))

    @admin.action(description="Cancelar (devuelve la mercancía)")
    def accion_cancelar(self, request, queryset):
        hechos = sum(1 for p in queryset if p.cancelar(usuario=request.user))
        self.message_user(
            request,
            "{} pedido(s) cancelado(s). La mercancía volvió al inventario.".format(hechos),
        )

    def save_model(self, request, obj, form, change):
        """Cambiar el estado desde el formulario mueve el inventario igual que
        las acciones. Si no, el número del panel y el del local se separan."""
        if change and "estado" in form.changed_data:
            nuevo = obj.estado
            obj.estado = Pedido.objects.values_list("estado", flat=True).get(pk=obj.pk)
            super().save_model(request, obj, form, change)
            if nuevo == Pedido.CONFIRMADO:
                obj.confirmar(usuario=request.user)
            elif nuevo == Pedido.ENTREGADO:
                obj.entregar(usuario=request.user)
            elif nuevo == Pedido.CANCELADO:
                obj.cancelar(usuario=request.user)
            else:
                obj.estado = nuevo
                super().save_model(request, obj, form, change)
            obj.refresh_from_db()
            return
        super().save_model(request, obj, form, change)
