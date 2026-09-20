# -*- coding: utf-8 -*-
"""Aplica la capa de SEO local a index.html. Idempotente: se puede correr varias veces."""

import io, json, os, re

SITE = "https://www.dacars.com.co"
WA = "573112629406"
LAT, LON = 4.1420, -73.6340
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "index.html")

BARRIOS = ["San Francisco", "Barzal", "Centro", "Siete de Agosto", "La Esperanza",
           "Ciudad Porfía", "Catumare", "El Buque", "Villa Bolívar", "La Rosita",
           "Los Centauros", "Balcones de Toledo", "Maizaro", "San Fernando",
           "Las Colinas", "Nueva Andalucía", "Camoa", "Montecarlo",
           "Las Américas", "Playa Rica", "El Refugio", "La Vega"]

MUNICIPIOS = ["Acacías", "Restrepo", "Cumaral", "Granada", "Puerto López",
              "San Martín", "Guamal", "Castilla la Nueva", "San Carlos de Guaroa",
              "Barranca de Upía", "Puerto Gaitán", "Fuente de Oro"]

SERVICIOS = [
    ("Lujos y accesorios para vehículos", "lujos-y-accesorios-villavicencio"),
    ("Accesorios y equipamiento 4x4", "accesorios-4x4-villavicencio"),
    ("PPF - Paint Protection Film", "ppf-villavicencio"),
    ("Detailing automotriz", "detailing-villavicencio"),
    ("Polarizado de vidrios", "polarizados-villavicencio"),
    ("Iluminación automotriz", "iluminacion-para-carros-villavicencio"),
    ("Sonido e insonorización", "sonido-para-carros-villavicencio"),
    ("Llantas y montaje", "llantas-villavicencio"),
    ("PDR - Desabolladura sin pintura", "pdr-desabolladura-sin-pintura-villavicencio"),
]

# Preguntas de la portada -> FAQPage
FAQ = [
    ("¿Necesito agendar cita?",
     "Es lo ideal, sobre todo para PPF, detailing y trabajos que ocupan el carro varias horas. Escríbenos por WhatsApp con la marca, el modelo y el servicio que buscas, y te damos disponibilidad."),
    ("¿Cuánto tarda un polarizado o un PPF?",
     "Depende del vehículo, del número de paneles y del tipo de lámina. Al cotizar te confirmamos el tiempo exacto para que organices tu día sin quedarte sin carro a mitad de semana."),
    ("¿El PPF daña la pintura al retirarlo?",
     "No. Se instala sobre el barniz de fábrica y está diseñado para removerse sin arrancar pintura, siempre que la instalación y el retiro se hagan de forma profesional."),
    ("¿Trabajan camionetas y vehículos 4x4?",
     "Sí, y es una parte grande de lo que hacemos: snorkel, bumpers, winches, canastillas, protectores, iluminación auxiliar y llantas para uso mixto entre ciudad y trocha."),
    ("¿Dónde queda DACARS en Villavicencio?",
     "En la Carrera 33 #24-60, Barrio San Francisco, Villavicencio, Meta. Para confirmar el horario de atención del día, escríbenos por WhatsApp al 311 262 9406."),
    ("¿Puedo llevar mis propios accesorios para que los instalen?",
     "Cuéntanos qué tienes y lo revisamos. Si la pieza es compatible y está en buen estado, coordinamos la instalación; si vemos un riesgo para el vehículo, te lo decimos antes de montarla."),
]

