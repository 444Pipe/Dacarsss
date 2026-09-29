# -*- coding: utf-8 -*-
"""Convierte el Excel del sistema contable en la semilla del catálogo masivo.

El comercio exportó su inventario en un Excel de tres hojas que no se hablan
entre sí:

    INVENTARIO NUEVO PROGRAMA  el inventario real de hoy: ~270 códigos con existencias
    INVENTARIO 1               991 códigos del histórico, con costo y precio
    INVENTARIO 2               660 códigos con categoría (de un sistema anterior)

La hoja que manda es INVENTARIO NUEVO PROGRAMA (confirmado por el comercio):
eso es lo que hay en el local. Las otras dos solo la enriquecen, cruzando por
código: el precio y el costo salen de INVENTARIO 1, la categoría de
INVENTARIO 2. Un código con precio sale con carrito; sin precio sale «a
cotizar» por WhatsApp. Los cientos de códigos que solo viven en el histórico
se quedan afuera: cada uno sería una página sin stock ni foto, y Google
castiga el sitio entero por ese relleno.

Este script produce `catalogo/semillas/inventario.json`, que
`manage.py inventario_masivo` carga en producción durante el arranque del
contenedor.

Se corre en la máquina de trabajo, no en producción (necesita openpyxl y el
Excel local):

    python tools/inventario-a-semillas.py "C:/ruta/al/inventario.xlsx"

El JSON resultante se commitea. Correrlo de nuevo con el mismo Excel produce
el mismo archivo (orden estable), así el diff de git muestra solo lo que
cambió de verdad.
"""

import json
import re
import sys
import unicodedata
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parents[1]
DESTINO = RAIZ / "catalogo" / "semillas" / "inventario.json"

# Códigos que ya existen en el catálogo curado (los 19 con fotos de estudio).
# Importarlos crearía la misma página dos veces, una con foto y otra sin.
YA_CURADOS = {
    "ACC02-134",  # Cámara de reversa tipo domo Hanex HX-CM01
    "ACC02-166",  # CarPlay AI Box Android
    "ACC02-309",  # Cámara para carro Ultra DVR ULT-801
    "ILU04-090",  # Kit iluminación LED ambiente 18 en 1
    "ILU04-154",  # Bombillo LED H4 C12
    "ILU04-172",  # Luz LED para baúl Osram LEDambient
    "ILU04-174",  # Luces decorativas Novotec
    "SEG11-29",   # Alarma de reversa Loyta
}

# La categoría de la hoja 2 manda cuando existe; si no, decide el nombre del
# producto, y si tampoco, el prefijo del código. Los nombres de categoría son
# los mismos del catálogo en producción: el comando hace get_or_create por
# nombre y un typo acá crearía una categoría duplicada.
CATEGORIA_HOJA2 = {
    "ACCESORIOS Y LUJOS": "Lujos y accesorios",
    "ILUIMINACION": "Iluminación",
    "ILUMINACION": "Iluminación",
    "TAPETES": "Tapetes",
    "SONIDO": "Sonido",
    "LLANTAS": "Llantas y rines",
    "SEGUROS ESPEJOS": "Seguridad y parqueo",
    "SISTEMA ELECTRICO": "Lujos y accesorios",
    "CARPA": "Carpas y cubiertas",
    "PLANTAS": "Sonido",  # plantas = amplificadores
    "SEGURIDAD": "Seguridad y parqueo",
    "SEGURIDAD GPS": "Seguridad y parqueo",
    "LIQUIDOS Y AROMAS": "Detailing",
    "LLAVE": "Seguridad y parqueo",
    "PPF": "PPF y protección de pintura",
}

CATEGORIA_PREFIJO = {
    "ACC": "Lujos y accesorios",
    "ILU": "Iluminación",
    "SON": "Sonido",
    "TAP": "Tapetes",
    "LLAN": "Llantas y rines",
    "SEG": "Seguridad y parqueo",
    "CARP": "Carpas y cubiertas",
    "ARO": "Detailing",
    "ELEC": "Lujos y accesorios",
    "PLA": "Sonido",
}

