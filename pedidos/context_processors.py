from pedidos.carrito import Carrito


def carrito(request):
    """El contador del carrito, disponible en todas las plantillas."""
    if not hasattr(request, "session"):
        return {}
    bolsa = Carrito(request)
    return {"carrito_unidades": bolsa.unidades, "carrito_lineas": len(bolsa)}