# Videos publicados en la portada.
# OJO: falta "uploadDate". Google lo exige para mostrar resultados enriquecidos
# de video. Cuando tengas la fecha real de publicacion de cada reel en Instagram,
# agregala aqui como "uploadDate": "2025-08-14" y vuelve a correr el script.
VIDEOS = [
    ("reel-ppf-sportage", "Full PPF mate en un Kia Sportage 2025",
     "Instalacion de PPF mate completo sobre un Kia Sportage 2025 en el taller "
     "de DACARS en Villavicencio, Meta.", "PT36S"),
    ("reel-led-4x4", "Exploradoras LED para camioneta 4x4",
     "Montaje de exploradoras LED SC para camioneta 4x4 en DACARS Villavicencio.", "PT34S"),
    ("reel-hummer-ev", "Hummer EV: barra LED, faros y rines",
     "Personalizacion de una Hummer EV en Villavicencio: barra LED, faros e "
     "iluminacion delantera y rines.", "PT55S"),
    ("reel-volante-gr", "Volante deportivo en fibra de carbono",
     "Instalacion de un volante deportivo GR en fibra de carbono sobre Toyota, "
     "en DACARS Villavicencio.", "PT44S"),
    ("reel-testimonio-cubierta", "Testimonio de cliente: cubierta de platon",
     "Un cliente de DACARS Villavicencio cuenta como quedo la cubierta de platon "
     "instalada en su camioneta.", "PT1M3S"),
]


DIRECCION = {
    "@type": "PostalAddress",
    "streetAddress": "Carrera 33 #24-60, Barrio San Francisco",
    "addressLocality": "Villavicencio",
    "addressRegion": "Meta",
    "postalCode": "500001",
    "addressCountry": "CO",
}


