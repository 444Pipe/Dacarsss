"""El historial de inventario.

Es de solo lectura a propósito: un movimiento ya ocurrido no se edita ni se
borra, porque entonces deja de ser un historial. Lo único que se puede hacer es
**agregar** uno nuevo, y eso sirve justo para lo que el comercio hace a diario:
llegó mercancía, se dañó una pieza, volvió algo que se había sacado.

Las ventas no se cargan a mano: las escribe el sistema cuando se confirma un
pedido.
"""

from django import forms
from dacars import colores
from django.contrib import admin, messages
from django.utils.html import format_html

from inventario import servicios
from inventario.models import Movimiento


class FormMovimiento(forms.ModelForm):
    """Solo los movimientos que se cargan a mano."""

    TIPOS_MANUALES = [
        (Movimiento.ENTRADA, "Entrada — llegó mercancía"),
        (Movimiento.SALIDA, "Salida — se usó, se dañó o se regaló"),
        (Movimiento.DEVOLUCION, "Devolución — volvió al inventario"),
    ]

    tipo = forms.ChoiceField(choices=TIPOS_MANUALES, label="Qué pasó")
    cantidad = forms.IntegerField(min_value=1, label="Cuántas unidades")

    class Meta:
        model = Movimiento
        fields = ("variante", "tipo", "cantidad", "motivo")
        labels = {"variante": "Producto y medida"}

    def clean(self):
        datos = super().clean()
        variante = datos.get("variante")
        cantidad = datos.get("cantidad")
        if variante and cantidad and datos.get("tipo") == Movimiento.SALIDA:
            if cantidad > variante.stock:
                self.add_error(
                    "cantidad",
                    "No se puede sacar {}: solo hay {} en existencia.".format(
                        cantidad, variante.stock
                    ),
                )
        return datos


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    form = FormMovimiento
    list_display = ("creado", "variante", "que_paso", "cambio", "stock_despues", "motivo", "usuario")
    list_filter = ("tipo", "creado", "variante__producto__categoria")
    search_fields = ("variante__sku", "variante__producto__nombre", "motivo")
    date_hierarchy = "creado"
    list_select_related = ("variante", "variante__producto", "usuario", "pedido")
    list_per_page = 50
    autocomplete_fields = ("variante",)

    @admin.display(description="movimiento", ordering="tipo")
    def que_paso(self, obj):
        return obj.get_tipo_display().split(" — ")[0]

    @admin.display(description="cambio")
    def cambio(self, obj):
        delta = obj.delta
        color = colores.OK if delta > 0 else colores.MAL if delta < 0 else colores.APAGADO
        return format_html(
            '<b style="color:{}">{}{}</b>', color, "+" if delta > 0 else "", delta
        )

    # -- Solo se agrega; no se edita ni se borra ----------------------------
    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def save_model(self, request, obj, form, change):
        variante = form.cleaned_data["variante"]
        cantidad = form.cleaned_data["cantidad"]
        tipo = form.cleaned_data["tipo"]
        motivo = form.cleaned_data.get("motivo", "")

        if tipo == Movimiento.ENTRADA:
            movimiento = servicios.entrada(variante, cantidad, motivo=motivo, usuario=request.user)
        elif tipo == Movimiento.SALIDA:
            movimiento = servicios.salida(variante, cantidad, motivo=motivo, usuario=request.user)
        else:
            movimiento = servicios.devolver(variante, cantidad, usuario=request.user)

        # El movimiento lo creó el servicio, con las cuentas y el bloqueo de
        # fila hechos. `obj` era el borrador del formulario: lo apuntamos a la
        # fila real para que el admin registre el alta y redirija bien.
        obj.pk = movimiento.pk
        obj.refresh_from_db()

        variante.refresh_from_db()
        messages.info(
            request,
            "{} queda con {} unidad(es) en existencia.".format(variante, variante.stock),
        )
