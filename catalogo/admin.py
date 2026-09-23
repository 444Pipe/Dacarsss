"""El catálogo visto desde el panel.

Una decisión que vale explicar: el campo `existencias` se puede editar a mano
acá, pero **nunca** se escribe directo. El admin compara con lo que había en la
base y manda la diferencia por `inventario.servicios`, que deja el movimiento
con quién lo cambió y cuándo. Para el comercio es escribir un número; para el
inventario es un ajuste auditado. Si se permitiera el atajo, el historial
tendría huecos justo donde más se lo necesita.
"""

from dacars import colores
from django.contrib import admin
from django.db.models import Count, F
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.html import format_html

from catalogo.models import Categoria, ImagenProducto, Marca, Producto, Variante
from inventario import servicios


# ---------------------------------------------------------------------------
# Escribir existencias sin romper el historial
# ---------------------------------------------------------------------------
def _guardar_variante(request, obj, change, campos_cambiados):
    """Guarda la variante mandando cualquier cambio de stock por inventario."""
    if not change:
        inicial = obj.stock
        obj.stock = 0
        obj.save()
        if inicial:
            servicios.entrada(
                obj, inicial, motivo="Carga inicial desde el panel", usuario=request.user
            )
            obj.refresh_from_db()
        return

    if "stock" not in campos_cambiados:
        obj.save()
        return

    nuevo = obj.stock
    anterior = Variante.objects.values_list("stock", flat=True).get(pk=obj.pk)
    obj.stock = anterior  # el resto de campos sí se guardan de una
    obj.save()
    servicios.ajustar(obj, nuevo, motivo="Editado en el panel", usuario=request.user)
    obj.refresh_from_db()


def _pinta_stock(variante):
    if variante.agotada:
        color, texto = colores.MAL, "AGOTADO"
    elif variante.bajo_stock:
        color, texto = colores.OJO, "quedan " + str(variante.disponible)
    else:
        color, texto = colores.OK, str(variante.disponible) + " disponibles"
    extra = ""
    if variante.reservado:
        extra = " ({} reservada{})".format(
            variante.reservado, "s" if variante.reservado != 1 else ""
        )
    return format_html(
        '<b style="color:{}">{}</b><span style="color:{}">{}</span>',
        color,
        texto,
        colores.APAGADO,
        extra,
    )


# ---------------------------------------------------------------------------
# Filtros propios
# ---------------------------------------------------------------------------
class FiltroSituacion(admin.SimpleListFilter):
    title = "situación del stock"
    parameter_name = "situacion"

    def lookups(self, request, model_admin):
        return [
            ("agotadas", "Agotadas"),
            ("bajas", "Bajo el mínimo"),
            ("ok", "Con stock suficiente"),
            ("reservadas", "Con unidades reservadas"),
        ]

    def queryset(self, request, queryset):
        qs = queryset.annotate(_disp=F("stock") - F("reservado"))
        if self.value() == "agotadas":
            return qs.filter(_disp__lte=0)
        if self.value() == "bajas":
            return qs.filter(_disp__lte=F("stock_minimo"))
        if self.value() == "ok":
            return qs.filter(_disp__gt=F("stock_minimo"))
        if self.value() == "reservadas":
            return qs.filter(reservado__gt=0)
        return queryset