def build_jsonld():
    negocio = {
        "@type": ["AutoPartsStore", "AutoRepair"],
        "@id": SITE + "/#dacars",
        "name": "DACARS",
        "alternateName": ["Dacars Lujos Villavicencio", "DACARS VILLAVICENCIO S.A.S", "Dacars Accesorios"],
        "legalName": "DACARS VILLAVICENCIO S.A.S",
        "taxID": "901798060",
        "slogan": "Especialistas en personalización de vehículos",
        "description": ("Taller de personalización de vehículos en Villavicencio, Meta. Lujos y accesorios, "
                        "equipamiento 4x4, PPF (Paint Protection Film), detailing, polarizados, iluminación, "
                        "sonido, llantas y PDR."),
        "url": SITE + "/",
        "telephone": "+" + WA,
        "image": [SITE + "/statics/og-image.jpg", SITE + "/statics/logo-dacars.png"],
        "logo": {"@type": "ImageObject", "url": SITE + "/statics/logo-dacars.png",
                 "width": 1000, "height": 729},
        "priceRange": "$$",
        "currenciesAccepted": "COP",
        "paymentAccepted": "Efectivo, Transferencia, Tarjeta",
        "address": DIRECCION,
        "geo": {"@type": "GeoCoordinates", "latitude": LAT, "longitude": LON},
        "hasMap": ("https://www.google.com/maps/search/?api=1&query="
                   "Carrera+33+%2324-60+Barrio+San+Francisco+Villavicencio+Meta"),
        "areaServed": (
            [{"@type": "City", "name": "Villavicencio", "containedInPlace":
              {"@type": "AdministrativeArea", "name": "Meta, Colombia"}}]
            + [{"@type": "City", "name": m} for m in MUNICIPIOS]
            + [{"@type": "AdministrativeArea", "name": "Departamento del Meta"}]
        ),
        "serviceArea": {
            "@type": "GeoCircle",
            "geoMidpoint": {"@type": "GeoCoordinates", "latitude": LAT, "longitude": LON},
            "geoRadius": "80000",
        },
        "knowsLanguage": "es-CO",
        "sameAs": [
            "https://www.instagram.com/dacarslujosvillavicencio/",
            "https://www.instagram.com/dacars.accesorios/",
            "https://www.instagram.com/dacarslujos/",
            "https://www.facebook.com/Dacars.accesorios/",
        ],
        "contactPoint": {
            "@type": "ContactPoint",
            "contactType": "customer service",
            "telephone": "+" + WA,
            "availableLanguage": "Spanish",
            "areaServed": "CO",
        },
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": "Servicios DACARS en Villavicencio",
            "itemListElement": [
                {"@type": "Offer",
                 "itemOffered": {
                     "@type": "Service",
                     "name": nombre,
                     "url": SITE + "/" + slug + ".html",
                     "areaServed": {"@type": "City", "name": "Villavicencio"},
                     "provider": {"@id": SITE + "/#dacars"},
                 }}
                for nombre, slug in SERVICIOS
            ],
        },
    }

    graph = [
        negocio,
        {
            "@type": "Organization",
            "@id": SITE + "/#organizacion",
            "name": "DACARS VILLAVICENCIO S.A.S",
            "url": SITE + "/",
            "logo": {"@type": "ImageObject", "url": SITE + "/statics/logo-dacars.png"},
            "taxID": "901798060",
            "address": DIRECCION,
            "sameAs": negocio["sameAs"],
        },
        {
            "@type": "WebSite",
            "@id": SITE + "/#sitio",
            "url": SITE + "/",
            "name": "DACARS Villavicencio",
            "description": "Personalización de vehículos en Villavicencio, Meta.",
            "inLanguage": "es-CO",
            "publisher": {"@id": SITE + "/#organizacion"},
        },
        {
            "@type": "WebPage",
            "@id": SITE + "/#pagina",
            "url": SITE + "/",
            "name": "DACARS | Lujos, Accesorios 4x4, PPF, Detailing y Polarizados en Villavicencio",
            "description": ("Taller de personalización de vehículos en Villavicencio, Meta. "
                            "Lujos, accesorios 4x4, PPF, detailing, polarizados, iluminación, "
                            "sonido, llantas y PDR."),
            "inLanguage": "es-CO",
            "isPartOf": {"@id": SITE + "/#sitio"},
            "about": {"@id": SITE + "/#dacars"},
            "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + "/statics/og-image.jpg"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": SITE + "/#migas",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"}
            ],
        },
        {
            "@type": "ItemList",
            "@id": SITE + "/#listaservicios",
            "name": "Servicios de DACARS en Villavicencio",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": nombre,
                 "url": SITE + "/" + slug + ".html"}
                for i, (nombre, slug) in enumerate(SERVICIOS)
            ],
        },
        {
            "@type": "ItemList",
            "@id": SITE + "/#listavideos",
            "name": "Videos de trabajos de DACARS en Villavicencio",
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "item": {
                     "@type": "VideoObject",
                     "@id": SITE + "/#video-" + slug,
                     "name": nombre,
                     "description": desc,
                     "duration": dur,
                     "thumbnailUrl": SITE + "/statics/video/" + slug + ".jpg",
                     "contentUrl": SITE + "/statics/video/" + slug + ".mp4",
                     "inLanguage": "es-CO",
                     "isFamilyFriendly": True,
                     "publisher": {"@id": SITE + "/#organizacion"},
                     "locationCreated": {"@type": "Place", "address": DIRECCION},
                 }}
                for i, (slug, nombre, desc, dur) in enumerate(VIDEOS)
            ],
        },
        {
            "@type": "FAQPage",
            "@id": SITE + "/#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in FAQ
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, indent=2)


