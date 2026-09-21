# -*- coding: utf-8 -*-
"""
Genera el hub departamental: personalizacion-de-vehiculos-meta.html

Por que existe una pagina aparte y no basta con nombrar al Meta en las
landings: las 10 landings compiten por «<servicio> en Villavicencio», que es
una busqueda de ciudad. «lujos para carros en el Meta», «taller de polarizados
meta» o «donde hacer PPF en Granada Meta» son otra intencion —la de alguien
que NO esta en Villavicencio y necesita saber si vale la pena el viaje—, y sin
una pagina que la responda esas consultas no tienen donde aterrizar.

El contenido es de verdad distinto al de las landings: distancias reales,
corredores viales, que suele traer cada municipio y como se organiza un
trabajo cuando el cliente viene de fuera. No es la misma pagina con el nombre
del departamento cambiado, que es justo lo que Google trata como doorway.

    python tools/generar-meta.py

Reutiliza TPL_CABEZA y TPL_PIE de generar-servicios.py para no duplicar el
<head>, la pantalla de carga ni el footer. Emite rutas locales (statics/...);
usar-cloudinary.py las convierte despues. Ver tools/build.py.
"""

import importlib.util
import io
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _cargar_generador():
    """generar-servicios.py tiene guion en el nombre: no se puede importar."""
    ruta = os.path.join(ROOT, "tools", "generar-servicios.py")
    spec = importlib.util.spec_from_file_location("generar_servicios", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GS = _cargar_generador()

SITE = GS.SITE
WA = GS.WA
WA_TEL = GS.WA_TEL
DIR_CALLE = GS.DIR_CALLE
LAT, LON = GS.LAT, GS.LON
SLUG = "personalizacion-de-vehiculos-meta"
URL = SITE + "/" + SLUG + ".html"

TITLE = "Lujos, PPF y Detailing en el Meta | DACARS Villavicencio"
DESC = ("Lujos, accesorios 4x4, PPF, detailing, polarizados y pintura para todo el Meta. "
        "Atendemos Acacías, Granada, Puerto López y Restrepo desde Villavicencio.")
KEYWORDS = ("lujos para carros meta, accesorios para carros meta, ppf meta, polarizados meta, "
            "detailing meta, taller de lujos meta, personalizacion de vehiculos meta, "
            "accesorios 4x4 meta, pintura para carros meta, lujos para carros acacias, "
            "polarizados granada meta, accesorios para carros puerto lopez, taller de carros meta, "
            "autolujos meta, llantas meta")

WA_TEXTO = "Hola DACARS, vengo de otro municipio del Meta y quiero cotizar un servicio."
WA_URL = GS.wa_url(WA_TEXTO)

# ---------------------------------------------------------------------------
#  Municipios con trato propio.
#
#  Las distancias son aproximadas por carretera desde Villavicencio y por eso
#  van redactadas como «unos X km»: sirven para que alguien calcule si el
#  viaje le cuadra, no para navegar. El texto de cada uno describe lo que de
#  verdad entra al taller desde esa zona, que es lo que hace util la pagina.
# ---------------------------------------------------------------------------
MUNICIPIOS_DETALLE = [
    ("Restrepo", "unos 19 km", "vía al norte",
     "El municipio más cercano al taller: se viene y se vuelve el mismo día sin despeinarse. "
     "De Restrepo llega sobre todo detailing, polarizado y lujos, casi siempre gente que aprovecha "
     "una vuelta a Villavicencio y deja el carro un par de horas."),

    ("Acacías", "unos 28 km", "vía al sur, ruta a Acacías",
     "La segunda ciudad más grande del área. Entra mucho vehículo de operación de empresas "
     "petroleras y de servicios: polarizado, protectores, iluminación auxiliar y PPF para las "
     "camionetas que se la pasan en carretera destapada."),

    ("Cumaral", "unos 35 km", "vía al norte, corredor Restrepo–Cumaral",
     "Zona de fincas y de finca de fin de semana. De acá llegan camionetas que se mueven entre "
     "asfalto y trocha: accesorios 4x4, iluminación, llantas para uso mixto y cubiertas de platón."),

    ("Guamal", "unos 38 km", "vía al sur, pasando Acacías",
     "Piedemonte y fincas. Vehículos que trabajan: estribos, protectores de bajos, llantas y "
     "pintura de paneles castigados por el sol y la carga."),

    ("Castilla la Nueva", "unos 45 km", "vía al sur, desvío después de Acacías",
     "Zona petrolera. Lo que más entra son camionetas de operación que necesitan iluminación "
     "auxiliar, barras, protectores y mantenimiento de pintura, porque viven en vías internas "
     "sin pavimentar."),

    ("San Carlos de Guaroa", "unos 60 km", "vía al sur y desvío hacia el oriente",
     "Territorio de palma. Vehículos de trabajo duro que llegan por llantas, protección de "
     "pintura y repintes de platón y guardafangos."),

    ("San Martín", "unos 62 km", "vía al sur, ruta del Ariari",
     "Tierra ganadera. Camionetas doble cabina con uso real: cubiertas de platón, bumpers, "
     "estribos, iluminación y PPF en el frente, que es lo primero que se pica en esa vía."),

    ("Granada", "unos 85 km", "vía al sur, ruta del Ariari",
     "El segundo polo urbano del departamento y el viaje más frecuente desde el sur. De Granada "
     "llega de todo el catálogo, y casi siempre en combinación: el que viaja hora y media no "
     "viene por un solo servicio."),

    ("Puerto López", "unos 86 km", "vía al oriente, ruta 40",
     "El puerto sobre el Meta y paso obligado hacia la altillanura. Entra bastante detailing y "
     "PPF: esa vía deja el frente del carro tapizado de insectos y picado de grava."),

    ("Barranca de Upía", "unos 100 km", "vía al norte, corredor hacia Casanare",
     "El extremo norte del departamento. Vehículos de trabajo y de finca que vienen por "
     "equipamiento 4x4, iluminación y llantas."),

    ("Fuente de Oro", "unos 110 km", "vía al sur, pasando Granada",
     "Agro del Ariari. Camionetas de carga liviana que llegan por cubiertas, llantas, protectores "
     "y pintura, casi siempre agendando el trabajo con antelación."),

    ("Puerto Gaitán", "unos 185 km", "vía al oriente, pasando Puerto López",
     "El viaje más largo de los frecuentes: tres horas largas de ida. Por eso desde acá casi "
     "siempre se agendan trabajos que valen el desplazamiento —PPF completo, pintura, "
     "equipamiento 4x4 de una vez— y el carro se deja varios días."),
]

# Los 29 municipios del Meta. Los 12 de arriba tienen párrafo propio; el resto
# entra acá para que la cobertura declarada sea la real y no una lista a medias.
MUNICIPIOS_TODOS = [
    "Acacías", "Barranca de Upía", "Cabuyaro", "Castilla la Nueva", "Cubarral",
    "Cumaral", "El Calvario", "El Castillo", "El Dorado", "Fuente de Oro",
    "Granada", "Guamal", "La Macarena", "Lejanías", "Mapiripán", "Mesetas",
    "Puerto Concordia", "Puerto Gaitán", "Puerto Lleras", "Puerto López",
    "Puerto Rico", "Restrepo", "San Carlos de Guaroa", "San Juan de Arama",
    "San Juanito", "San Martín", "Uribe", "Villavicencio", "Vistahermosa",
]

SERVICIOS_META = [
    ("PPF · Paint Protection Film", "ppf-villavicencio",
     "La vía al Llano y las rutas del Ariari y la altillanura son grava y piedra suelta. "
     "Si haces esos trayectos seguido, el PPF es lo que evita que la pintura se pique."),
    ("Accesorios y equipamiento 4x4", "accesorios-4x4-villavicencio",
     "Snorkel, bumpers, winches, canastillas y protectores para las camionetas que salen del "
     "pavimento todos los días, no solo los domingos."),
    ("Pintura automotriz", "pintura-automotriz-villavicencio",
     "Repinte de paneles y pintura general. En el Meta el sol quema el barniz del techo y el capó "
     "más rápido que en el resto del país."),
    ("Polarizados", "polarizados-villavicencio",
     "Menos calor adentro, que en el Llano no es un detalle estético sino una necesidad diaria."),
    ("Detailing", "detailing-villavicencio",
     "Lavado técnico, descontaminación y pulimento. Lo que pide un carro después de una temporada "
     "de carretera y sol."),
    ("Lujos y accesorios", "lujos-y-accesorios-villavicencio",
     "Estribos, molduras, cubiertas de platón, tapetes y todo lo que le da carácter propio al carro."),
    ("Iluminación", "iluminacion-para-carros-villavicencio",
     "Exploradoras, barras LED y luces auxiliares: en las vías veredales del Meta la iluminación "
     "de fábrica se queda corta."),
    ("Llantas", "llantas-villavicencio",
     "Asesoría según tu uso real. La llanta de ciudad y la de trocha no son intercambiables y acá "
     "muchos hacen las dos cosas."),
    ("Sonido e insonorización", "sonido-para-carros-villavicencio",
     "Equipos, parlantes y aislamiento, montados sin improvisar el cableado."),
    ("PDR · Desabolladura sin pintura", "pdr-desabolladura-sin-pintura-villavicencio",
     "Golpes de parqueadero sacados sin repintar, conservando la pintura de fábrica."),
]

PASOS = [
    ("Escríbenos con fotos",
     "Mándanos por WhatsApp la marca, el modelo, el año y fotos de lo que quieres resolver. "
     "Con eso hacemos la mitad del diagnóstico sin que hayas salido de tu municipio."),
    ("Cotización y tiempo real",
     "Te damos el precio y —más importante si vienes de lejos— cuántos días ocupa el carro. "
     "Así decides si lo dejas o si esperas."),
    ("Agendamos el día",
     "Reservamos el cupo y pedimos el material con antelación. Es la diferencia entre viajar una "
     "vez y viajar dos: nadie viene de Granada a que le digan que la lámina llega el jueves."),
    ("Entrega y revisión contigo",
     "Revisamos el trabajo juntos antes de que arranques de vuelta, no después. Y te damos las "
     "indicaciones de cuidado de los primeros días."),
]

RAZONES = [
    ("Acá está el material",
     "Láminas, películas, accesorios y repuestos de personalización se consiguen en la capital. "
     "En los municipios hay talleres buenos de mecánica, pero el material específico de lujos, "
     "PPF o polarizado casi siempre sale de Villavicencio."),
    ("Un solo viaje, varios servicios",
     "Si vives a hora y media, entrar tres veces al taller no tiene sentido. Combinar polarizado, "
     "accesorios y detailing en la misma visita es lo que hace que el desplazamiento valga."),
    ("Trabajos que necesitan área controlada",
     "El PPF, la pintura y el detailing de corrección dependen de trabajar sin polvo y con "
     "tiempos de curado respetados. Eso no se improvisa en un patio."),
]

FAQ = [
    ("¿Atienden vehículos de fuera de Villavicencio?",
     "Sí, y es una parte importante de lo que hacemos. El taller está en Villavicencio, en la "
     "Carrera 33 #24-60 del Barrio San Francisco, y recibimos carros de todo el Meta. Lo único "
     "que pedimos es que escribas antes de viajar para agendar."),

    ("¿Van hasta mi municipio a hacer el trabajo?",
     "No. Los trabajos se hacen en el taller de Villavicencio, porque el PPF, la pintura, el "
     "polarizado y el detailing necesitan área controlada, sin polvo y con tiempos de curado. "
     "Un trabajo de estos hecho a la intemperie se daña, y preferimos decírtelo antes que "
     "prometerte algo que quedaría mal."),

    ("Vengo de lejos. ¿Cuánto tiempo va a estar el carro en el taller?",
     "Depende del servicio, y por eso te lo decimos al cotizar y no al recibir el carro. Un "
     "polarizado es de horas; un PPF completo o una pintura general son de varios días. Si vienes "
     "de Granada, Puerto Gaitán o Fuente de Oro, organizamos la agenda alrededor de eso."),

    ("¿Puedo dejar el carro varios días?",
     "Sí, es lo normal cuando el cliente viene de otro municipio y el trabajo es largo. "
     "Coordínalo por WhatsApp antes de viajar para que el cupo y el material estén listos el día "
     "que llegues."),

    ("¿Vale la pena viajar desde Granada o Acacías por esto?",
     "Depende de qué necesites. Para un servicio pequeño, quizá no. Para PPF, pintura, detailing "
     "de corrección o un equipamiento 4x4 completo, la mayoría de nuestros clientes del sur del "
     "Meta hace el viaje porque es donde consiguen el material y la mano de obra especializada. "
     "Cuéntanos tu caso y te decimos con franqueza si te conviene."),

    ("¿Cotizan por WhatsApp sin que lleve el carro?",
     "Sí, para la mayoría de los servicios. Con la marca, el modelo, el año y unas fotos podemos "
     "darte un rango cerrado. Lo que sí necesita ver el carro en persona es la pintura y el PDR, "
     "porque el estado real de la lámina no siempre se aprecia en una foto."),

    ("¿Manejan facturación para empresas del Meta?",
     "Trabajamos como DACARS VILLAVICENCIO S.A.S, con NIT 901.798.060. Si necesitas facturación "
     "para una empresa o una flota, escríbenos y coordinamos los datos antes del trabajo."),
]


def jsonld():
    negocio = {
        "@type": ["AutoPartsStore", "AutoRepair"],
        "@id": SITE + "/#dacars",
        "name": "DACARS",
        "telephone": "+" + WA,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": DIR_CALLE,
            "addressLocality": "Villavicencio",
            "addressRegion": "Meta",
            "postalCode": "500001",
            "addressCountry": "CO",
        },
        "geo": {"@type": "GeoCoordinates", "latitude": LAT, "longitude": LON},
    }

    meta = {
        "@type": "State",
        "@id": URL + "#meta",
        "name": "Meta",
        "alternateName": "Departamento del Meta",
        "containedInPlace": {"@type": "Country", "name": "Colombia"},
    }

    graph = [
        {
            "@type": "WebPage",
            "@id": URL + "#pagina",
            "url": URL,
            "name": TITLE,
            "description": DESC,
            "inLanguage": "es-CO",
            "isPartOf": {"@id": SITE + "/#sitio"},
            "about": {"@id": URL + "#servicio"},
            "breadcrumb": {"@id": URL + "#migas"},
            "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + "/statics/og-image.jpg"},
        },
        {
            "@type": "Service",
            "@id": URL + "#servicio",
            "name": "Personalización de vehículos en el departamento del Meta",
            "description": DESC,
            "url": URL,
            "serviceType": "Personalización y protección de vehículos",
            "category": "Automotriz",
            "provider": negocio,
            "areaServed": [meta] + [{"@type": "City", "name": m,
                                     "containedInPlace": {"@id": URL + "#meta"}}
                                    for m in MUNICIPIOS_TODOS],
            "availableChannel": {
                "@type": "ServiceChannel",
                "serviceUrl": WA_URL,
                "servicePhone": "+" + WA,
                "serviceLocation": {
                    "@type": "Place",
                    "name": "DACARS Villavicencio",
                    "address": negocio["address"],
                    "geo": negocio["geo"],
                },
            },
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": "Servicios DACARS para el Meta",
                "itemListElement": [
                    {"@type": "Offer",
                     "itemOffered": {"@type": "Service", "name": nombre,
                                     "url": SITE + "/" + slug + ".html",
                                     "areaServed": {"@id": URL + "#meta"},
                                     "provider": {"@id": SITE + "/#dacars"}}}
                    for nombre, slug, _ in SERVICIOS_META
                ],
            },
        },
        {
            "@type": "BreadcrumbList",
            "@id": URL + "#migas",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Cobertura", "item": SITE + "/#cobertura"},
                {"@type": "ListItem", "position": 3, "name": "Meta", "item": URL},
            ],
        },
        {
            "@type": "FAQPage",
            "@id": URL + "#faq",
            "mainEntity": [
                {"@type": "Question", "name": q,
                 "acceptedAnswer": {"@type": "Answer", "text": a}}
                for q, a in FAQ
            ],
        },
        {
            "@type": "ItemList",
            "@id": URL + "#municipios",
            "name": "Municipios del Meta que atiende DACARS",
            "numberOfItems": len(MUNICIPIOS_TODOS),
            "itemListElement": [
                {"@type": "ListItem", "position": i + 1,
                 "item": {"@type": "City", "name": m,
                          "containedInPlace": {"@id": URL + "#meta"}}}
                for i, m in enumerate(MUNICIPIOS_TODOS)
            ],
        },
    ]
    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, indent=2)


