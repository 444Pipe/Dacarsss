"""Las páginas del sitio que no salen de la base de datos.

Son las 12 landings de servicio, el hub del Meta y la portada. El contenido sigue viviendo en
las plantillas (una por página, migradas desde los HTML originales con
`tools/migrar-a-django.py`); esta lista es solo el índice: qué URL sirve qué
plantilla, y con qué prioridad va al sitemap.

Cada página se sirve en /<slug>, sin extensión. Hasta septiembre de 2026 las
URLs terminaban en `.html`; esas direcciones siguen respondiendo con un 301 a
la limpia, así que un slug de esta lista **no se renombra**: cambiarlo rompe
las dos URLs a la vez, la nueva y la vieja que redirige a ella.
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
    ("latoneria-villavicencio", "Latonería"),
    ("pintura-automotriz-villavicencio", "Pintura"),
    ("kits-de-actualizacion-villavicencio", "Kits de actualización"),
]

SLUGS = [slug for slug, _ in SERVICIOS]
NOMBRES = dict(SERVICIOS)

# El hub del departamento. No es un servicio y por eso no entra en la lista
# de arriba: no tiene catálogo propio y no compite por «<servicio> en
# Villavicencio» sino por «lujos para carros en el Meta» y similares, que es
# la búsqueda de quien no vive en la capital y quiere saber si le vale el
# viaje. Tiene vista propia porque tampoco muestra productos.
HUB_META = "personalizacion-de-vehiculos-meta"
