"""Las páginas del sitio que no salen de la base de datos.

Son las 9 landings de servicio más la portada. El contenido sigue viviendo en
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
]

SLUGS = [slug for slug, _ in SERVICIOS]
NOMBRES = dict(SERVICIOS)
