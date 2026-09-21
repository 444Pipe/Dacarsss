# -*- coding: utf-8 -*-
"""Aplica la capa de SEO local a index.html. Idempotente: se puede correr varias veces."""

import io, json, os, re

SITE = "https://www.dacarslujos.com"
HUB_META = "personalizacion-de-vehiculos-meta.html"
WA = "573112629406"
LAT, LON = 4.1420, -73.6340
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IDX = os.path.join(ROOT, "index.html")

KEYWORDS = (
    '<meta name="keywords" content="lujos para carros villavicencio, accesorios para carros villavicencio, '
    'ppf villavicencio, polarizados villavicencio, detailing villavicencio, accesorios 4x4 villavicencio, '
    'autolujos villavicencio, llantas villavicencio, sonido para carros villavicencio, '
    'iluminacion para carros villavicencio, pdr villavicencio, pintura para carros villavicencio, '
    'latoneria y pintura villavicencio, pintura automotriz villavicencio, taller de lujos villavicencio, '
    'personalizacion de vehiculos meta, lujos para carros meta, ppf meta, polarizados meta, '
    'detailing meta, accesorios para carros meta">'
)

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
    ("Pintura automotriz y latonería", "pintura-automotriz-villavicencio"),
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
    ("¿Hacen pintura de carros?",
     "Sí. Hacemos repinte de paneles, pintura general y los trabajos de latonería que el repinte exige, "
     "con igualación de color. Y si el golpe no partió la pintura, te decimos si te sirve más un PDR, "
     "que es más barato y conserva la pintura de fábrica."),
    ("¿Atienden carros de otros municipios del Meta?",
     "Sí. Recibimos vehículos de Acacías, Granada, Restrepo, Cumaral, Puerto López y el resto del "
     "departamento. Escríbenos antes de viajar: agendamos el cupo y pedimos el material para que "
     "hagas un solo viaje."),
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
                        "equipamiento 4x4, PPF (Paint Protection Film), detailing, polarizados, pintura "
                        "automotriz y latonería, iluminación, sonido, llantas y PDR. Atendemos todo el "
                        "departamento del Meta."),
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
        "knowsAbout": [
            "Paint Protection Film", "Polarizado de vidrios automotrices",
            "Detailing automotriz", "Corrección de pintura", "Pintura automotriz",
            "Latonería automotriz", "Desabolladura sin pintura (PDR)",
            "Accesorios 4x4", "Iluminación automotriz LED",
            "Sonido e insonorización automotriz", "Llantas y rines",
        ],
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
            "@type": "WebPage",
            "@id": SITE + "/" + HUB_META + "#pagina",
            "url": SITE + "/" + HUB_META,
            "name": "Personalización de vehículos en el departamento del Meta",
            "description": ("Cobertura de DACARS para los 29 municipios del Meta: distancias, cómo se "
                            "organiza un trabajo cuando el cliente viene de otro municipio y qué "
                            "servicios conviene combinar en un solo viaje."),
            "inLanguage": "es-CO",
            "isPartOf": {"@id": SITE + "/#sitio"},
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
        '<meta name="description" content="Taller de personalización de vehículos en Villavicencio, '
        'Meta: lujos, accesorios 4x4, PPF, detailing, polarizados y pintura. Cotiza por WhatsApp.">',
        html, count=1)

    # Las keywords se reescriben SIEMPRE, no solo al insertar bloque_geo:
    # ese bloque ya existe en index.html desde la primera corrida, asi que
    # ahi dentro la lista habria quedado congelada para siempre.
    html = re.sub(r'<meta name="keywords" content="[^"]*">', lambda _: KEYWORDS,
                  html, count=1)

    # ---------- 2. Metadatos geográficos y de indexación ----------
    bloque_geo = (
        KEYWORDS + '\n'
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
                     "Polarizados", "Iluminación", "Sonido", "Llantas", "PDR",
                     "Pintura"]
        nuevo = partes[0]
        for i, (nombre, slug) in enumerate(SERVICIOS):
            nuevo += ('        <a class="card__mas" href="%s.html">%s en Villavicencio &rarr;</a>\n'
                      '      </article>' % (slug, etiquetas[i])) + partes[i + 1]
        html = nuevo

    # ---------- 5b. Tarjeta de Pintura ----------
    # index.html no se genera, se parchea, asi que la decima tarjeta se inserta
    # aca en vez de a mano: si alguien restaura la portada desde el repositorio,
    # el servicio no se pierde.
    # OJO con la guarda: NO sirve preguntar por "pintura-automotriz-
    # villavicencio.html" a secas, porque el JSON-LD del paso 3 ya escribio esa
    # URL mas arriba y la condicion nunca se cumpliria. Se mira el enlace
    # exacto de la tarjeta.
    MARCA_TARJETA = '<a class="card__mas" href="pintura-automotriz-villavicencio.html">'
    if MARCA_TARJETA not in html:
        tarjeta = """
      <article class="card" data-reveal>
        <span class="card__n">10</span>
        <span class="card__ico">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9.4 8.6h5.2v11.8H9.4z"/><path d="M10.8 8.6V5.4h2.4v3.2"/><path d="M9.4 12.6h5.2"/><path d="M17.4 4.6h2.4M17.4 7.4h2.4M17.4 10.2h2.4"/></svg>
        </span>
        <h3>Pintura &middot; Latonería</h3>
        <p>Repinte de paneles y pintura general con igualación de color. El sol del Llano quema el barniz del techo y el capó, y ahí pulir ya no alcanza.</p>
        <a class="card__mas" href="pintura-automotriz-villavicencio.html">Pintura en Villavicencio &rarr;</a>
      </article>
"""
        ancla = ('        <a class="card__mas" href="pdr-desabolladura-sin-pintura-villavicencio.html">'
                 'PDR en Villavicencio &rarr;</a>\n      </article>\n')
        if ancla in html:
            html = html.replace(ancla, ancla + tarjeta, 1)

    # El texto de la seccion contaba los servicios, asi que tambien sube.
    html = html.replace(
        "Nueve especialidades que normalmente te obligan",
        "Diez especialidades que normalmente te obligan", 1)

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
          antes de venir para tener todo listo cuando llegues.
          <a class="link" href="@@HUB@@">Cómo atendemos al departamento del Meta &rarr;</a></p>
      </div>
    </div>
  </div>
