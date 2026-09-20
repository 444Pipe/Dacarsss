"""Los colores que el panel pinta desde Python.

Van acá y no sueltos en cada `admin.py` porque tienen que coincidir con los de
`static/css/panel.css`. Son las versiones claras de la paleta: en el panel el
fondo es oscuro, y un rojo #b91c1c sobre #04060c no se lee.
"""

TEXTO = "#e9eef8"
APAGADO = "#6c7a93"

OK = "#3ddc84"      # hay stock, entregado, todo en orden
OJO = "#ffb74d"     # bajo el mínimo, pedido sin responder
MAL = "#ff7a8f"     # agotado, falta cargar algo
AZUL = "#3d8bff"    # informativo, confirmado