# Señales en el nombre que afinan la categoría: una cámara con código ACC es
# de seguridad, un radio con código SON es multimedia.
POR_NOMBRE = [
    (re.compile(r"\b(TAPETE|TAPETES)\b"), "Tapetes"),
    (re.compile(r"\b(CARPA|CUBIERTA DE PLATON|DURALINER)\b"), "Carpas y cubiertas"),
    (re.compile(r"\b(PITO|ALARMA|SIRENA)\b"), "Pitos y alarmas"),
    (re.compile(r"\b(CAMARA|SENSOR|GPS|BLOQUEO|CHAPA|PIN DE SEGURIDAD|DVR)\b"), "Seguridad y parqueo"),
    (re.compile(r"\b(RADIO|PANTALLA|CARPLAY|ANDROID)\b"), "Multimedia y CarPlay"),
    (re.compile(r"\b(CERA|SHAMPOO|SILICONA|AROMA|AMBIENTADOR|RESTAURADOR|RENOVADOR)\b"), "Detailing"),
    (re.compile(r"\b(LLANTA|LLANTAS|RIN|RINES)\b"), "Llantas y rines"),
]

# Categorías que todavía no existen en producción. Las demás ya están
# sembradas por categorias_iniciales y el comando solo las referencia.
CATEGORIAS_NUEVAS = [
    {
        "nombre": "Tapetes",
        "descripcion": "Tapetes termoformados 5D, 3D y de goma por modelo: Hilux, "
        "Fortuner, Prado, Frontier, Sportage y más. Cubren completo y no se "
        "corren. Envíos a toda Colombia.",
        "servicio": "lujos-y-accesorios-villavicencio",
        "orden": 25,
    },
    {
        "nombre": "Carpas y cubiertas",
        "descripcion": "Carpas planas, duraliner y cubiertas de platón para "
        "camioneta. Instalación en el taller de Villavicencio y envíos a "
        "toda Colombia.",
        "servicio": "accesorios-4x4-villavicencio",
        "orden": 22,
    },
]

# Marcas de producto que aparecen en los nombres. Vehículos aparte: Toyota es
# compatibilidad, no marca de lo que se vende.
MARCAS = {
    "OSRAM": "Osram", "NARVA": "Narva", "PHILIPS": "Philips", "HANEX": "Hanex",
    "LOYTA": "Loyta", "NOVOTEC": "Novotec", "ELEPHANT": "Elephant",
    "SYLVANIA": "Sylvania", "PIONEER": "Pioneer", "SONY": "Sony", "JBL": "JBL",
    "HERTZ": "Hertz", "KICKER": "Kicker", "KIKER": "Kicker", "FOCAL": "Focal",
    "KENWOOD": "Kenwood", "THULE": "Thule", "MEGUIARS": "Meguiar's",
    "3DMAXPIDER": "3D MAXpider", "STIT": "STIT", "AVM": "AVM",
    "JCM": "JCM", "MOURA": "Moura", "AEROKLAS": "Aeroklas",
}

VEHICULOS = {
    "TOYOTA": "Toyota", "HILUX": "Hilux", "FORTUNER": "Fortuner", "PRADO": "Prado",
    "COROLLA": "Corolla", "CAROLLA": "Corolla", "YARIS": "Yaris", "RAV": "RAV4",
    "SW4": "SW4", "REVO": "Revo", "VIGO": "Vigo", "LC": "Land Cruiser",
    "KIA": "Kia", "SPORTAGE": "Sportage", "PICANTO": "Picanto", "CERATO": "Cerato",
    "MAZDA": "Mazda", "CHEVROLET": "Chevrolet", "COLORADO": "Colorado",
    "DMAX": "D-Max", "D-MAX": "D-Max", "ONIX": "Onix", "SPARK": "Spark",
    "FORD": "Ford", "RANGER": "Ranger", "RAPTOR": "Raptor",
    "NISSAN": "Nissan", "FRONTIER": "Frontier", "RENAULT": "Renault",
    "DUSTER": "Duster", "SANDERO": "Sandero", "LOGAN": "Logan",
    "VOLKSWAGEN": "Volkswagen", "AMAROK": "Amarok", "MITSUBISHI": "Mitsubishi",
    "MONTERO": "Montero", "L200": "L200", "HUMMER": "Hummer", "AUDI": "Audi",
    "BMW": "BMW", "HYUNDAI": "Hyundai", "TUCSON": "Tucson", "JIMNY": "Jimny",
    "VITARA": "Vitara", "SUZUKI": "Suzuki", "JEEP": "Jeep", "WRANGLER": "Wrangler",
}

