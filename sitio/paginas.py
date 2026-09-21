"""Las páginas del sitio que no salen de la base de datos.

Son las 10 landings de servicio, el hub del Meta y la portada. El contenido sigue viviendo en
las plantillas (una por página, migradas desde los HTML originales con
`tools/migrar-a-django.py`); esta lista es solo el índice: qué URL sirve qué
plantilla, y con qué prioridad va al sitemap.

Los `.html` del final **no son un descuido**. Son las URLs que Google ya tiene
indexadas y las que apunta el canonical de cada página. Cambiarlas obliga a
redirigir y a esperar semanas de reindexado, a cambio de nada.
"""

SERVICIOS = [
    ("ppf-villavicencio", "PPF"),
    ("polarizados-villavicencio", "Polarizados"),
    ("detailing-villavicencio", "Detailing"),
    ("accesorios-4x4-villavicencio", "Accesorios 4x4"),
    ("lujos-y-accesorios-villavicencio", "Lujos y accesorios"),
    ("iluminacion-para-carros-villavicencio", "Iluminación"),
    ("sonido-para-carros-villavicencio", "Sonido"),
    ("llantas-villavicencio", "Llantas"),
    ("pdr-desabolladura-sin-pintura-villavicencio", "PDR"),
    ("pintura-automotriz-villavicencio", "Pintura"),
]

SLUGS = [slug for slug, _ in SERVICIOS]
NOMBRES = dict(SERVICIOS)

# El hub del departamento. No es un servicio y por eso no entra en la lista
# de arriba: no tiene catálogo propio y no compite por «<servicio> en
# Villavicencio» sino por «lujos para carros en el Meta» y similares, que es
# la búsqueda de quien no vive en la capital y quiere saber si le vale el
# viaje. Tiene vista propia porque tampoco muestra productos.
HUB_META = "personalizacion-de-vehiculos-meta"