</section>
"""
        seccion = (seccion.replace("@@CHIPS_B@@", chips_b)
                          .replace("@@CHIPS_M@@", chips_m)
                          .replace("@@HUB@@", HUB_META))
        html = html.replace('\n<!-- ============ FAQ ============ -->', seccion +
                            '\n<!-- ============ FAQ ============ -->', 1)
        # Renumerar las etiquetas de las secciones siguientes
        html = html.replace('<p class="tag" data-reveal>06 &mdash; Preguntas</p>',
                            '<p class="tag" data-reveal>07 &mdash; Preguntas</p>', 1)
        html = html.replace('<p class="tag" data-reveal>07 &mdash; Contacto</p>',
                            '<p class="tag" data-reveal>08 &mdash; Contacto</p>', 1)

    # La seccion de cobertura ya existe en index.html desde la primera
    # corrida, asi que el enlace al hub se inyecta aparte o nunca aparecería.
    # Misma trampa que con la tarjeta: HUB_META ya aparece en el JSON-LD.
    if "Cómo atendemos al departamento del Meta" not in html:
        html = html.replace(
            "antes de venir para tener todo listo cuando llegues.</p>",
            'antes de venir para tener todo listo cuando llegues.\n'
            '          <a class="link" href="' + HUB_META + '">'
            'Cómo atendemos al departamento del Meta &rarr;</a></p>', 1)

    # ---------- 7. Navegación: enlace a cobertura ----------
    html = html.replace('      <a href="#nosotros">Nosotros</a>\n      <a href="#contacto">Contacto</a>',
                        '      <a href="#nosotros">Nosotros</a>\n'
                        '      <a href="#cobertura">Cobertura</a>\n'
                        '      <a href="#contacto">Contacto</a>', 1)

    # ---------- 8. Footer con enlaces a las páginas de servicio ----------
    # Las dos columnas de enlaces del pie se reescriben ENTERAS con una
    # expresion regular, no por reemplazo de texto exacto. Antes se buscaba el
    # HTML original palabra por palabra, asi que en cuanto el parche corria una
    # vez dejaba de encontrarse: sumar un servicio obligaba a editar index.html
    # a mano. Asi el pie siempre queda como dice esta lista.
    col_servicios = """<nav class="foot__col" aria-label="Servicios">
      <h4>Servicios</h4>
      <a href="lujos-y-accesorios-villavicencio.html">Lujos y accesorios en Villavicencio</a>
      <a href="accesorios-4x4-villavicencio.html">Accesorios 4x4 en Villavicencio</a>
      <a href="ppf-villavicencio.html">PPF en Villavicencio</a>
      <a href="detailing-villavicencio.html">Detailing en Villavicencio</a>
      <a href="polarizados-villavicencio.html">Polarizados en Villavicencio</a>
      <a href="pintura-automotriz-villavicencio.html">Pintura y latonería en Villavicencio</a>
      <a href="pdr-desabolladura-sin-pintura-villavicencio.html">PDR en Villavicencio</a>
    </nav>"""

    col_mas = """<nav class="foot__col" aria-label="Más servicios">
      <h4>También</h4>
      <a href="iluminacion-para-carros-villavicencio.html">Iluminación para carros</a>
      <a href="sonido-para-carros-villavicencio.html">Sonido para carros</a>
      <a href="llantas-villavicencio.html">Llantas</a>
      <a href=\"""" + HUB_META + """\">Cobertura en todo el Meta</a>
      <a href="#nosotros">Nosotros</a>
      <a href="#faq">Preguntas frecuentes</a>
    </nav>"""

    html = re.sub(r'<nav class="foot__col" aria-label="Servicios">.*?</nav>',
                  lambda _: col_servicios, html, count=1, flags=re.S)
    html = re.sub(r'<nav class="foot__col" aria-label="(?:Empresa|Más servicios)">.*?</nav>',
                  lambda _: col_mas, html, count=1, flags=re.S)

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
             "        la vía al Llano, <strong>pintura</strong> para el techo que ya se descascaró o\n"
             "        <strong>accesorios 4x4</strong> para salir a trocha, este es el taller. Y si vienes de\n"
             "        otro municipio, mira cómo organizamos la visita para\n"
             '        <a class="link" href="' + HUB_META + '">todo el departamento del Meta</a>.\n'
             "      </p>")
    if extra not in html:
        html = html.replace(ancla, extra, 1)

    io.open(IDX, "w", encoding="utf-8", newline="\n").write(html)
    print("index.html actualizado con la capa de SEO local.")


if __name__ == "__main__":
    main()