# Siglas y unidades que se quedan como son, aunque el resto pase a minúsculas.
SIGLAS = {
    "LED", "PPF", "GPS", "DVR", "USB", "HD", "AHD", "FHD", "RGB", "SC", "DRL",
    "RCA", "AM", "FM", "TV", "LCD", "APK", "APX", "DCX", "AVM", "UND", "EV",
    "GR", "X2", "X4", "3D", "5D", "2D", "4X4", "12V", "24V", "W5W", "T20",
    "T10", "H1", "H3", "H4", "H7", "H8", "H9", "H11", "H16", "HB3", "HB4",
    "NP-300", "J250", "WA", "D-M", "JLT", "C12",
}


def _sin_tildes(texto):
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


def slugificar(texto):
    limpio = _sin_tildes(texto).lower()
    limpio = re.sub(r"[^a-z0-9]+", "-", limpio).strip("-")
    return limpio[:150] or "producto"


ES_CODIGO = re.compile(r"^(?=.*\d)[A-Z0-9][A-Z0-9./-]{3,}$")
ES_MEDIDA = re.compile(r"^\d[\d./x-]*(V|W|MM|CM|M|K|A|db|DB)?$", re.I)


def limpiar_nombre(crudo):
    """El nombre del sistema contable, vuelto título de página.

    Quita el código interno que algunos traen adelante (ACCA36, B-SC30-H4),
    respeta siglas y medidas, y pone mayúsculas donde van: marcas, vehículos
    y la primera letra.
    """
    nombre = crudo.replace("¨", '"').replace("*", " ")
    nombre = re.sub(r"\s+", " ", nombre).strip()
    palabras = nombre.split(" ")

    # El primer token es un código interno si mezcla letras y números y lo
    # que sigue alcanza para nombrar el producto solo. "3ER STOP" o
    # "H27/2 12V" no se tocan: son parte del nombre.
    if len(palabras) >= 3:
        primero = palabras[0].upper()
        parece_codigo = (
            ES_CODIGO.match(primero)
            and primero not in SIGLAS
            and not ES_MEDIDA.match(primero)
            and not primero.startswith("3ER")
        )
        if parece_codigo or re.match(r"^\d{3,}$", primero):
            palabras = palabras[1:]

    salida = []
    for cruda in palabras:
        p = cruda.upper()
        base = p.strip('()".,')
        if base in SIGLAS or (any(ch.isdigit() for ch in base) and base not in VEHICULOS):
            salida.append(cruda.upper().replace("4X4", "4x4"))
        elif base in MARCAS:
            salida.append(cruda.upper().replace(base, MARCAS[base], 1))
        elif base in VEHICULOS:
            salida.append(cruda.upper().replace(base, VEHICULOS[base], 1))
        else:
            salida.append(cruda.lower())
    resultado = " ".join(salida)
    return resultado[:1].upper() + resultado[1:]


def detectar(nombre_mayuscula, tabla):
    encontrados = []
    for clave, bonito in tabla.items():
        if re.search(r"\b" + re.escape(clave) + r"\b", nombre_mayuscula):
            if bonito not in encontrados:
                encontrados.append(bonito)
    return encontrados


def categoria_de(codigo, nombre_mayuscula, cat_hoja2):
    if cat_hoja2 in CATEGORIA_HOJA2:
        base = CATEGORIA_HOJA2[cat_hoja2]
    else:
        base = ""
    for patron, cat in POR_NOMBRE:
        if patron.search(nombre_mayuscula):
            return cat
    if base:
        return base
    prefijo = re.match(r"[A-Z]+", codigo)
    if prefijo:
        for largo in range(len(prefijo.group(0)), 2, -1):
            if prefijo.group(0)[:largo] in CATEGORIA_PREFIJO:
                return CATEGORIA_PREFIJO[prefijo.group(0)[:largo]]
    return "Lujos y accesorios"