def main():
    html = io.open(IDX, encoding="utf-8").read()

    # ---------- 1. Head: título y descripción orientados a búsqueda local ----------
    html = html.replace(
        "<title>DACARS | Lujos, Accesorios 4x4, PPF, Detailing y Polarizados en Villavicencio</title>",
        "<title>Lujos, PPF, Polarizados y Detailing en Villavicencio | DACARS</title>")
    html = re.sub(
        r'<meta name="description" content="[^"]*">',
        '<meta name="description" content="Taller de personalización de vehículos en Villavicencio, Meta. '
        'Lujos y accesorios 4x4, PPF, detailing, polarizados, iluminación, sonido, llantas y PDR. '
        'Cra. 33 #24-60, Barrio San Francisco. Cotiza por WhatsApp.">',
        html, count=1)

    # ---------- 2. Metadatos geográficos y de indexación ----------
    bloque_geo = (
        '<meta name="keywords" content="lujos para carros villavicencio, accesorios para carros villavicencio, '
        'ppf villavicencio, polarizados villavicencio, detailing villavicencio, accesorios 4x4 villavicencio, '
        'autolujos villavicencio, llantas villavicencio, sonido para carros villavicencio, '
        'iluminacion para carros villavicencio, pdr villavicencio, personalizacion de vehiculos meta, '
        'taller de lujos villavicencio">\n'
        '<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">\n'
        '<meta name="googlebot" content="index, follow">\n'
        '\n'
        '<!-- Geolocalización para búsqueda local -->\n'
        '<meta name="geo.region" content="CO-MET">\n'
        '<meta name="geo.placename" content="Villavicencio, Meta, Colombia">\n'
        f'<meta name="geo.position" content="{LAT};{LON}">\n'
        f'<meta name="ICBM" content="{LAT}, {LON}">\n'
        '<meta name="DC.title" content="DACARS — Personalización de vehículos en Villavicencio">\n'
        '<meta name="DC.coverage" content="Villavicencio, Meta, Colombia">\n'
        '\n'
        '<link rel="alternate" hreflang="es-co" href="' + SITE + '/">\n'
        '<link rel="alternate" hreflang="x-default" href="' + SITE + '/">\n'
    )
    if 'name="geo.region"' not in html:
        html = html.replace('<link rel="canonical" href="' + SITE + '/">',
                            '<link rel="canonical" href="' + SITE + '/">\n' + bloque_geo, 1)

    # Dimensiones y alt de la imagen social
    if 'og:image:width' not in html:
        html = html.replace(
            '<meta property="og:image" content="' + SITE + '/statics/og-image.jpg">',
            '<meta property="og:image" content="' + SITE + '/statics/og-image.jpg">\n'
            '<meta property="og:image:width" content="1200">\n'
            '<meta property="og:image:height" content="630">\n'
            '<meta property="og:image:alt" content="DACARS — personalización de vehículos en Villavicencio, Meta">',
            1)

    # Manifest
    if 'manifest.webmanifest' not in html:
        html = html.replace(
            '<link rel="apple-touch-icon" href="statics/logo-dacars-sm.png">',
            '<link rel="apple-touch-icon" href="statics/logo-dacars-sm.png">\n'
            '<link rel="manifest" href="manifest.webmanifest">', 1)

    # ---------- 3. JSON-LD completo ----------
    html = re.sub(r'<script type="application/ld\+json">.*?</script>',
                  '<script type="application/ld+json">\n' + build_jsonld() + '\n</script>',
                  html, count=1, flags=re.S)

    # ---------- 4. H1 con la palabra clave local ----------
    viejo_h1 = """    <p class="eyebrow" data-reveal>Villavicencio &middot; Meta <span class="dot"></span> Especialistas en personalización de vehículos</p>

    <h1 class="hero__title" data-reveal>
      <span class="chrome">Tu carro</span><br>
      <span class="chrome">con carácter</span>
      <em class="hero__accent">propio.</em>
    </h1>"""
    nuevo_h1 = """    <p class="eyebrow" data-reveal>Villavicencio &middot; Meta <span class="dot"></span> Tu carro con carácter propio</p>

    <h1 class="hero__title" data-reveal>
      <span class="chrome">Personalización</span><br>
      <span class="chrome">de vehículos en</span>
      <em class="hero__accent">Villavicencio</em>
    </h1>"""
    html = html.replace(viejo_h1, nuevo_h1, 1)

    # ---------- 5. Enlaces internos desde las tarjetas de servicio ----------
    # Inserción ordenada: cada </article> de .cards recibe su enlace
    partes = html.split("      </article>")
    if len(partes) == len(SERVICIOS) + 1 and 'class="card__mas"' not in html:
        etiquetas = ["Lujos y accesorios", "Accesorios 4x4", "PPF", "Detailing",
                     "Polarizados", "Iluminación", "Sonido", "Llantas", "PDR"]
        nuevo = partes[0]
        for i, (nombre, slug) in enumerate(SERVICIOS):
            nuevo += ('        <a class="card__mas" href="%s.html">%s en Villavicencio &rarr;</a>\n'
                      '      </article>' % (slug, etiquetas[i])) + partes[i + 1]
        html = nuevo

    # ---------- 6. Sección de cobertura ----------
    if 'id="cobertura"' not in html:
        chips_b = "\n".join('            <li>%s</li>' % b for b in BARRIOS)
        chips_m = "\n".join('            <li>%s</li>' % m for m in MUNICIPIOS)
        seccion = """
<!-- ============ COBERTURA ============ -->
<section class="sec" id="cobertura">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>06 &mdash; Cobertura</p>
      <h2 class="sec__title chrome" data-reveal>Dónde atendemos en Villavicencio y el Meta</h2>
      <p class="sec__lead" data-reveal>El taller queda en la <strong>Carrera 33 #24-60, Barrio San Francisco</strong>,
        a pocos minutos de buena parte de la ciudad. Si vienes de otro municipio, escríbenos antes de viajar
        y coordinamos la cita para que aproveches el desplazamiento.</p>
    </header>

    <div class="cobertura">
      <div class="cobertura__col" data-reveal>
        <h3>Barrios y zonas de Villavicencio</h3>
        <ul class="chips">
@@CHIPS_B@@
        </ul>
        <p class="cobertura__nota">Y el resto de la ciudad: si no ves tu barrio, igual te atendemos.</p>
      </div>

      <div class="cobertura__col" data-reveal>
        <h3>Municipios del Meta</h3>
        <ul class="chips">
@@CHIPS_M@@
        </ul>
        <p class="cobertura__nota">Recibimos vehículos de toda la región. Agenda por WhatsApp
          antes de venir para tener todo listo cuando llegues.</p>
      </div>
    </div>
  </div>
</section>
"""
        seccion = seccion.replace("@@CHIPS_B@@", chips_b).replace("@@CHIPS_M@@", chips_m)
        html = html.replace('\n<!-- ============ FAQ ============ -->', seccion +
                            '\n<!-- ============ FAQ ============ -->', 1)
        # Renumerar las etiquetas de las secciones siguientes
        html = html.replace('<p class="tag" data-reveal>06 &mdash; Preguntas</p>',
                            '<p class="tag" data-reveal>07 &mdash; Preguntas</p>', 1)
        html = html.replace('<p class="tag" data-reveal>07 &mdash; Contacto</p>',
                            '<p class="tag" data-reveal>08 &mdash; Contacto</p>', 1)

    # ---------- 7. Navegación: enlace a cobertura ----------
    html = html.replace('      <a href="#nosotros">Nosotros</a>\n      <a href="#contacto">Contacto</a>',
                        '      <a href="#nosotros">Nosotros</a>\n'
                        '      <a href="#cobertura">Cobertura</a>\n'
                        '      <a href="#contacto">Contacto</a>', 1)

    # ---------- 8. Footer con enlaces a las páginas de servicio ----------
    viejo_foot = """      <a href="#servicios">Lujos y accesorios</a>
      <a href="#servicios">Accesorios 4x4</a>
      <a href="#ppf">PPF</a>
      <a href="#servicios">Detailing</a>
      <a href="#servicios">Polarizados</a>
      <a href="#servicios">Iluminación y sonido</a>"""
    nuevo_foot = """      <a href="lujos-y-accesorios-villavicencio.html">Lujos y accesorios en Villavicencio</a>
      <a href="accesorios-4x4-villavicencio.html">Accesorios 4x4 en Villavicencio</a>
      <a href="ppf-villavicencio.html">PPF en Villavicencio</a>
      <a href="detailing-villavicencio.html">Detailing en Villavicencio</a>
      <a href="polarizados-villavicencio.html">Polarizados en Villavicencio</a>
      <a href="pdr-desabolladura-sin-pintura-villavicencio.html">PDR en Villavicencio</a>"""
    html = html.replace(viejo_foot, nuevo_foot, 1)

    viejo_emp = """      <a href="#nosotros">Nosotros</a>
      <a href="#proceso">Cómo trabajamos</a>
      <a href="#trabajos">Trabajos</a>
      <a href="#faq">Preguntas frecuentes</a>
      <a href="#contacto">Contacto</a>"""
    nuevo_emp = """      <a href="iluminacion-para-carros-villavicencio.html">Iluminación para carros</a>
      <a href="sonido-para-carros-villavicencio.html">Sonido para carros</a>
      <a href="llantas-villavicencio.html">Llantas</a>
      <a href="#nosotros">Nosotros</a>
      <a href="#cobertura">Cobertura</a>
      <a href="#faq">Preguntas frecuentes</a>"""
    html = html.replace(viejo_emp, nuevo_emp, 1)
    html = html.replace('<nav class="foot__col" aria-label="Empresa">\n      <h4>Empresa</h4>',
                        '<nav class="foot__col" aria-label="Más servicios">\n      <h4>También</h4>', 1)

    # ---------- 9. Alt de imágenes con contexto local ----------
    html = html.replace('alt="DACARS" width="600" height="117"',
                        'alt="DACARS Villavicencio — lujos y accesorios para vehículos" width="600" height="117"')
    html = html.replace('alt="Logotipo DACARS"',
                        'alt="Logotipo DACARS, taller de personalización de vehículos en Villavicencio"')
    html = html.replace('alt="DACARS" width="420" height="306"',
                        'alt="DACARS — Villavicencio, Meta" width="420" height="306"')
    reemplazos_gal = [
        ('alt="Vehículo con PPF instalado por DACARS"',
         'alt="PPF instalado en Villavicencio por DACARS"'),
        ('alt="Polarizado profesional de vidrios"',
         'alt="Polarizado de vidrios en Villavicencio — DACARS"'),
        ('alt="Camioneta con equipamiento 4x4"',
         'alt="Camioneta con accesorios 4x4 en Villavicencio — DACARS"'),
        ('alt="Proceso de detailing y pulimento"',
         'alt="Detailing y pulimento de carro en Villavicencio — DACARS"'),
        ('alt="Iluminación LED instalada en vehículo"',
         'alt="Iluminación LED para carro instalada en Villavicencio — DACARS"'),
        ('alt="Accesorios y lujos instalados"',
         'alt="Lujos y accesorios para carros en Villavicencio — DACARS"'),
    ]
    for viejo, nuevo in reemplazos_gal:
        html = html.replace(viejo, nuevo)

    # ---------- 10. Párrafo con contexto local en «Nosotros» ----------
    ancla = "a conductores de toda la ciudad y del Meta.\n      </p>"
    extra = ("a conductores de toda la ciudad y del Meta.\n      </p>\n"
             '      <p class="sec__lead" data-reveal>\n'
             "        Si estás buscando <strong>lujos para carros en Villavicencio</strong>, un\n"
             "        <strong>polarizado</strong> que no se llene de burbujas, <strong>PPF</strong> que aguante\n"
             "        la vía al Llano o <strong>accesorios 4x4</strong> para salir a trocha, este es el taller.\n"
             "      </p>")
    if extra not in html:
        html = html.replace(ancla, extra, 1)

    io.open(IDX, "w", encoding="utf-8", newline="\n").write(html)
    print("index.html actualizado con la capa de SEO local.")


if __name__ == "__main__":
    main()