CUERPO = """
<main id="contenido">

<nav class="migas" aria-label="Ruta de navegación">
  <div class="wrap">
    <ol>
      <li><a href="index.html">Inicio</a></li>
      <li><a href="index.html#cobertura">Cobertura</a></li>
      <li aria-current="page">Departamento del Meta</li>
    </ol>
  </div>
</nav>

<section class="shero">
  <div class="shero__bg" aria-hidden="true"><span class="grid"></span><span class="glow glow--a"></span></div>
  <div class="wrap">
    <p class="tag" data-reveal>Cobertura &middot; Departamento del Meta</p>
    <h1 class="shero__title" data-reveal><span class="chrome">Personalización de vehículos en el Meta</span></h1>
    <p class="shero__sub" data-reveal>Un taller en Villavicencio que atiende todo el departamento</p>
    <p class="shero__lead" data-reveal>Lujos, accesorios 4x4, PPF, detailing, polarizados y pintura para
      quienes vienen de Acacías, Granada, Puerto López, Restrepo y el resto del Meta.</p>
    <div class="hero__cta" data-reveal>
      <a class="btn btn--primary" href="@@WA@@" target="_blank" rel="noopener">
        @@SVGWA@@
        Cotizar antes de viajar
      </a>
      <a class="btn btn--ghost" href="#municipios">Ver mi municipio</a>
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap sec__narrow">
    <p class="sec__lead" data-reveal>El Meta es grande y desigual: cabe casi tres veces Suiza, pero la
      infraestructura de personalización automotriz está concentrada en la capital. Si vives en Granada,
      en Puerto Gaitán o en Cumaral, es muy probable que tu mecánico de confianza quede a diez minutos
      y que el taller que instala PPF quede a hora y media.</p>
    <p class="sec__lead" data-reveal>DACARS queda en Villavicencio, en la <strong>@@DIR@@</strong>, y buena
      parte de los carros que entran al taller no son de la ciudad. Vienen del sur por la ruta del Ariari,
      del norte por Restrepo y Cumaral, y del oriente por la vía a Puerto López. Esta página existe para eso:
      para que sepas de antemano cuánto se demora tu trabajo, qué conviene combinar y si el viaje te cuadra,
      antes de arrancar.</p>
    <p class="sec__lead" data-reveal>Lo decimos claro desde ya: <strong>no vamos hasta tu municipio</strong>.
      El PPF, la pintura, el polarizado y el detailing de corrección necesitan área controlada y tiempos
      de curado que no se improvisan. Lo que sí hacemos es organizar la visita para que viajes una sola vez.</p>
  </div>
</section>

<section class="sec sec--alt">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Por qué el viaje</p>
      <h2 class="sec__title chrome" data-reveal>Por qué la gente del Meta termina en Villavicencio</h2>
    </header>
    <div class="cards cards--3">
@@RAZONES@@
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Cómo funciona</p>
      <h2 class="sec__title chrome" data-reveal>Si vienes de otro municipio</h2>
      <p class="sec__lead" data-reveal>El objetivo es simple: que no viajes dos veces. Todo lo que se puede
        resolver por WhatsApp se resuelve antes de que salgas de tu casa.</p>
    </header>
    <ol class="steps">
@@PASOS@@
    </ol>
  </div>
</section>

<section class="sec sec--alt" id="municipios">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Municipio por municipio</p>
      <h2 class="sec__title chrome" data-reveal>De dónde llegan los carros que atendemos</h2>
      <p class="sec__lead" data-reveal>Distancias aproximadas por carretera desde el taller. Sirven para
        que calcules el viaje, no para navegar: el estado de la vía manda más que los kilómetros.</p>
    </header>
    <div class="cards cards--3">
@@MUNIS@@
    </div>
    <p class="sec__foot" data-reveal>¿Tu municipio no está en la lista? Igual te atendemos.
      <a class="link" href="@@WA@@" target="_blank" rel="noopener">Escríbenos y coordinamos &rarr;</a>
    </p>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Servicios</p>
      <h2 class="sec__title chrome" data-reveal>Lo que puedes resolver en una sola visita</h2>
      <p class="sec__lead" data-reveal>Diez especialidades en el mismo taller. Si viajas desde lejos,
        combinar varias es justamente lo que hace que el desplazamiento valga la pena.</p>
    </header>
    <div class="cards cards--3">
@@SERVICIOS@@
    </div>
  </div>
</section>

<section class="sec sec--alt" id="faq">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Preguntas frecuentes</p>
      <h2 class="sec__title chrome" data-reveal>Lo que nos preguntan desde fuera de Villavicencio</h2>
    </header>
    <div class="faq">
@@FAQ@@
    </div>
  </div>
</section>

<section class="sec" id="cobertura">
  <div class="wrap sec__narrow">
    <header class="sec__head">
      <p class="tag" data-reveal>Cobertura</p>
      <h2 class="sec__title chrome" data-reveal>Los 29 municipios del Meta</h2>
      <p class="sec__lead" data-reveal>Recibimos vehículos de todo el departamento. Los que quedan más lejos
        —la Macarena, Mapiripán, Uribe— requieren planear el viaje con más antelación, pero la puerta del
        taller es la misma para todos.</p>
    </header>
    <ul class="chips" data-reveal>
@@CHIPS@@
    </ul>
    <p class="sec__lead" data-reveal>¿Estás en Villavicencio? Entonces te sirve más la
      <a class="link" href="index.html#cobertura">cobertura por barrios de la ciudad</a>.</p>
    <div class="mapa-mini" data-reveal>
      <iframe title="Ubicación de DACARS en Villavicencio, Meta"
        src="https://www.google.com/maps?q=Carrera%2033%20%2324-60%20Barrio%20San%20Francisco%20Villavicencio%20Meta&amp;z=16&amp;output=embed"
        loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
  </div>
</section>

<section class="cierre">
  <div class="wrap cierre__in">
    <h2 class="chrome" data-reveal>Escríbenos antes de viajar</h2>
    <p data-reveal>Cuéntanos de dónde vienes, qué vehículo tienes y qué necesitas. Te cotizamos, te decimos
      cuántos días ocupa el carro y te agendamos el cupo.</p>
    <a class="btn btn--primary" href="@@WA@@" target="_blank" rel="noopener" data-reveal>
      @@SVGWA@@
      Escribir por WhatsApp
    </a>
  </div>
</section>

</main>
"""


