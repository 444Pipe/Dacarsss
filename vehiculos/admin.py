"""Los carros en venta vistos desde el panel: el carro y sus fotos en una sola pantalla."""

from django.contrib import admin
from django.utils.html import format_html

from vehiculos.models import FotoVehiculo, Vehiculo


class FotoInline(admin.TabularInline):
    model = FotoVehiculo
    extra = 3
    fields = ("imagen", "alt", "orden")


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "precio_txt", "kilometraje", "estado", "publicado", "orden", "ver")
    list_editable = ("estado", "publicado", "orden")
    list_filter = ("estado", "publicado", "marca")
    search_fields = ("marca", "modelo", "version")
    inlines = [FotoInline]
    fieldsets = (
        (
            None,
            {
                "fields": (
                    ("marca", "modelo"),
                    ("version", "anio"),
                    ("precio", "negociable"),
                    ("estado", "publicado", "orden"),
                )
            },
        ),
        (
            "Datos del carro",
            {
                "fields": (
                    ("kilometraje", "transmision"),
                    ("combustible", "traccion"),
                    ("motor", "color"),
                    "placa_ciudad",
                )
            },
        ),
        ("Textos", {"fields": ("resumen", "descripcion", "caracteristicas")}),
        ("Dirección de la ficha", {"classes": ("collapse",), "fields": ("slug",)}),
    )

    @admin.display(description="Precio", ordering="precio")
    def precio_txt(self, obj):
        if obj.precio is None:
            return "Consultar"
        return "$" + "{:,}".format(int(obj.precio)).replace(",", ".")

    @admin.display(description="En el sitio")
    def ver(self, obj):
        if not obj.publicado:
            return "—"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">Ver ficha</a>', obj.get_absolute_url()
        )
