"""El panel que usa el comercio.

Es el admin de Django con dos cambios: la marca DACARS y un tablero de entrada
que muestra lo que hay que atender hoy (stock bajo, pedidos sin responder,
productos a medio cargar). Las alertas se calculan en `each_context`, así
aparecen en todas las pantallas del panel y no solo en el índice: el contador
de pendientes vive en el ítem «Tablero» de la barra lateral, que está siempre
a la vista.

El resumen del mes, en cambio, se calcula en `index`. Son consultas que solo
mira quien entra al tablero, y cobrárselas a cada pantalla del panel —incluidas
las de guardar un formulario— sería pagar de más por un número que nadie está
viendo.

Las fichas de alerta salen de acá armadas (número, título, detalle y color) en
vez de escribirse una por una en la plantilla. Sumar una alerta nueva es
agregar un `_ficha(...)` a la lista; la plantilla no se toca.
"""

from django.contrib import admin
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone


def _ficha(cuantos, titulo, detalle, url, tono):
    return {
        "cuantos": cuantos,
        "titulo": titulo,    # qué es, en dos o tres palabras
        "detalle": detalle,  # por qué importa
        "url": url,
        "tono": tono,        # mal | ojo | neutro
    }


class PanelDacars(admin.AdminSite):
    site_header = "DACARS"
    site_title = "Panel DACARS"
    index_title = "Tablero"
    index_template = "admin/dacars_index.html"

    # El panel trae su propia barra lateral fija. Apagar ésta no es sólo dejar
    # de dibujarla: `admin/base.html` mira esta bandera para decidir si carga
    # nav_sidebar.css y nav_sidebar.js, y esas dos hojas son las que más pelean
    # contra un rail propio (el colapso por `margin-left:-276px`, el
    # `visibility:hidden` que sólo levanta su JS, y un `display:none` en
    # celular). Apagándola no hay nada que neutralizar.
    enable_nav_sidebar = False

    def each_context(self, request):
        contexto = super().each_context(request)
        if not request.user.is_active or not request.user.is_staff:
            return contexto
        contexto["alertas"] = self._alertas(request)
        return contexto

    def index(self, request, extra_context=None):
        extra_context = dict(extra_context or {})
        extra_context["resumen"] = self._resumen()
        return super().index(request, extra_context)

    # -- Lo que hay que atender ---------------------------------------------
    def _alertas(self, request):
        # Import tardío: en tiempo de import de settings las apps todavía no
        # están cargadas.
        from catalogo.models import Producto, Variante
        from pedidos.models import Pedido

        bajas = Variante.bajo_minimo()
        agotadas = [v for v in bajas if v.disponible <= 0]
        # Las agotadas ya están contadas dentro de `bajas`; se separan para que
        # no aparezca la misma variante en dos fichas diciendo cosas distintas.
        por_reponer = len(bajas) - len(agotadas)

        pedidos_nuevos = Pedido.objects.filter(estado=Pedido.NUEVO).count()

        sin_foto = Producto.objects.filter(
            activo=True, imagenes__isnull=True
        ).count()

        lista = reverse("admin:catalogo_variante_changelist")
        productos = reverse("admin:catalogo_producto_changelist")

        fichas = [
            _ficha(
                len(agotadas),
                "Agotadas",
                "Se ven en la web sin poder venderse",
                lista + "?situacion=agotadas",
                "mal",
            ),
            _ficha(
                pedidos_nuevos,
                "Pedidos sin responder",
                "Entraron por la web y siguen esperando",
                reverse("admin:pedidos_pedido_changelist") + "?estado__exact=nuevo",
                "ojo",
            ),
            _ficha(
                por_reponer,
                "Bajo el mínimo",
                "Conviene reponer antes de que se agoten",
                lista + "?situacion=bajas",
                "ojo",
            ),
            _ficha(
                sin_foto,
                "Sin fotos",
                "Se ven pobres en el catálogo de la web",
                productos + "?completitud=sin_foto",
                "neutro",
            ),
        ]
        fichas = [f for f in fichas if f["cuantos"]]

        return {
            "fichas": fichas,
            "pendientes": sum(f["cuantos"] for f in fichas),
            "hay_algo": bool(fichas),
        }

    # -- Cómo viene el mes ---------------------------------------------------
    def _resumen(self):
        from catalogo.models import Producto
        from pedidos.models import Pedido

        hoy = timezone.localdate()
        desde = hoy.replace(day=1)

        # Lo vendido cuenta desde que el pedido se confirma: es el momento en
        # que la mercancía sale del inventario. Los cancelados nunca entran.
        del_mes = Pedido.objects.filter(creado__date__gte=desde)
        vendido = (
            Pedido.objects.filter(
                confirmado_en__date__gte=desde,
                estado__in=[Pedido.CONFIRMADO, Pedido.ENTREGADO],
            ).aggregate(plata=Sum("total"))["plata"]
            or 0
        )

        productos = reverse("admin:catalogo_producto_changelist")
        return [
            {
                "valor": Producto.objects.publicados().count(),
                "rotulo": "publicados en la web",
                "url": productos,
            },
            {
                # Sin variante activa no hay precio y la ficha ofrece cotizar.
                # No es una falla: así se publica hoy casi todo el catálogo, y
                # por eso el número va acá y no entre las alertas.
                "valor": Producto.objects.filter(activo=True)
                .exclude(variantes__activa=True)
                .count(),
                "rotulo": "a cotizar por WhatsApp",
                "url": productos + "?completitud=sin_variante",
            },
            {
                "valor": del_mes.count(),
                "rotulo": "pedidos este mes",
                "url": reverse("admin:pedidos_pedido_changelist"),
            },
            {
                "valor": vendido,
                "rotulo": "vendido este mes",
                "plata": True,
                "url": reverse("admin:pedidos_pedido_changelist"),
            },
        ]