def leer(ruta):
    wb = openpyxl.load_workbook(ruta, data_only=True)
    inv1, cat2, stock3, nombres23 = {}, {}, {}, {}

    for f in wb["INVENTARIO 1"].iter_rows(min_row=2, values_only=True):
        if not f[5]:
            continue
        codigo = str(f[5]).strip().upper()
        inv1[codigo] = {
            "nombre": str(f[4] or "").strip(),
            "referencia": str(f[6] or "").strip(),
            "costo": f[9],
            "precio_base": f[10],
            "precio_total": f[12],
        }

    for f in wb["INVENTARIO 2"].iter_rows(min_row=2, values_only=True):
        if not f[1]:
            continue
        codigo = str(f[1]).strip().upper()
        cat2[codigo] = str(f[2] or "").strip().upper()
        if f[0]:
            nombres23.setdefault(codigo, str(f[0]).strip())

    for f in wb["INVENTARIO NUEVO PROGRAMA"].iter_rows(min_row=2, values_only=True):
        if not f[1]:
            continue
        codigo = str(f[1]).strip().upper()
        try:
            stock3[codigo] = int(float(f[3] or 0))
        except (TypeError, ValueError):
            pass
        nombre = str(f[0] or "").strip()
        if nombre and nombre != ".":
            nombres23.setdefault(codigo, nombre)

    return inv1, cat2, stock3, nombres23


def precio_de(fila):
    for campo in ("precio_total", "precio_base"):
        try:
            valor = float(fila.get(campo) or 0)
        except (TypeError, ValueError):
            continue
        if valor > 0:
            return int(round(valor))
    return 0


def convertir(ruta):
    inv1, cat2, stock3, nombres23 = leer(ruta)

    productos = []
    slugs, skus = set(), set()
    sin_precio = con_precio = 0

    # Solo lo que está en el programa nuevo: ese es el inventario de verdad.
    for codigo in sorted(stock3):
        if codigo in YA_CURADOS:
            continue
        fila = inv1.get(codigo, {})
        precio = precio_de(fila)
        stock = stock3.get(codigo, 0)

        crudo = fila.get("nombre") or nombres23.get(codigo, "")
        if len(crudo) < 4:
            continue
        nombre = limpiar_nombre(crudo)
        mayuscula = _sin_tildes(crudo).upper()

        slug = slugificar(nombre)
        if slug in slugs:
            slug = (slug[:140] + "-" + codigo.lower().replace(" ", ""))[:150]
        if slug in slugs:
            continue  # mismo código dos veces: con uno alcanza
        slugs.add(slug)

        categoria = categoria_de(codigo, mayuscula, cat2.get(codigo, ""))
        marcas = detectar(mayuscula, MARCAS)
        vehiculos = detectar(mayuscula, VEHICULOS)

        if len(nombre) <= 61:
            seo_titulo = nombre + " | DACARS"
        else:
            seo_titulo = nombre[:70]
        seo_descripcion = (
            "Compra {} en DACARS Villavicencio. Envíos a toda Colombia y "
            "asesoría por WhatsApp.".format(nombre)
        )
        if len(seo_descripcion) > 160:
            seo_descripcion = (
                "{} en DACARS Villavicencio. Envíos a toda Colombia.".format(nombre)
            )[:160]

        producto = {
            "codigo": codigo,
            "nombre": nombre,
            "slug": slug,
            "categoria": categoria,
            "seo_titulo": seo_titulo,
            "seo_descripcion": seo_descripcion,
            "instalacion": categoria != "Detailing",
        }
        if marcas:
            producto["marca"] = marcas[0]
        if vehiculos:
            producto["compatibilidad"] = ", ".join(vehiculos[:6])

        if precio > 0:
            sku = (fila.get("referencia") or codigo).upper().replace(" ", "")[:40]
            if sku in skus:
                sku = codigo.replace(" ", "")[:40]
            if sku in skus:
                continue
            skus.add(sku)
            # El costo de compra NO se emite a propósito: el JSON se commitea
            # y el repositorio es público. Publicar costos es publicar los
            # márgenes del negocio. Se cargan después desde el panel.
            producto["variante"] = {"sku": sku, "precio": precio, "stock": max(stock, 0)}
            con_precio += 1
        else:
            sin_precio += 1

        productos.append(producto)

    return {
        "categorias": CATEGORIAS_NUEVAS,
        "productos": productos,
    }, con_precio, sin_precio


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Uso: python tools/inventario-a-semillas.py <inventario.xlsx>")
    datos, con_precio, sin_precio = convertir(sys.argv[1])
    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(
        json.dumps(datos, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print(
        "{} productos ({} con precio y carrito, {} a cotizar) -> {}".format(
            len(datos["productos"]), con_precio, sin_precio, DESTINO
        )
    )


if __name__ == "__main__":
    main()