def build():
    esc = GS.esc

    razones = "\n".join(
        '        <article class="card" data-reveal>\n'
        '          <h3>%s</h3>\n'
        '          <p>%s</p>\n'
        '        </article>' % (esc(t), esc(d))
        for t, d in RAZONES
    )
    pasos = "\n".join(
        '        <li class="step" data-reveal>\n'
        '          <span class="step__n">0%d</span>\n'
        '          <h3>%s</h3>\n'
        '          <p>%s</p>\n'
        '        </li>' % (i + 1, esc(t), esc(d))
        for i, (t, d) in enumerate(PASOS)
    )
    munis = "\n".join(
        '        <article class="card" data-reveal>\n'
        '          <h3>%s</h3>\n'
        '          <p><strong>%s</strong> desde el taller &middot; %s</p>\n'
        '          <p>%s</p>\n'
        '        </article>' % (esc(n), esc(km), esc(via), esc(txt))
        for n, km, via, txt in MUNICIPIOS_DETALLE
    )
    servicios = "\n".join(
        '        <article class="card" data-reveal>\n'
        '          <h3>%s</h3>\n'
        '          <p>%s</p>\n'
        '          <a class="card__mas" href="%s.html">%s en Villavicencio &rarr;</a>\n'
        '        </article>' % (esc(n), esc(d), slug, esc(n.split(" · ")[0]))
        for n, slug, d in SERVICIOS_META
    )
    faq = "\n".join(
        '      <details data-reveal>\n'
        '        <summary>%s</summary>\n'
        '        <div><p>%s</p></div>\n'
        '      </details>' % (esc(q), esc(a))
        for q, a in FAQ
    )
    chips = "\n".join('      <li>%s</li>' % m for m in MUNICIPIOS_TODOS)

    # El glifo de WhatsApp se toma de la plantilla compartida en vez de
    # repetirlo acá: fix-iconos.py lo mantiene al día en un solo lugar.
    ini = GS.TPL_PIE.index('<svg class="marca"')
    svg_wa = GS.TPL_PIE[ini:GS.TPL_PIE.index("</svg>", ini) + len("</svg>")]

    html = GS.TPL_CABEZA + CUERPO + GS.TPL_PIE

    reemplazos = {
        "@@TITLE@@": esc(TITLE),
        "@@DESC@@": esc(DESC),
        "@@KEYWORDS@@": esc(KEYWORDS),
        "@@URL@@": URL,
        "@@SITE@@": SITE,
        "@@LAT@@": str(LAT),
        "@@LON@@": str(LON),
        "@@JSONLD@@": jsonld(),
        "@@NAV@@": GS.nav_html(SLUG),
        "@@SVGWA@@": svg_wa,
        "@@RAZONES@@": razones,
        "@@PASOS@@": pasos,
        "@@MUNIS@@": munis,
        "@@SERVICIOS@@": servicios,
        "@@FAQ@@": faq,
        "@@CHIPS@@": chips,
        "@@DIR@@": DIR_CALLE,
        "@@WA@@": WA_URL,
        "@@WANUM@@": WA,
        "@@WATEL@@": WA_TEL,
    }
    for k, v in reemplazos.items():
        html = html.replace(k, v)
    return html


def main():
    destino = os.path.join(ROOT, SLUG + ".html")
    io.open(destino, "w", encoding="utf-8", newline="\n").write(build())
    print("generada  %s.html" % SLUG)


if __name__ == "__main__":
    main()
