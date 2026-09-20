"""El panel que usa el comercio.

Es el admin de Django con dos cambios: la marca DACARS y un tablero de entrada
que muestra lo que hay que atender hoy (stock bajo, pedidos sin responder,
productos a medio cargar). Las alertas se calculan acá, en `each_context`, así
aparecen en el encabezado de todas las pantallas del panel y no solo en el
índice.
"""

from django.contrib import admin
from django.urls import reverse


class PanelDacars(admin.AdminSite):
    site_header = "DACARS"
    site_title = "Panel DACARS"
    index_title = "Qué hay para hoy"
    index_template = "admin/dacars_index.html"
    enable_nav_sidebar = True

    def each_context(self, request):
        contexto = super().each_context(request)
        if not request.user.is_active or not request.user.is_staff:
            return contexto
        contexto["alertas"] = self._alertas(request)
        return contexto

    def _alertas(self, request):
        # Import tardío: en tiempo de import de settings las apps todavía no
        # están cargadas.
        from catalogo.models import Producto, Variante
        from pedidos.models import Pedido

        bajas = Variante.bajo_minimo()
        agotadas = [v for v in bajas if v.disponible <= 0]
        pedidos_nuevos = Pedido.objects.filter(estado=Pedido.NUEVO).count()
        sin_foto = Producto.objects.filter(activo=True, imagenes__isnull=True).count()
        sin_variante = Producto.objects.filter(activo=True, variantes__isnull=True).count()

        return {
            "stock_bajo": len(bajas),
            "agotadas": len(agotadas),
            "pedidos_nuevos": pedidos_nuevos,
            "sin_foto": sin_foto,
            "sin_variante": sin_variante,
            "url_stock_bajo": (
                reverse("admin:catalogo_variante_changelist") + "?situacion=bajas"
            ),
            "url_agotadas": (
                reverse("admin:catalogo_variante_changelist") + "?situacion=agotadas"
            ),
            "url_pedidos": (
                reverse("admin:pedidos_pedido_changelist") + "?estado__exact=nuevo"
            ),
            "url_sin_foto": (
                reverse("admin:catalogo_producto_changelist") + "?completitud=sin_foto"
            ),
            "url_sin_variante": (
                reverse("admin:catalogo_producto_changelist") + "?completitud=sin_variante"
            ),
            "hay_algo": bool(bajas or pedidos_nuevos or sin_foto or sin_variante),
        }
