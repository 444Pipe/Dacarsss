"""El carrito, guardado en la sesión.

No hay cuentas de usuario para los clientes, así que el carrito vive en la
sesión (tabla `django_session`, dos semanas). Se guarda solo el SKU y la
cantidad: el precio se vuelve a leer de la base en cada vista. Guardar el
precio en la sesión sería una invitación a que alguien lo edite desde el
navegador.
"""

from decimal import Decimal

from catalogo.models import Variante

CLAVE = "carrito"

# Tope por línea. No es una regla de negocio, es un freno: si alguien pide 400
# llantas, es un error de tipeo o una broma, y conviene que lo hable con el
# taller antes de que el sistema le reserve el inventario entero.
TOPE = 20


class Carrito:
    def __init__(self, request):
        self.sesion = request.session
        self.items = self.sesion.setdefault(CLAVE, {})

    # -- Escritura ----------------------------------------------------------
    def agregar(self, variante, cantidad=1, reemplazar=False):
        sku = variante.sku
        actual = self.items.get(sku, 0)
        nueva = cantidad if reemplazar else actual + cantidad
        nueva = max(1, min(nueva, TOPE, variante.disponible))
        self.items[sku] = nueva
        self._guardar()
        return nueva

    def quitar(self, sku):
        if sku in self.items:
            del self.items[sku]
            self._guardar()

    def vaciar(self):
        self.sesion[CLAVE] = {}
        self.items = self.sesion[CLAVE]
        self._guardar()

    def _guardar(self):
        self.sesion[CLAVE] = self.items
        self.sesion.modified = True

    # -- Lectura ------------------------------------------------------------
    def lineas(self):
        """Las líneas con los datos frescos de la base.

        De paso hace la limpieza: lo que se dio de baja o se quedó sin stock
        sale del carrito y se avisa. Es preferible que el cliente se entere
        acá y no después de dejar sus datos.
        """
        if not self.items:
            return [], []

        variantes = {
            v.sku: v
            for v in Variante.objects.filter(sku__in=list(self.items))
            .select_related("producto", "producto__categoria")
            .prefetch_related("producto__imagenes")
        }

        lineas, avisos = [], []
        cambio = False

        for sku, cantidad in list(self.items.items()):
            variante = variantes.get(sku)
            if variante is None or not variante.activa or not variante.producto.activo:
                del self.items[sku]
                cambio = True
                avisos.append("Sacamos un producto del carrito: ya no está disponible.")
                continue
            if variante.disponible <= 0:
                del self.items[sku]
                cambio = True
                avisos.append("{} se agotó, lo sacamos del carrito.".format(variante))
                continue
            if cantidad > variante.disponible:
                cantidad = variante.disponible
                self.items[sku] = cantidad
                cambio = True
                avisos.append(
                    "De {} quedan {}. Ajustamos la cantidad.".format(
                        variante, variante.disponible
                    )
                )
            lineas.append(
                {
                    "variante": variante,
                    "producto": variante.producto,
                    "cantidad": cantidad,
                    "precio": variante.precio,
                    "subtotal": variante.precio * cantidad,
                }
            )

        if cambio:
            self._guardar()
        return lineas, avisos

    @property
    def total(self):
        lineas, _ = self.lineas()
        return sum((l["subtotal"] for l in lineas), Decimal(0))

    @property
    def unidades(self):
        return sum(self.items.values())

    def __len__(self):
        return len(self.items)

    def __bool__(self):
        return bool(self.items)