class FiltroCompletitud(admin.SimpleListFilter):
    """Lo que falta para que un producto se pueda publicar bien."""

    title = "qué le falta"
    parameter_name = "completitud"

    def lookups(self, request, model_admin):
        return [
            ("sin_foto", "Sin fotos"),
            ("sin_variante", "A cotizar (sin precio)"),
            ("sin_descripcion", "Sin descripción"),
            ("listo", "Completos"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "sin_foto":
            return queryset.filter(imagenes__isnull=True)
        if self.value() == "sin_variante":
            return queryset.filter(variantes__isnull=True)
        if self.value() == "sin_descripcion":
            return queryset.filter(descripcion="")
        if self.value() == "listo":
            return queryset.filter(imagenes__isnull=False, variantes__isnull=False).exclude(
                descripcion=""
            ).distinct()
        return queryset


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------
# Los dos inlines se muestran distinto al crear que al editar. Cuando se carga
# un producto nuevo hace falta lo mínimo —una foto y un precio— y cualquier
# columna de más es una pregunta que no se sabe responder todavía; una vez
# guardado, ya con el producto delante, aparece todo.
class ImagenInline(admin.TabularInline):
    model = ImagenProducto
    verbose_name = "foto"
    verbose_name_plural = "Fotos (la de menor número es la principal)"

    CAMPOS_ALTA = ("imagen", "tipo", "alt")
    CAMPOS = ("vista", "imagen", "tipo", "referencia", "alt", "orden")

    def get_fields(self, request, obj=None):
        return self.CAMPOS_ALTA if obj is None else self.CAMPOS

    def get_readonly_fields(self, request, obj=None):
        # `vista` dibuja la miniatura de una foto ya subida: en el alta todavía
        # no hay ninguna y sería una columna de guiones.
        return () if obj is None else ("vista",)

    def get_extra(self, request, obj=None, **kwargs):
        return 1

    @admin.display(description="")
    def vista(self, obj):
        if obj.pk and obj.imagen:
            return format_html(
                '<img src="{}" style="height:64px;border-radius:6px;object-fit:cover">',
                obj.imagen.url,
            )
        return "—"


class VarianteInline(admin.TabularInline):
    model = Variante
    verbose_name = "medida / presentación"
    # Corto a propósito: el título del inline se dibuja en versalitas con
    # tracking, y una frase larga ahí se vuelve ilegible.
    verbose_name_plural = "Precios y existencias (sin filas, sale «a cotizar»)"

    CAMPOS_ALTA = ("nombre", "costo", "precio", "stock", "stock_minimo")
    CAMPOS = (
        "nombre", "sku", "costo", "precio", "precio_antes",
        "stock", "stock_minimo", "situacion", "activa", "orden",
    )

    def get_fields(self, request, obj=None):
        return self.CAMPOS_ALTA if obj is None else self.CAMPOS

    def get_readonly_fields(self, request, obj=None):
        return () if obj is None else ("situacion",)

    def get_extra(self, request, obj=None, **kwargs):
        # Al crear, una fila ya abierta: lo normal es un solo precio, y dejarla
        # lista ahorra el clic de «añadir otro» que casi nadie encuentra. Al
        # editar, ninguna: las filas vacías confunden más de lo que ayudan.
        return 1 if obj is None else 0

    @admin.display(description="Estado")
    def situacion(self, obj):
        if not obj.pk:
            return "—"
        return _pinta_stock(obj)


# ---------------------------------------------------------------------------
# Modelos
# ---------------------------------------------------------------------------
@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cuantos", "servicio", "orden", "activa")
    list_editable = ("orden", "activa")
    list_filter = ("activa",)
    search_fields = ("nombre", "descripcion")
    prepopulated_fields = {"slug": ("nombre",)}

    # A crear una categoría se llega casi siempre desde el «+» que está al lado
    # del selector, en mitad de la carga de un producto. Ahí no se viene a
    # pensar el SEO ni el orden: se viene a escribir un nombre y volver.
    FIELDSETS_ALTA = (
        (
            None,
            {
                "fields": ("nombre", "descripcion"),
                "description": "Con el nombre alcanza: la dirección en la web se "
                "arma sola. Lo demás lo podés ajustar después desde «Categorías».",
            },
        ),
    )

    fieldsets = (
        (None, {"fields": ("nombre", "slug", "descripcion", "imagen")}),
        (
            "Dónde aparece",
            {
                "fields": ("servicio", "orden", "activa"),
                "description": "El servicio relacionado cruza el catálogo con la "
                "página de ese servicio, en los dos sentidos.",
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        return self.FIELDSETS_ALTA if obj is None else self.fieldsets

    def get_prepopulated_fields(self, request, obj=None):
        # Sin `slug` en el formulario de alta, apuntarle sería un KeyError.
        if obj is None:
            return {}
        return super().get_prepopulated_fields(request, obj)

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_n=Count("productos"))

    @admin.display(description="productos", ordering="_n")
    def cuantos(self, obj):
        return obj._n


@admin.register(Marca)
class MarcaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "activa")
    list_editable = ("activa",)
    search_fields = ("nombre",)
    prepopulated_fields = {"slug": ("nombre",)}


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria", "marca", "precios", "existencias", "publicado")
    list_filter = ("categoria", "marca", "activo", "destacado", FiltroCompletitud)
    search_fields = ("nombre", "resumen", "descripcion", "compatibilidad", "variantes__sku")
    prepopulated_fields = {"slug": ("nombre",)}
    inlines = [VarianteInline, ImagenInline]
    list_per_page = 40
    save_on_top = True
    actions = ("publicar", "despublicar", "destacar", "quitar_destacado")

    # Al crear se pide lo mínimo para publicar; la ficha entera aparece recién
    # al editar. Un formulario de veinte campos frente a un producto que
    # todavía no existe hace que se carguen a medias o no se carguen.
    FIELDSETS_ALTA = (
        (
            "El producto",
            {
                "fields": ("nombre", "categoria", "marca", "resumen"),
                "description": "Con esto ya queda publicado. Apenas lo guardes vas "
                "a poder completar la ficha: descripción larga, características, "
                "compatibilidad, más fotos, más medidas y el texto para Google.",
            },
        ),
    )

    fieldsets = (
        (
            "Lo básico",
            {"fields": ("nombre", "slug", "categoria", "marca", "resumen")},
        ),
        (
            "La ficha",
            {
                "fields": ("descripcion", "caracteristicas", "compatibilidad", "instalacion"),
                "description": "Las características van una por línea. La descripción "
                "acepta varios párrafos: separalos con una línea en blanco.",
            },
        ),
        (
            "Publicación",
            {"fields": ("activo", "destacado", "orden")},
        ),
        (
            "Google (opcional)",
            {
                "classes": ("collapse",),
                "fields": ("seo_titulo", "seo_descripcion"),
                "description": "Si lo dejás vacío se arma solo con el nombre y el "
                "resumen. Llenalo solo si querés un texto distinto en el buscador.",
            },
        ),
    )

    def get_fieldsets(self, request, obj=None):
        return self.FIELDSETS_ALTA if obj is None else self.fieldsets

    def get_prepopulated_fields(self, request, obj=None):
        # El slug no se muestra en el alta —lo arma solo `Producto.save`— y
        # `prepopulated_fields` revienta con un KeyError si apunta a un campo
        # que no está en el formulario.
        if obj is None:
            return {}
        return super().get_prepopulated_fields(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """Al crear, quedarse en la ficha en vez de volver al listado.

        El alta muestra lo mínimo, así que siempre queda algo por completar.
        Volver al listado escondería justo el paso siguiente; acá se cae en la
        ficha completa, que es donde están las fotos y las demás medidas.
        """
        atajos = ("_continue", "_addanother", "_saveasnew", "_popup")
        if any(a in request.POST for a in atajos):
            return super().response_add(request, obj, post_url_continue)

        self.message_user(
            request,
            "«{}» quedó creado y publicado. Abajo podés terminar de armarle la "
            "ficha: más fotos, más medidas y el texto para Google.".format(obj),
        )
        return HttpResponseRedirect(
            reverse("admin:catalogo_producto_change", args=[obj.pk])
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("categoria", "marca").prefetch_related("variantes")

    @admin.display(description="precio")
    def precios(self, obj):
        desde = obj.precio_desde
        if desde is None:
            return format_html('<span style="color:{}">a cotizar</span>', colores.OJO)
        if obj.rango_de_precios:
            return "${:,.0f} a ${:,.0f}".format(desde, obj.precio_hasta).replace(",", ".")
        return "${:,.0f}".format(desde).replace(",", ".")

    @admin.display(description="existencias")
    def existencias(self, obj):
        variantes = obj.variantes_activas
        if not variantes:
            return "—"
        total = sum(v.disponible for v in variantes)
        bajas = [v for v in variantes if v.bajo_stock]
        if total <= 0:
            return format_html('<b style="color:{}">AGOTADO</b>', colores.MAL)
        if bajas:
            return format_html(
                '<b style="color:{}">{} — {} bajo mínimo</b>',
                colores.OJO,
                total,
                len(bajas),
            )
        return format_html('<b style="color:{}">{}</b>', colores.OK, total)

    @admin.display(description="en el sitio", boolean=True)
    def publicado(self, obj):
        return obj.activo and obj.categoria.activa

    def save_formset(self, request, form, formset, change):
        """Las variantes del inline también pasan por inventario."""
        if formset.model is not Variante:
            return super().save_formset(request, form, formset, change)

        formset.save(commit=False)
        for obj in formset.deleted_objects:
            obj.delete()
        for obj, campos in formset.changed_objects:
            _guardar_variante(request, obj, True, campos)
        for obj in formset.new_objects:
            _guardar_variante(request, obj, False, [])
        formset.save_m2m()

    @admin.action(description="Publicar en el sitio")
    def publicar(self, request, queryset):
        n = queryset.update(activo=True)
        self.message_user(request, "{} producto(s) publicado(s).".format(n))

    @admin.action(description="Sacar del sitio")
    def despublicar(self, request, queryset):
        n = queryset.update(activo=False)
        self.message_user(request, "{} producto(s) fuera del sitio.".format(n))

    @admin.action(description="Marcar como destacado")
    def destacar(self, request, queryset):
        n = queryset.update(destacado=True)
        self.message_user(request, "{} producto(s) destacado(s).".format(n))

    @admin.action(description="Quitar de destacados")
    def quitar_destacado(self, request, queryset):
        n = queryset.update(destacado=False)
        self.message_user(request, "{} producto(s) sin destacar.".format(n))


@admin.register(Variante)
class VarianteAdmin(admin.ModelAdmin):
    """La pantalla de inventario: todas las existencias en una sola lista."""

    list_display = ("descripcion_corta", "sku", "costo", "precio", "ganancia", "stock", "reservado", "stock_minimo", "situacion", "activa")
    list_editable = ("costo", "precio", "stock", "stock_minimo", "activa")
    list_filter = (FiltroSituacion, "activa", "producto__categoria", "producto__marca")
    search_fields = ("sku", "nombre", "producto__nombre")
    list_per_page = 60
    list_select_related = ("producto", "producto__categoria")
    readonly_fields = ("reservado", "sku_actual", "creado", "actualizado")

    fieldsets = (
        (None, {"fields": ("producto", "nombre", "sku", "sku_actual", "activa", "orden")}),
        (
            "Plata",
            {
                "fields": ("costo", "precio", "precio_antes"),
                "description": "El costo no sale nunca en la web: es para saber "
                "cuánto te deja cada venta.",
            },
        ),
        (
            "Existencias",
            {
                "fields": ("stock", "stock_minimo", "reservado"),
                "description": "Cambiar las existencias acá deja un ajuste en el "
                "historial de inventario, a tu nombre. Las reservadas las maneja "
                "el sistema con los pedidos: no se editan a mano.",
            },
        ),
        ("Fechas", {"classes": ("collapse",), "fields": ("creado", "actualizado")}),
    )

    @admin.display(description="producto", ordering="producto__nombre")
    def descripcion_corta(self, obj):
        return str(obj)

    @admin.display(description="situación")
    def situacion(self, obj):
        return _pinta_stock(obj)

    @admin.display(description="ganancia")
    def ganancia(self, obj):
        if obj.ganancia is None:
            return format_html(
                '<span style="color:{}">sin costo</span>', colores.APAGADO
            )
        color = colores.OK if obj.ganancia > 0 else colores.MAL
        return format_html(
            '<b style="color:{}">${}</b> <span style="color:{}">{}%</span>',
            color,
            "{:,.0f}".format(obj.ganancia).replace(",", "."),
            colores.APAGADO,
            obj.margen,
        )

    @admin.display(description="SKU generado")
    def sku_actual(self, obj):
        return obj.sku or "se genera al guardar"

    def save_model(self, request, obj, form, change):
        _guardar_variante(request, obj, change, form.changed_data)
