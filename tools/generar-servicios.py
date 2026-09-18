# -*- coding: utf-8 -*-
"""
Generador de las paginas de servicio de DACARS.

Crea una landing page optimizada para busqueda local por cada servicio
(«<servicio> en Villavicencio»), con contenido unico, JSON-LD de Service,
BreadcrumbList y FAQPage.

    python tools/generar-servicios.py

OJO: sobrescribe los .html de servicio. Si editas esos archivos a mano,
edita mejor los datos de ESTE script y vuelve a generarlos, o deja de
usarlo para no perder los cambios.
"""

import io
import json
import os

SITE = "https://www.dacars.com.co"
WA = "573112629406"
WA_TEL = "+57 311 262 9406"
DIR_CALLE = "Carrera 33 #24-60, Barrio San Francisco"
CIUDAD = "Villavicencio"
DEPTO = "Meta"
# Coordenada aproximada del casco urbano de Villavicencio.
# REEMPLAZAR por la exacta de la ficha de Google Business de DACARS.
LAT, LON = 4.1420, -73.6340

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BARRIOS = [
    "San Francisco", "Barzal", "Centro", "Siete de Agosto", "La Esperanza",
    "Ciudad Porfía", "Catumare", "El Buque", "Villa Bolívar", "La Rosita",
    "Los Centauros", "Balcones de Toledo", "Maizaro", "San Fernando",
    "Las Colinas", "Nueva Andalucía", "Camoa", "Montecarlo",
    "Las Américas", "Playa Rica", "El Refugio", "La Vega",
]

MUNICIPIOS = [
    "Acacías", "Restrepo", "Cumaral", "Granada", "Puerto López",
    "San Martín", "Guamal", "Castilla la Nueva", "San Carlos de Guaroa",
    "Barranca de Upía", "Puerto Gaitán", "Fuente de Oro",
]


VIDEOS = {
    'ppf-villavicencio': ('reel-ppf-sportage', 'Full PPF mate en un Kia Sportage 2025', 'PT36S', 'Instalacion de PPF mate completo sobre un Kia Sportage 2025 en DACARS Villavicencio.', 'Mira el trabajo completo: alistamiento, corte e instalación panel por panel hasta el acabado mate final.'),
    'iluminacion-para-carros-villavicencio': ('reel-led-4x4', 'Exploradoras LED para camioneta 4x4', 'PT34S', 'Montaje de exploradoras LED SC para camioneta 4x4 en DACARS Villavicencio.', 'Exploradoras LED montadas y encendidas. Así se ve la diferencia real cuando cae la noche en trocha.'),
    'accesorios-4x4-villavicencio': ('reel-testimonio-cubierta', 'Testimonio: cubierta de platón', 'PT1M3S', 'Un cliente de DACARS Villavicencio cuenta como quedo la cubierta de platon de su camioneta.', 'Un cliente cuenta, junto a su camioneta, cómo le quedó la cubierta de platón que le instalamos. Tiene audio.'),
    'lujos-y-accesorios-villavicencio': ('reel-hummer-ev', 'Hummer EV: barra LED, faros y rines', 'PT55S', 'Personalizacion de una Hummer EV en Villavicencio: barra LED, faros y rines.', 'Una Hummer EV que pasó por el taller: barra LED, faros, iluminación delantera y rines.'),
}

# =========================================================
#  CONTENIDO POR SERVICIO
# =========================================================
SERVICIOS = [
    {
        "slug": "ppf-villavicencio",
        "menu": "PPF",
        "nombre": "PPF · Paint Protection Film",
        "h1": "PPF en Villavicencio",
        "h1_sub": "Protección de pintura que aguanta la vía al Llano",
        "title": "PPF en Villavicencio | Paint Protection Film para carros — DACARS",
        "desc": "Instalación de PPF en Villavicencio. Película de poliuretano que protege la pintura de tu carro de la grava, la arena y los insectos de la vía al Llano. Cotiza por WhatsApp.",
        "keywords": "ppf villavicencio, paint protection film villavicencio, proteccion de pintura villavicencio, lamina protectora de pintura villavicencio, ppf carros meta, proteger pintura carro villavicencio",
        "lead": "Película transparente de poliuretano instalada panel por panel. Recibe el impacto que hoy se lleva tu pintura de fábrica.",
        "intro": [
            "Entre la vía al Llano, el Anillo Vial y cualquier salida hacia una finca hay un enemigo constante: la grava. A 80 km/h una piedra pequeña no raya el barniz, lo pica. Y cada pica es un punto por donde entra humedad y arranca la corrosión. Súmale los insectos del Llano, que en ciertas épocas dejan el frente del carro tapizado, y la arena que levanta cualquier volqueta.",
            "El PPF (Paint Protection Film) es una lámina transparente de poliuretano que se instala <strong>sobre</strong> el barniz de fábrica y se lleva esos golpes en lugar de la pintura. Es una capa sacrificable: se daña ella, no tu carro. En DACARS la cortamos a medida para cada panel, con los bordes escondidos, para que no se note que está puesta.",
        ],
        "incluye_titulo": "Qué incluye la instalación",
        "incluye": [
            ["Lavado y descontaminación previa", "La lámina solo pega bien sobre pintura limpia. Sacamos grasa, savia y contaminación antes de cortar."],
            ["Corte a medida por panel", "Cada pieza se ajusta al vehículo, no se pega un rollo genérico encima."],
            ["Instalación en área controlada", "Menos polvo en el ambiente, menos motas atrapadas bajo la película."],
            ["Sellado y escondido de bordes", "Los bordes van por dentro del panel donde el diseño lo permite, para que no levanten ni acumulen mugre."],
            ["Curado y revisión final", "Revisamos el resultado contigo panel por panel antes de entregarte el carro."],
            ["Recomendaciones de cuidado", "Te explicamos qué hacer y qué no durante los primeros días."],
        ],
        "razones_titulo": "Por qué el PPF tiene sentido acá",
        "razones": [
            ["Grava en la vía al Llano", "Los tramos en obra y las bermas sin pavimentar son una lluvia constante de piedra sobre el capó, el bómper y los espejos."],
            ["Sol del Llano todo el año", "El sol directo castiga el barniz. La película suma una barrera adicional sobre el acabado original."],
            ["Valor de reventa", "La pintura original es de lo primero que mira un comprador. Repintada, el carro pierde valor; protegida, lo sostiene."],
        ],
        "proceso": [
            ["Diagnóstico de la pintura", "Revisamos el estado real del barniz. Si hay rayones previos, te decimos si conviene corregir antes de instalar, porque la lámina no los tapa: los congela."],
            ["Alistamiento", "Lavado técnico, descontaminación y secado completo. Es la parte que nadie ve y la que define si la instalación dura."],
            ["Instalación panel por panel", "Corte a medida, posicionamiento y extracción de solución. Acá se define que no queden burbujas ni bordes visibles."],
            ["Curado y entrega", "La película necesita unas horas para asentarse. Te entregamos el carro con las indicaciones de los primeros días."],
        ],
        "precio_titulo": "Qué define el precio de un PPF",
        "precio": [
            "El <strong>tamaño del vehículo</strong>: no es lo mismo un hatchback que una camioneta doble cabina.",
            "Los <strong>paneles a cubrir</strong>: desde un kit frontal (capó parcial, bómper, espejos, farolas) hasta el vehículo completo.",
            "El <strong>tipo de película</strong>: brillante, mate o de acabado especial.",
            "El <strong>estado de la pintura</strong>: si hace falta corrección previa, eso se cotiza aparte.",
        ],
        "faq": [
            ["¿El PPF daña la pintura cuando lo retiran?", "No. Está diseñado para removerse sin arrancar el barniz de fábrica, siempre que la instalación y el retiro los haga alguien que sepa. Por eso importa tanto el corte y el manejo de los bordes."],
            ["¿Se nota que el carro tiene PPF?", "Bien instalado, casi no. La película es transparente y los bordes quedan escondidos dentro del panel donde el diseño lo permite. De lejos no se ve; de cerca hay que saber dónde mirar."],
            ["¿Puedo lavar el carro normal después?", "Sí, pasados los días de curado que te indicamos. Lo que recomendamos es evitar hidrolavadora a presión muy alta apuntando directo a los bordes."],
            ["¿PPF o polarizado? ¿Son lo mismo?", "No. El polarizado va en los vidrios y controla calor, luz y privacidad. El PPF va sobre la pintura de la carrocería y la protege de impactos. Son servicios distintos y muchos clientes hacen los dos."],
            ["¿Cuánto tiempo se demora la instalación?", "Depende del vehículo y de cuántos paneles cubras. Un kit frontal y un vehículo completo son trabajos muy distintos. Al cotizar te damos el tiempo exacto para que organices tu semana."],
        ],
        "wa": "Hola DACARS, quiero cotizar PPF para mi vehículo en Villavicencio.",
    },

    {
        "slug": "polarizados-villavicencio",
        "menu": "Polarizados",
        "nombre": "Polarizados",
        "h1": "Polarizados en Villavicencio",
        "h1_sub": "Menos calor adentro, más privacidad, sin burbujas",
        "title": "Polarizados en Villavicencio | Láminas para vidrios — DACARS",
        "desc": "Polarizado de vidrios en Villavicencio con corte y curado profesional. Menos calor, bloqueo UV y privacidad, sin burbujas ni bordes a la vista. Cotiza por WhatsApp.",
        "keywords": "polarizados villavicencio, polarizado de carros villavicencio, laminas para vidrios villavicencio, entintado de vidrios villavicencio, polarizado ceramico villavicencio, polarizar carro meta",
        "lead": "Instalación de láminas con corte a medida y curado controlado. El trabajo que se nota cuando abres la puerta a mediodía.",
        "intro": [
            "En Villavicencio el carro se calienta parado. Dejarlo dos horas al sol y volver a montarse es una experiencia que todo el mundo acá conoce. Una lámina buena no es estética: es la diferencia entre entrar a un horno o entrar a un carro que el aire acondicionado sí alcanza a enfriar.",
            "El problema es que el polarizado mal instalado se ve barato y se daña rápido: burbujas a los tres meses, bordes que levantan, el morado que aparece al año. Todo eso sale de dos cosas — la calidad de la lámina y la calidad de la mano. En DACARS cuidamos las dos: limpieza profunda del vidrio, corte a medida y curado sin afanes.",
        ],
        "incluye_titulo": "Qué incluye el servicio",
        "incluye": [
            ["Limpieza profunda del vidrio", "Se saca todo residuo antes de pegar. Una mota atrapada es una burbuja permanente."],
            ["Corte a medida del vidrio", "Se ajusta a la curvatura real de tu carro, sin recortes visibles ni sobrantes."],
            ["Instalación sin burbujas", "Aplicación y extracción de solución hasta que el vidrio quede limpio de aire."],
            ["Curado controlado", "Te decimos cuántos días esperar antes de bajar los vidrios para que la lámina se asiente."],
            ["Asesoría de nivel de oscuridad", "Te orientamos sobre qué porcentaje conviene según el uso del vehículo."],
            ["Respaldo del trabajo", "Si algo queda mal instalado, lo corregimos."],
        ],
        "razones_titulo": "Lo que cambia con un buen polarizado",
        "razones": [
            ["Calor adentro", "Menos radiación entrando significa un habitáculo más fresco y un aire acondicionado que no tiene que trabajar al máximo todo el día."],
            ["Protección UV", "El sol decolora tableros, tapicería y volantes. La lámina reduce la radiación que entra y el interior se conserva mejor."],
            ["Privacidad", "Lo que va en la silla de atrás o en el baúl deja de ser una vitrina en cada semáforo."],
        ],
        "proceso": [
            ["Elección de la lámina", "Te mostramos las opciones y te explicamos la diferencia real entre una lámina estándar y una de gama alta en rechazo de calor."],
            ["Preparación de los vidrios", "Limpieza profunda por dentro y por fuera, con el vehículo en zona cubierta."],
            ["Corte e instalación", "Pieza por pieza, ajustada a la curvatura de cada vidrio."],
            ["Curado y entrega", "Te explicamos el tiempo de espera antes de bajar los vidrios y cómo limpiarlos de ahí en adelante."],
        ],
        "precio_titulo": "Qué define el precio de un polarizado",
        "precio": [
            "El <strong>número y tamaño de los vidrios</strong>: un sedán, una camioneta y un panorámico completo no cuestan igual.",
            "El <strong>tipo de lámina</strong>: las de gama alta rechazan más calor y duran más sin virar de color.",
            "El <strong>porcentaje de oscuridad</strong> que elijas.",
            "Si hay que <strong>retirar una lámina vieja</strong>, que es un trabajo aparte y toma tiempo.",
        ],
        "faq": [
            ["¿Cuánto tiempo debo esperar para bajar los vidrios?", "Unos días, dependiendo de la lámina y del clima. Te damos la indicación exacta al entregarte el carro. Bajarlos antes de tiempo es la causa número uno de que una lámina se despegue por el borde."],
            ["¿Es legal polarizar el carro en Colombia?", "El uso de vidrios polarizados u oscurecidos está regulado y en ciertos casos exige autorización de la autoridad de tránsito. Te asesoramos sobre el nivel de oscuridad, pero el trámite del permiso lo debe hacer el propietario ante la entidad correspondiente."],
            ["¿Vale la pena una lámina cerámica en Villavicencio?", "Por el clima de acá, sí marca diferencia: rechaza más calor sin necesidad de ser tan oscura. Escríbenos y te comparamos las opciones con precios reales."],
            ["¿Por qué se ponen moradas algunas láminas?", "Es lo que pasa con láminas de baja calidad cuando el adhesivo se degrada con el sol. Por eso trabajamos con material que aguanta el sol del Llano."],
            ["¿Pueden quitar el polarizado viejo?", "Sí. Es un trabajo aparte porque el adhesivo viejo hay que retirarlo por completo antes de instalar la lámina nueva. Se cotiza sumado al polarizado."],
        ],
        "wa": "Hola DACARS, quiero cotizar polarizado para mi vehículo en Villavicencio.",
    },

    {
        "slug": "detailing-villavicencio",
        "menu": "Detailing",
        "nombre": "Detailing",
        "h1": "Detailing automotriz en Villavicencio",
        "h1_sub": "Lavado técnico, corrección de pintura y sellado",
        "title": "Detailing en Villavicencio | Pulimento de carros — DACARS",
        "desc": "Detailing automotriz en Villavicencio: descontaminación, corrección de pintura, pulimento, sellado y limpieza de interiores. Recupera el brillo de tu carro. Cotiza por WhatsApp.",
        "keywords": "detailing villavicencio, pulida de carro villavicencio, lavado tecnico villavicencio, correccion de pintura villavicencio, brillado de carros villavicencio, encerado de autos meta",
        "lead": "No es una lavada. Es sacarle a la pintura la contaminación, los rayones finos y la opacidad que acumuló el sol.",
        "intro": [
            "Un carro en Villavicencio vive una combinación difícil: sol fuerte casi todo el año, aguaceros que dejan cal, polvo de vías destapadas y barro cuando toca salir a finca. Eso no se quita con jabón. Se incrusta en el barniz, lo opaca y lo va dejando áspero al tacto.",
            "El detailing ataca eso por capas: primero se descontamina la pintura, luego se corrige lo que se puede corregir con pulimento, y al final se sella para que el brillo dure. El resultado no es un carro «lavado»; es un carro que vuelve a reflejar como cuando salió de agencia.",
        ],
        "incluye_titulo": "Qué contempla un trabajo de detailing",
        "incluye": [
            ["Lavado técnico", "Con método y materiales que no siguen rayando la pintura mientras se lava."],
            ["Descontaminación", "Se retira lo que quedó incrustado en el barniz y que un lavado normal no saca."],
            ["Corrección de pintura", "Pulimento para atenuar rayones finos, marcas de lavado y opacidad."],
            ["Sellado o protección", "Una capa que protege el trabajo y hace que el brillo aguante más."],
            ["Limpieza de interiores", "Tapicería, plásticos, tablero y detalles que suelen quedar por fuera."],
            ["Motor y llantas", "Los detalles que hacen que el carro se vea completo, no solo por fuera."],
        ],
        "razones_titulo": "Cuándo tu carro te está pidiendo detailing",
        "razones": [
            ["La pintura se siente áspera", "Si pasas la mano y no está lisa, hay contaminación incrustada que el lavado ya no saca."],
            ["Brillo apagado bajo el sol", "Al sol directo se ven telarañas y marcas circulares. Eso es rayón fino de lavado mal hecho, y se corrige."],
            ["Antes de vender o entregar", "Un carro detallado se ve mejor en fotos, se muestra mejor y negocia mejor."],
        ],
        "proceso": [
            ["Evaluación de la pintura", "Miramos el estado real bajo luz, para saber qué se puede corregir y qué no. Te lo decimos de frente."],
            ["Lavado y descontaminación", "Se retira toda la mugre superficial y la incrustada antes de tocar el pulidor."],
            ["Corrección", "Pulimento en las zonas que lo necesitan, con el nivel de agresividad que la pintura aguante."],
            ["Protección y entrega", "Sellado del trabajo, revisión contigo y recomendaciones para que dure."],
        ],
        "precio_titulo": "Qué define el precio del detailing",
        "precio": [
            "El <strong>tamaño del vehículo</strong> y la superficie a trabajar.",
            "El <strong>estado de la pintura</strong>: no es lo mismo refrescar que corregir años de sol y lavadas bruscas.",
            "El <strong>nivel del servicio</strong>: desde un lavado detallado hasta una corrección completa con sellado.",
            "Si se incluye o no <strong>interior a profundidad</strong>.",
        ],
        "faq": [
            ["¿En qué se diferencia de una lavada normal?", "Una lavada quita la mugre de encima. El detailing trabaja el barniz: lo descontamina, corrige defectos y lo protege. Son escalas distintas de trabajo y de tiempo."],
            ["¿El pulimento desgasta la pintura?", "Todo pulimento retira una capa mínima de barniz, por eso se hace con criterio y solo hasta donde la pintura lo permita. Un trabajo bien hecho corrige sin comprometer el acabado."],
            ["¿Cuánto dura el resultado?", "Depende del sellado que se aplique y de cómo se lave el carro después. Te damos las recomendaciones para que el trabajo no se pierda en un mes."],
            ["¿Puedo combinar detailing con PPF?", "Es lo ideal, y en ese orden: primero se corrige la pintura y luego se instala la película. Así no quedan rayones congelados debajo del PPF."],
            ["¿Cuánto tiempo se queda el carro?", "Depende del nivel de trabajo. Una corrección completa no es un servicio de una hora. Al cotizar te confirmamos el tiempo real."],
        ],
        "wa": "Hola DACARS, quiero cotizar un detailing para mi vehículo en Villavicencio.",
    },

    {
        "slug": "accesorios-4x4-villavicencio",
        "menu": "Accesorios 4x4",
        "nombre": "Accesorios 4x4",
        "h1": "Accesorios 4x4 en Villavicencio",
        "h1_sub": "Equipamiento para camionetas que sí salen del pavimento",
        "title": "Accesorios 4x4 en Villavicencio | Snorkel y bumpers — DACARS",
        "desc": "Accesorios 4x4 en Villavicencio: snorkel, bumpers, winches, canastillas, protectores y estribos reforzados para camionetas del Meta. Instalación técnica. Cotiza por WhatsApp.",
        "keywords": "accesorios 4x4 villavicencio, snorkel villavicencio, bumper 4x4 villavicencio, winche villavicencio, canastilla de techo villavicencio, accesorios camionetas meta, equipamiento offroad villavicencio",
        "lead": "Snorkel, bumpers, winches, canastillas y protectores. Montados para trabajar, no para la foto.",
        "intro": [
            "En el Meta la camioneta no es un accesorio de ciudad. Se usa para llegar a finca, cruzar caño, moverse en verano entre polvo y en invierno entre barro. Y un vehículo que hace eso necesita equipamiento distinto al que trae de agencia.",
            "Acá montamos accesorios 4x4 pensando en el uso real: que el bumper aguante, que el winche esté anclado donde debe, que el snorkel quede sellado y que la canastilla no silbe a 100. La diferencia entre un accesorio que sirve y uno que estorba casi siempre está en la instalación.",
        ],
        "incluye_titulo": "Qué montamos",
        "incluye": [
            ["Snorkel", "Para elevar la toma de aire del motor. Su valor está en el sellado: mal instalado es peor que no tenerlo."],
            ["Bumpers y defensas", "Protección frontal y trasera, con los anclajes adecuados al chasis del vehículo."],
            ["Winches", "Malacate con su montaje y conexión eléctrica hecha como toca, no empalmada."],
            ["Canastillas y barras de techo", "Capacidad de carga para viaje, herramientas o equipaje."],
            ["Protectores de bajos", "Para cárter, caja y transferencia, que es lo primero que golpea una piedra en trocha."],
            ["Estribos reforzados", "Acceso más cómodo y protección lateral de los estribos originales."],
        ],
        "razones_titulo": "Para el uso real del Llano",
        "razones": [
            ["Vías destapadas", "Entre Villavicencio, Puerto López y las fincas de la región, buena parte del recorrido no es asfalto."],
            ["Cruces de agua", "En invierno cualquier caño crecido cambia el plan. El equipamiento correcto define si pasas o te devuelves."],
            ["Carga y herramienta", "Canastilla y anclajes bien puestos evitan tener que meter todo adentro y viajar incómodo."],
        ],
        "proceso": [
            ["Asesoría según tu uso", "Nos cuentas a dónde sale el carro de verdad. No tiene sentido venderte un equipamiento de expedición si vas a finca los domingos."],
            ["Selección del accesorio", "Revisamos compatibilidad con tu marca, modelo y año antes de comprometer nada."],
            ["Instalación y anclaje", "Montaje con los puntos de anclaje correctos y cableado protegido donde aplique."],
            ["Prueba y entrega", "Verificamos ajuste, holguras y funcionamiento antes de entregarte el vehículo."],
        ],
        "precio_titulo": "Qué define el precio",
        "precio": [
            "El <strong>accesorio y su calidad</strong>: hay diferencias grandes de material y acabado.",
            "La <strong>marca, modelo y año</strong> del vehículo, que determina qué piezas aplican.",
            "La <strong>complejidad de la instalación</strong>: un winche con su conexión eléctrica no es lo mismo que unos estribos.",
            "Si se requiere <strong>adaptación o refuerzo</strong> adicional.",
        ],
        "faq": [
            ["¿El snorkel realmente sirve o es estética?", "Sirve, y mucho, si la instalación queda sellada. Eleva la toma de aire y reduce el riesgo de que el motor aspire agua o polvo. Mal sellado, en cambio, puede hacer que entre agua directo: por eso importa quién lo instala."],
            ["¿Instalar accesorios me quita la garantía del carro?", "Depende del accesorio y de la política de cada marca. Te lo advertimos antes de montar cualquier cosa que pueda afectarla, para que decidas con la información en la mano."],
            ["¿Qué winche necesito para mi camioneta?", "Se calcula según el peso del vehículo. Escríbenos con la marca, el modelo y el año y te decimos qué capacidad te corresponde."],
            ["¿Trabajan Hilux, Ranger, D-Max, Amarok, Prado?", "Trabajamos camionetas y vehículos 4x4 en general. Mándanos los datos de tu vehículo y confirmamos compatibilidad de la pieza antes de cotizar."],
            ["¿Puedo llevar accesorios que ya compré?", "Cuéntanos qué tienes. Si la pieza es compatible y está en buen estado, coordinamos la instalación; si vemos riesgo para el vehículo, te lo decimos antes de montarla."],
        ],
        "wa": "Hola DACARS, quiero cotizar accesorios 4x4 para mi camioneta en Villavicencio.",
    },

    {
        "slug": "lujos-y-accesorios-villavicencio",
        "menu": "Lujos y accesorios",
        "nombre": "Lujos y accesorios",
        "h1": "Lujos y accesorios para carros en Villavicencio",
        "h1_sub": "El detalle que le da personalidad a tu vehículo",
        "title": "Lujos para carros en Villavicencio | Accesorios — DACARS",
        "desc": "Lujos y accesorios para carros en Villavicencio: estribos, molduras, spoilers, tapetes, barras, emblemas, cámaras de reversa y más. Instalación profesional. Cotiza por WhatsApp.",
        "keywords": "lujos para carros villavicencio, accesorios para carros villavicencio, autolujos villavicencio, estribos villavicencio, tapetes para carro villavicencio, personalizacion de vehiculos villavicencio, lujos automotrices meta",
        "lead": "Estribos, molduras, spoilers, emblemas, tapetes y barras. Catálogo amplio y montaje que no deja huecos ni holguras.",
        "intro": [
            "Personalizar un carro en Villavicencio suele significar recorrer tres o cuatro locales: uno tiene el estribo, otro el tapete, otro instala. Y cada uno responde solo por su parte. DACARS existe en buena medida para evitar eso.",
            "Acá el catálogo de lujos y accesorios va desde lo estético —molduras, spoilers, emblemas, deflectores— hasta lo funcional: tapetes a medida, barras de techo, cámaras de reversa, sensores. Todo montado por el mismo equipo, con una sola garantía de trabajo y sin improvisar perforaciones.",
        ],
        "incluye_titulo": "Qué manejamos",
        "incluye": [
            ["Estribos y pisaderas", "Acceso más cómodo y una línea lateral más marcada, con anclajes al chasis."],
            ["Molduras y apliques", "Cromados, negros o al color del vehículo, según el estilo que busques."],
            ["Spoilers y deflectores", "Para el acabado trasero y para las ventanas, que en época de lluvia se agradecen."],
            ["Tapetes y protección de baúl", "A medida del modelo, que es lo que evita que se corran y se enrollen."],
            ["Barras de techo y portaequipajes", "Capacidad de carga sin sacrificar el interior."],
            ["Cámaras, sensores y emblemas", "Los detalles que suman comodidad diaria y presencia."],
        ],
        "razones_titulo": "Por qué importa quién lo instala",
        "razones": [
            ["Perforaciones", "Un accesorio mal montado deja huecos donde entra agua y empieza la corrosión. Se monta con criterio o no se monta."],
            ["Ajuste al modelo", "Una pieza genérica forzada al carro siempre se nota. Verificamos compatibilidad antes de comprometer la compra."],
            ["Clima del Llano", "Sol y aguaceros degradan materiales baratos rápido. Lo que recomendamos es lo que aguanta acá."],
        ],
        "proceso": [
            ["Nos dices qué buscas", "Con la marca, el modelo y el año revisamos qué aplica a tu vehículo y qué no."],
            ["Cotización con opciones", "Te damos alternativas por calidad y precio, no una sola opción a tomar o dejar."],
            ["Instalación", "Montaje en taller, con el vehículo protegido y sin perforar donde no se debe."],
            ["Revisión contigo", "Verificamos ajuste y acabado antes de entregarte el carro."],
        ],
        "precio_titulo": "Qué define el precio",
        "precio": [
            "El <strong>accesorio</strong> y su calidad de material y acabado.",
            "La <strong>marca, modelo y año</strong> del vehículo.",
            "Si el montaje requiere <strong>adaptación</strong> o solo anclaje directo.",
            "La <strong>cantidad de piezas</strong>: varios accesorios juntos se cotizan mejor que uno por uno.",
        ],
        "faq": [
            ["¿Tienen accesorios para mi marca y modelo?", "Manejamos catálogo amplio para los vehículos más comunes en la región. Mándanos marca, modelo y año por WhatsApp y te confirmamos disponibilidad antes de que te muevas al taller."],
            ["¿Instalan accesorios comprados en otro lado?", "Sí, siempre que la pieza sea compatible y esté en buen estado. Si vemos un riesgo para el vehículo te lo decimos antes de montarla."],
            ["¿Los tapetes son universales o a medida?", "Recomendamos siempre a medida del modelo. Los universales se corren, se enrollan y terminan estorbando en los pedales."],
            ["¿Cuánto se demora la instalación?", "La mayoría de accesorios estéticos se montan el mismo día. Los que implican cableado o anclajes al chasis toman más. Te confirmamos al cotizar."],
            ["¿Puedo hacer varios servicios en la misma visita?", "Sí, y es lo que más recomendamos: combinar lujos con polarizado o detailing en una sola entrada al taller para no quedarte sin carro dos veces."],
        ],
        "wa": "Hola DACARS, quiero cotizar lujos y accesorios para mi carro en Villavicencio.",
    },

    {
        "slug": "iluminacion-para-carros-villavicencio",
        "menu": "Iluminación",
        "nombre": "Iluminación automotriz",
        "h1": "Iluminación para carros en Villavicencio",
        "h1_sub": "LED, xenón, barras y exploradoras con conexión segura",
        "title": "Iluminación para carros en Villavicencio | LED y xenón — DACARS",
        "desc": "Iluminación automotriz en Villavicencio: LED, xenón, barras, exploradoras y luces de cortesía instaladas con cableado seguro. Ve mejor en vías sin alumbrado. Cotiza por WhatsApp.",
        "keywords": "iluminacion para carros villavicencio, luces led villavicencio, xenon villavicencio, barra led villavicencio, exploradoras villavicencio, luces auxiliares 4x4 meta",
        "lead": "Ver de noche en vía destapada no es lujo. Es seguridad, y depende tanto del equipo como del cableado.",
        "intro": [
            "Buena parte de las vías del Meta no tienen alumbrado. Súmale la neblina de ciertos tramos de la vía al Llano y los animales que se cruzan en carretera destapada, y la iluminación original de fábrica se queda corta rápido.",
            "El problema de la iluminación es que es el servicio donde más se improvisa: empalmes con cinta, cargas colgadas de cualquier fusible, barras conectadas sin relé. Eso funciona hasta que deja de funcionar, y cuando falla lo hace de noche. Acá lo hacemos con conexión protegida y cableado que no se recalienta.",
        ],
        "incluye_titulo": "Qué instalamos",
        "incluye": [
            ["Kits LED y xenón", "Upgrade de las luces principales para mejorar alcance y visibilidad."],
            ["Barras LED", "Para uso fuera de vía pública, montadas en parrilla, techo o bómper según el vehículo."],
            ["Exploradoras y auxiliares", "Apoyo para neblina y trocha, con su interruptor al alcance."],
            ["Luces de cortesía e interiores", "Iluminación de habitáculo, pisos y baúl."],
            ["Stops y direccionales", "Reemplazo y actualización de la iluminación trasera."],
            ["Cableado con protección", "Relés y fusibles donde corresponde, no empalmes sueltos."],
        ],
        "razones_titulo": "Por qué el cableado es lo que importa",
        "razones": [
            ["Carga eléctrica", "Una barra potente colgada de un circuito que no la soporta termina quemando algo. Se calcula antes de instalar."],
            ["Humedad del Llano", "Conexiones mal selladas más lluvia constante es igual a fallas intermitentes imposibles de rastrear."],
            ["Seguridad en vía", "Una luz que se apaga en plena trocha de noche es un problema serio, no una incomodidad."],
        ],
        "proceso": [
            ["Definimos el uso", "Ciudad, carretera o trocha. Cada uno pide un tipo de iluminación distinto."],
            ["Selección del equipo", "Te explicamos la diferencia real entre opciones, más allá de los lúmenes del empaque."],
            ["Instalación con protección", "Cableado ruteado, sellado y protegido, con relé y fusible donde corresponda."],
            ["Prueba y ajuste", "Verificamos funcionamiento y orientación antes de entregar."],
        ],
        "precio_titulo": "Qué define el precio",
        "precio": [
            "El <strong>tipo y potencia</strong> del equipo que elijas.",
            "La <strong>cantidad de puntos</strong> a instalar.",
            "La <strong>complejidad del cableado</strong>: no es lo mismo cambiar un bombillo que rutear una barra con su relé.",
            "Si requiere <strong>adaptación</strong> al vehículo o soportes especiales.",
        ],
        "faq": [
            ["¿Puedo usar una barra LED en vía pública?", "El uso de luces auxiliares en vía pública está regulado. Generalmente se instalan para uso fuera de carretera y se apagan en vía. Te asesoramos sobre el montaje, pero el uso responsable queda en manos del conductor."],
            ["¿El LED o el xenón dañan el sistema eléctrico?", "No, si la instalación respeta la carga del circuito y usa la protección adecuada. El daño aparece cuando se conecta sin calcular, que es justamente lo que evitamos."],
            ["¿Por qué mis luces nuevas parpadean?", "Casi siempre es un tema de compatibilidad con el sistema del vehículo o de una conexión mal hecha. Llévalo y lo diagnosticamos."],
            ["¿Instalan luces compradas por internet?", "Sí, si el equipo es compatible y está en buen estado. Te decimos antes si vemos un riesgo eléctrico."],
            ["¿Cuánto tarda la instalación?", "Un cambio simple sale el mismo día. Una instalación con cableado nuevo y relés toma más. Te lo confirmamos al cotizar."],
        ],
        "wa": "Hola DACARS, quiero cotizar iluminación para mi vehículo en Villavicencio.",
    },

    {
        "slug": "sonido-para-carros-villavicencio",
        "menu": "Sonido",
        "nombre": "Sonido para carros",
        "h1": "Sonido para carros en Villavicencio",
        "h1_sub": "Equipos, parlantes, amplificación e insonorización",
        "title": "Sonido para carros en Villavicencio | Parlantes — DACARS",
        "desc": "Instalación de sonido para carros en Villavicencio: pantallas, parlantes, amplificadores, subwoofers e insonorización. Montaje limpio y sin vibraciones. Cotiza por WhatsApp.",
        "keywords": "sonido para carros villavicencio, instalacion de sonido villavicencio, parlantes para carro villavicencio, amplificadores villavicencio, pantalla android carro villavicencio, insonorizacion vehicular meta",
        "lead": "Que suene fuerte es fácil. Que suene bien y no haga vibrar el carro entero es otra cosa.",
        "intro": [
            "En el Llano el sonido del carro es parte de la cultura, y eso hace que abunde el montaje hecho a las carreras: parlantes sin caja, amplificadores sin ventilación, cableado colgando bajo la alfombra. El resultado es un equipo que distorsiona, calienta y a los meses falla.",
            "Acá trabajamos el sonido como instalación técnica: cada componente con su alimentación correcta, el cableado ruteado y protegido, y la insonorización donde la lámina vibra. Lo que buscamos es que el equipo rinda lo que promete, no que solo suene duro.",
        ],
        "incluye_titulo": "Qué instalamos",
        "incluye": [
            ["Radios y pantallas", "Unidades con pantalla, conectividad y cámara integrada."],
            ["Parlantes y componentes", "Reemplazo de los originales por juegos que sí aprovechan la potencia."],
            ["Amplificadores", "Con su alimentación, fusible y ubicación ventilada."],
            ["Subwoofers y cajas", "Bajos limpios, con la caja adecuada al parlante y al espacio del vehículo."],
            ["Insonorización", "Tratamiento de puertas y paneles para que la lámina no vibre con el volumen."],
            ["Cámaras y sensores", "Reversa y apoyo de maniobra integrados al sistema."],
        ],
        "razones_titulo": "Lo que separa un buen montaje de uno malo",
        "razones": [
            ["Alimentación correcta", "Un amplificador mal alimentado distorsiona, calienta y se puede llevar por delante otros componentes."],
            ["Insonorización", "Sin tratar la lámina, buena parte de la potencia se va en hacer vibrar la puerta en lugar de sonar."],
            ["Cableado ordenado", "Ruteado y protegido significa menos ruido eléctrico, menos fallas y un carro que no huele a cable caliente."],
        ],
        "proceso": [
            ["Qué quieres lograr", "Claridad, potencia o las dos. De ahí sale el equipo, no al revés."],
            ["Armado del sistema", "Te proponemos una combinación coherente: de nada sirve un subwoofer de gama alta con un radio que no lo alimenta."],
            ["Instalación", "Montaje, cableado protegido e insonorización donde haga falta."],
            ["Ajuste y entrega", "Configuración del sistema y prueba contigo antes de entregar."],
        ],
        "precio_titulo": "Qué define el precio",
        "precio": [
            "Los <strong>componentes</strong> que elijas y su gama.",
            "Si es <strong>reemplazo directo</strong> o un sistema armado desde cero.",
            "La <strong>insonorización</strong>: cuántas puertas y paneles se tratan.",
            "El <strong>vehículo</strong>, porque algunos exigen adaptadores y marcos específicos.",
        ],
        "faq": [
            ["¿Instalar sonido daña la batería o el alternador?", "Un sistema dimensionado para el vehículo, no. Los problemas aparecen cuando se monta más potencia de la que el sistema eléctrico puede entregar, y eso lo revisamos antes de instalar."],
            ["¿Vale la pena insonorizar?", "Si vas a poner potencia, sí. Es la diferencia entre escuchar música y escuchar la puerta vibrando. También reduce el ruido de carretera."],
            ["¿Pueden instalar equipos que ya compré?", "Sí, si son compatibles con tu vehículo. Mándanos las referencias y lo confirmamos antes de que vayas al taller."],
            ["¿Puedo conservar el radio original?", "En muchos vehículos sí, mejorando parlantes y sumando amplificación. Depende del modelo; te decimos qué se puede hacer sin tocar el original."],
            ["¿Cuánto tarda la instalación?", "Un cambio de radio o parlantes sale rápido. Un sistema completo con insonorización toma más tiempo. Te confirmamos al cotizar."],
        ],
        "wa": "Hola DACARS, quiero cotizar sonido para mi carro en Villavicencio.",
    },

    {
        "slug": "llantas-villavicencio",
        "menu": "Llantas",
        "nombre": "Llantas",
        "h1": "Llantas en Villavicencio",
        "h1_sub": "Asesoría según el uso real de tu vehículo y montaje",
        "title": "Llantas en Villavicencio | Carros y camionetas — DACARS",
        "desc": "Llantas en Villavicencio con asesoría según tu uso: ciudad, carretera o trocha. Medidas correctas para carros y camionetas del Meta y montaje. Cotiza por WhatsApp.",
        "keywords": "llantas villavicencio, venta de llantas villavicencio, llantas para camioneta villavicencio, llantas todoterreno villavicencio, llantas at villavicencio, montaje de llantas meta",
        "lead": "La llanta correcta cambia el carro más que casi cualquier accesorio. La incorrecta te cuesta consumo, ruido y seguridad.",
        "intro": [
            "Un carro que solo se mueve entre Villavicencio y Bogotá no necesita la misma llanta que uno que sale a finca tres veces por semana. Y sin embargo mucha gente compra por precio o por estética, y termina con una llanta ruidosa, dura o que se gasta en un año.",
            "Acá primero preguntamos para qué usas el carro de verdad. De ahí sale la recomendación: medida, índice de carga y velocidad, y tipo de labrado. Después viene el montaje.",
        ],
        "incluye_titulo": "Cómo te asesoramos",
        "incluye": [
            ["Uso real del vehículo", "Ciudad, carretera, mixto o trocha. Es la variable que más pesa y la que menos se pregunta."],
            ["Medida e índices", "Respetar carga y velocidad no es opcional: es seguridad y es lo que exige el fabricante."],
            ["Tipo de labrado", "Carretera, mixto (A/T) o todoterreno, según el porcentaje real de destapado que manejes."],
            ["Comparación de opciones", "Te mostramos alternativas por precio y duración, no una sola."],
            ["Montaje", "Instalación de las llantas en el vehículo."],
            ["Recomendaciones de cuidado", "Presiones, rotación y qué revisar para que duren lo que deben."],
        ],
        "razones_titulo": "Lo que castiga una llanta en el Meta",
        "razones": [
            ["Calor del asfalto", "Las altas temperaturas aceleran el desgaste, sobre todo con presiones mal manejadas."],
            ["Destapado y piedra", "El labrado de carretera se corta y se pica rápido si le metes trocha seguido."],
            ["Carga", "Camionetas de trabajo cargadas exigen un índice de carga que no todas las llantas del mercado cumplen."],
        ],
        "proceso": [
            ["Nos dices tu vehículo y tu uso", "Marca, modelo, año y a dónde sale el carro realmente."],
            ["Te damos opciones", "Con medidas correctas y alternativas de precio y durabilidad."],
            ["Montaje", "Instalación en taller."],
            ["Recomendaciones", "Presiones y cuidados para que el juego rinda lo que debe."],
        ],
        "precio_titulo": "Qué define el precio",
        "precio": [
            "La <strong>medida</strong> y el rin de tu vehículo.",
            "El <strong>tipo de llanta</strong>: carretera, mixta o todoterreno.",
            "La <strong>marca y gama</strong> que elijas.",
            "La <strong>cantidad</strong>: el juego completo siempre sale mejor que unidad por unidad.",
        ],
        "faq": [
            ["¿Qué llanta me sirve si uso el carro en ciudad y finca?", "Normalmente una mixta (A/T), que da agarre en destapado sin volverse ruidosa en carretera. El punto exacto depende del porcentaje de cada uso: cuéntanos y te orientamos."],
            ["¿Puedo cambiar la medida original?", "Se puede en ciertos rangos, pero afecta velocímetro, consumo y a veces la suspensión. Te decimos hasta dónde es razonable en tu vehículo."],
            ["¿Debo cambiar las cuatro al tiempo?", "Es lo ideal para un desgaste parejo y un comportamiento predecible. Si no es posible, al menos por ejes completos y nunca mezclando labrados distintos en el mismo eje."],
            ["¿Cada cuánto debo revisar la presión?", "Con el calor de acá, mínimo una vez al mes y siempre antes de un viaje largo. La presión baja es la causa más común de desgaste irregular y de daños por calor."],
            ["¿Tienen la medida de mi camioneta?", "Escríbenos con la medida que aparece en el flanco de tu llanta actual y te confirmamos disponibilidad antes de que vayas."],
        ],
        "wa": "Hola DACARS, quiero cotizar llantas para mi vehículo en Villavicencio.",
    },

    {
        "slug": "pdr-desabolladura-sin-pintura-villavicencio",
        "menu": "PDR",
        "nombre": "PDR · Desabolladura sin pintura",
        "h1": "PDR en Villavicencio",
        "h1_sub": "Desabolladura sin pintura: sacamos el golpe, conservamos la pintura",
        "title": "PDR en Villavicencio | Desabolladura sin pintura — DACARS",
        "desc": "PDR en Villavicencio: desabolladura sin pintura para golpes de parqueadero y abolladuras menores. Se conserva la pintura original de fábrica, sin repintes. Cotiza por WhatsApp.",
        "keywords": "pdr villavicencio, desabolladura sin pintura villavicencio, quitar abolladuras carro villavicencio, reparar golpe puerta carro villavicencio, desabollado sin pintar meta",
        "lead": "Sin masilla, sin repinte, sin diferencia de tono. El golpe se saca desde adentro del panel.",
        "intro": [
            "El golpe clásico: alguien abre la puerta en el parqueadero de un centro comercial, o una rama cae sobre el capó. Un abollón pequeño, la pintura intacta. Y la solución tradicional —masillar, lijar y repintar— es desproporcionada: acabas de perder la pintura original de ese panel para siempre.",
            "El PDR (Paintless Dent Repair) trabaja distinto. Se accede por detrás del panel y se devuelve la lámina a su forma con herramientas específicas, sin tocar la pintura. Cuando el caso aplica, es más rápido, más barato y —lo más importante— el carro conserva su acabado de fábrica.",
        ],
        "incluye_titulo": "Cuándo aplica el PDR",
        "incluye": [
            ["Abolladuras de parqueadero", "Golpes de puerta, los más comunes y donde el PDR brilla."],
            ["Golpes en paneles amplios", "Puertas, capó, techo y laterales, donde hay superficie para trabajar."],
            ["Pintura sin daño", "La condición clave: si la pintura está intacta o apenas marcada, el PDR es la opción."],
            ["Marcas de granizo o impactos leves", "Abolladuras múltiples y poco profundas."],
            ["Golpes de rama o carga", "Hundimientos sin quiebre de la lámina."],
            ["Preparación para venta", "Sacar los golpes menores sin repintar sostiene el valor del vehículo."],
        ],
        "razones_titulo": "Por qué conviene frente a repintar",
        "razones": [
            ["Conserva la pintura original", "Un panel repintado se detecta y baja el valor del carro. El PDR no toca el acabado de fábrica."],
            ["Más rápido", "No hay tiempos de masilla, secado ni cabina de pintura de por medio."],
            ["Sin diferencia de tono", "No hay que igualar color, porque el color nunca se toca."],
        ],
        "proceso": [
            ["Evaluación del golpe", "Miramos profundidad, ubicación y acceso por detrás del panel. Acá se define si el PDR aplica o no."],
            ["Te decimos la verdad", "Si el caso necesita latonería y pintura, te lo decimos. No forzamos un PDR que va a quedar mal."],
            ["Trabajo del panel", "Se accede por detrás y se devuelve la lámina a su forma con presión controlada y paciencia."],
            ["Revisión bajo luz", "Verificamos el acabado contigo bajo luz directa, que es donde se ve todo."],
        ],
        "precio_titulo": "Qué define el precio",
        "precio": [
            "El <strong>tamaño y profundidad</strong> del golpe.",
            "La <strong>ubicación</strong>: un borde o un refuerzo interno complica mucho el acceso.",
            "La <strong>cantidad de abolladuras</strong> a trabajar.",
            "El <strong>panel</strong>: algunos permiten acceso fácil por detrás y otros no.",
        ],
        "faq": [
            ["¿Siempre se puede hacer PDR?", "No. Si la pintura está partida, si la lámina está estirada o si el golpe está sobre un refuerzo sin acceso, el caso pide latonería y pintura. Lo evaluamos y te decimos con franqueza cuál es tu caso."],
            ["¿Queda algún rastro del golpe?", "En un caso que aplica bien, el panel queda liso y sin marca visible. Por eso revisamos bajo luz directa contigo antes de entregar."],
            ["¿Es más barato que latonería y pintura?", "Normalmente sí, y además es más rápido. El ahorro real está en no perder la pintura original del panel."],
            ["¿Cuánto tiempo toma?", "Muchos casos salen el mismo día. Depende del número de abolladuras y de qué tan complicado sea el acceso al panel."],
            ["¿Sirve para varios golpes pequeños?", "Sí, es justamente donde más se usa: abolladuras múltiples y poco profundas repartidas en el carro."],
        ],
        "wa": "Hola DACARS, quiero cotizar un PDR (desabolladura sin pintura) en Villavicencio.",
    },
]


VIDEO_TPL = """
<section class="sec sec--alt">
  <div class="wrap vserv">
    <div class="vserv__media" data-reveal>
      <div class="clip">
        <div class="clip__media">
          <video class="clip__v" src="statics/video/@@VSLUG@@.mp4"
                 poster="statics/video/@@VSLUG@@.jpg"
                 preload="none" playsinline loop
                 aria-label="@@VNOMBRE@@ — DACARS Villavicencio"></video>
          <span class="clip__tag">En video</span>
          <button class="clip__btn" type="button" aria-label="Reproducir: @@VNOMBRE@@"></button>
        </div>
      </div>
    </div>
    <div class="vserv__copy">
      <p class="tag" data-reveal>En video</p>
      <h2 class="sec__title chrome" data-reveal>@@VNOMBRE@@</h2>
      <p class="sec__lead" data-reveal>@@VTEXTO@@</p>
      <a class="btn btn--primary" href="@@WA@@" target="_blank" rel="noopener" data-reveal>
        <svg class="marca" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
        Quiero algo así
      </a>
    </div>
  </div>
</section>
"""


# =========================================================
#  PLANTILLA
# =========================================================
def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def wa_url(texto):
    from urllib.parse import quote
    return "https://wa.me/" + WA + "?text=" + quote(texto)


def nav_html(activo):
    items = [
        ("index.html#servicios", "Servicios"),
        ("ppf-villavicencio.html", "PPF"),
        ("polarizados-villavicencio.html", "Polarizados"),
        ("detailing-villavicencio.html", "Detailing"),
        ("accesorios-4x4-villavicencio.html", "4x4"),
        ("index.html#contacto", "Contacto"),
    ]
    out = []
    for href, txt in items:
        cls = ' class="is-active"' if href.startswith(activo) and activo else ""
        out.append('      <a href="%s"%s>%s</a>' % (href, cls, txt))
    out.append('      <a class="btn btn--wa nav__cta" href="%s" target="_blank" rel="noopener">Cotizar</a>'
               % wa_url("Hola DACARS, quiero cotizar un servicio."))
    return "\n".join(out)


def jsonld(s):
    url = SITE + "/" + s["slug"] + ".html"
    negocio = {
        "@type": "AutoPartsStore",
        "@id": SITE + "/#dacars",
        "name": "DACARS",
        "telephone": "+" + WA,
        "address": {
            "@type": "PostalAddress",
            "streetAddress": DIR_CALLE,
            "addressLocality": CIUDAD,
            "addressRegion": DEPTO,
            "addressCountry": "CO",
        },
    }
    graph = [
        {
            "@type": "Service",
            "@id": url + "#servicio",
            "name": s["nombre"] + " en " + CIUDAD,
            "alternateName": s["h1"],
            "description": s["desc"],
            "url": url,
            "serviceType": s["nombre"],
            "category": "Automotriz",
            "provider": negocio,
            "areaServed": (
                [{"@type": "City", "name": CIUDAD}]
                + [{"@type": "AdministrativeArea", "name": DEPTO}]
                + [{"@type": "City", "name": m} for m in MUNICIPIOS[:6]]
            ),
            "availableChannel": {
                "@type": "ServiceChannel",
                "serviceUrl": wa_url(s["wa"]),
                "servicePhone": "+" + WA,
                "serviceLocation": {
                    "@type": "Place",
                    "name": "DACARS " + CIUDAD,
                    "address": negocio["address"],
                },
            },
            "hasOfferCatalog": {
                "@type": "OfferCatalog",
                "name": s["nombre"],
                "itemListElement": [
                    {"@type": "Offer", "itemOffered": {"@type": "Service", "name": t}}
                    for t, _ in s["incluye"]
                ],
            },
        },
        {
            "@type": "BreadcrumbList",
            "@id": url + "#migas",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Inicio", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": "Servicios", "item": SITE + "/#servicios"},
                {"@type": "ListItem", "position": 3, "name": s["h1"], "item": url},
            ],
        },
        {
            "@type": "FAQPage",
            "@id": url + "#faq",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": q,
                    "acceptedAnswer": {"@type": "Answer", "text": a},
                }
                for q, a in s["faq"]
            ],
        },
        {
            "@type": "WebPage",
            "@id": url + "#pagina",
            "url": url,
            "name": s["title"],
            "description": s["desc"],
            "inLanguage": "es-CO",
            "isPartOf": {"@id": SITE + "/#sitio"},
            "about": {"@id": url + "#servicio"},
            "breadcrumb": {"@id": url + "#migas"},
            "primaryImageOfPage": {"@type": "ImageObject", "url": SITE + "/statics/og-image.jpg"},
        },
    ]
    if s["slug"] in VIDEOS:
        slug, nombre, dur, desc, _ = VIDEOS[s["slug"]]
        graph.append({
            "@type": "VideoObject",
            "@id": url + "#video",
            "name": nombre,
            "description": desc,
            "duration": dur,
            "thumbnailUrl": SITE + "/statics/video/" + slug + ".jpg",
            "contentUrl": SITE + "/statics/video/" + slug + ".mp4",
            "inLanguage": "es-CO",
            "isFamilyFriendly": True,
            "publisher": {"@id": SITE + "/#organizacion"},
            "locationCreated": {"@type": "Place", "address": negocio["address"]},
        })

    return json.dumps({"@context": "https://schema.org", "@graph": graph},
                      ensure_ascii=False, indent=2)


def otros_servicios(actual):
    otros = [x for x in SERVICIOS if x["slug"] != actual][:6]
    filas = []
    for o in otros:
        filas.append(
            '        <a class="otro" href="%s.html">\n'
            '          <b>%s</b>\n'
            '          <span>en Villavicencio</span>\n'
            '        </a>' % (o["slug"], esc(o["menu"]))
        )
    return "\n".join(filas)


def build(s):
    url = SITE + "/" + s["slug"] + ".html"
    wa = wa_url(s["wa"])

    incluye = "\n".join(
        '        <li><span></span><div><b>%s</b> %s</div></li>' % (esc(t), esc(d))
        for t, d in s["incluye"]
    )
    razones = "\n".join(
        '        <article class="card" data-reveal>\n'
        '          <h3>%s</h3>\n'
        '          <p>%s</p>\n'
        '        </article>' % (esc(t), esc(d))
        for t, d in s["razones"]
    )
    pasos = "\n".join(
        '        <li class="step" data-reveal>\n'
        '          <span class="step__n">0%d</span>\n'
        '          <h3>%s</h3>\n'
        '          <p>%s</p>\n'
        '        </li>' % (i + 1, esc(t), esc(d))
        for i, (t, d) in enumerate(s["proceso"])
    )
    precio = "\n".join('        <li>%s</li>' % p for p in s["precio"])
    faq = "\n".join(
        '      <details data-reveal>\n'
        '        <summary>%s</summary>\n'
        '        <div><p>%s</p></div>\n'
        '      </details>' % (esc(q), esc(a))
        for q, a in s["faq"]
    )
    intro = "\n".join('      <p class="sec__lead" data-reveal>%s</p>' % p for p in s["intro"])
    barrios = " &middot; ".join(BARRIOS)
    munis = " &middot; ".join(MUNICIPIOS)

    html = """<!DOCTYPE html>
<html lang="es-CO">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>@@TITLE@@</title>
<meta name="description" content="@@DESC@@">
<meta name="keywords" content="@@KEYWORDS@@">
<meta name="robots" content="index, follow, max-snippet:-1, max-image-preview:large, max-video-preview:-1">
<meta name="theme-color" content="#04060c">
<meta name="author" content="DACARS VILLAVICENCIO S.A.S">
<link rel="canonical" href="@@URL@@">
<link rel="alternate" hreflang="es-co" href="@@URL@@">
<link rel="alternate" hreflang="x-default" href="@@URL@@">

<!-- Geolocalización para búsqueda local -->
<meta name="geo.region" content="CO-MET">
<meta name="geo.placename" content="Villavicencio, Meta, Colombia">
<meta name="geo.position" content="@@LAT@@;@@LON@@">
<meta name="ICBM" content="@@LAT@@, @@LON@@">

<meta property="og:type" content="website">
<meta property="og:locale" content="es_CO">
<meta property="og:site_name" content="DACARS">
<meta property="og:title" content="@@TITLE@@">
<meta property="og:description" content="@@DESC@@">
<meta property="og:url" content="@@URL@@">
<meta property="og:image" content="@@SITE@@/statics/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="DACARS — personalización de vehículos en Villavicencio">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="@@TITLE@@">
<meta name="twitter:description" content="@@DESC@@">
<meta name="twitter:image" content="@@SITE@@/statics/og-image.jpg">

<link rel="icon" type="image/png" href="statics/logo-dacars-sm.png">
<link rel="apple-touch-icon" href="statics/logo-dacars-sm.png">
<link rel="manifest" href="manifest.webmanifest">

<!-- Pantalla de carga: en línea a propósito, para que pinte antes que nada -->
<style>
#carga{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;overflow:hidden;
  background:radial-gradient(75% 60% at 50% 45%,#0a1327 0%,#04060c 72%);
  transition:opacity .55s ease,visibility .55s ease}
#carga.se-va{opacity:0;visibility:hidden;pointer-events:none}
#carga.se-va .carga__in{transform:scale(1.07);transition:transform .55s cubic-bezier(.4,0,1,1)}
#carga[hidden]{display:none}
html.sin-carga #carga{display:none}

/* Ancho fijo a propósito: la posición de los rayos está calculada en píxeles
   para que sus extremos se junten justo en el destello. Con un ancho elástico
   la geometría se desarma, así que en pantallas chicas se escala entera. */
.carga__in{position:relative;display:grid;place-items:center}
.carga__marca{position:relative;display:grid;place-items:center;width:400px;height:78px}
@media (max-width:480px){.carga__in{transform:scale(.74)}}

/* El wordmark aparece una vez y se queda */
.carga__marca img{height:44px;width:auto;opacity:0;
  animation:cargaEntra .6s cubic-bezier(.22,.61,.36,1) .05s forwards;
  filter:drop-shadow(0 0 24px rgba(10,92,255,.45))}
@keyframes cargaEntra{from{opacity:0;transform:scale(.95)}to{opacity:1;transform:none}}

/* Los cuatro rayos entran desde fuera y convergen, como en el logotipo */
.carga__rayo{position:absolute;width:2px;height:50px;border-radius:2px;opacity:0;
  background:linear-gradient(180deg,transparent,#00c8ff 30%,#0a5cff 72%,transparent);
  box-shadow:0 0 10px rgba(10,92,255,.95),0 0 30px rgba(10,92,255,.5);
  animation:cargaRayo 2.4s cubic-bezier(.16,1,.3,1) infinite}
/* Cada par converge en un vértice a 74 px del borde, justo antes del wordmark */
.carga__rayo--a{left:15%;top:-8px;--rot:-27deg;--dx:-58px;--dy:-30px}
.carga__rayo--b{left:15%;top:36px;--rot:27deg;--dx:-58px;--dy:30px;animation-delay:.06s}
.carga__rayo--c{right:15%;top:-8px;--rot:27deg;--dx:58px;--dy:-30px;animation-delay:.12s}
.carga__rayo--d{right:15%;top:36px;--rot:-27deg;--dx:58px;--dy:30px;animation-delay:.18s}
@keyframes cargaRayo{
  0%  {opacity:0;transform:translate(var(--dx),var(--dy)) rotate(var(--rot)) scaleY(.3)}
  18% {opacity:1;transform:translate(0,0) rotate(var(--rot)) scaleY(1)}
  62% {opacity:1;transform:translate(0,0) rotate(var(--rot)) scaleY(1)}
  100%{opacity:0;transform:translate(var(--dx),var(--dy)) rotate(var(--rot)) scaleY(.3)}
}

/* Destello en los puntos donde los rayos se juntan */
.carga__chispa{position:absolute;top:50%;width:13px;height:13px;border-radius:50%;
  margin-top:-6.5px;opacity:0;
  background:radial-gradient(circle,#fff 0%,#7fe3ff 32%,rgba(0,200,255,0) 70%);
  box-shadow:0 0 22px 6px rgba(0,200,255,.6);
  animation:cargaChispa 2.4s ease-out infinite}
.carga__chispa--i{left:16.8%}
.carga__chispa--d{right:16.8%;animation-delay:.12s}
@keyframes cargaChispa{
  0%,10%{opacity:0;transform:scale(.2)}
  20%{opacity:1;transform:scale(1)}
  38%{opacity:.3;transform:scale(.75)}
  70%,100%{opacity:0;transform:scale(.2)}
}

/* Brillo cromado que barre las letras. Se recorta con la silueta del propio
   logotipo, por eso barre el texto y no un rectángulo. */
.carga__brillo{position:absolute;inset:0;pointer-events:none;opacity:0;
  /* Banda angosta a propósito: con el fondo a 250% (1000 px), un 8% son ~80 px.
     Más ancha que eso no barre, solo ilumina el wordmark entero. */
  background:linear-gradient(100deg,transparent 46%,rgba(255,255,255,.95) 48.5%,
    rgba(180,230,255,.98) 50%,rgba(0,200,255,.75) 51.5%,transparent 54%);
  background-size:250% 100%;background-repeat:no-repeat;
  -webkit-mask-image:url(statics/logo-wordmark.png);mask-image:url(statics/logo-wordmark.png);
  -webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;
  -webkit-mask-position:center;mask-position:center;
  -webkit-mask-size:auto 44px;mask-size:auto 44px;
  animation:cargaBrillo 2.4s cubic-bezier(.45,0,.25,1) .45s infinite}
@keyframes cargaBrillo{
  0%{opacity:0;background-position:175% 0}
  9%{opacity:1}
  44%{opacity:1;background-position:-75% 0}
  52%,100%{opacity:0;background-position:-75% 0}
}

@media (prefers-reduced-motion:reduce){
  #carga,#carga.se-va .carga__in{transition:none}
  .carga__rayo{animation:none;opacity:.7;transform:rotate(var(--rot))}
  .carga__chispa{animation:none;opacity:.5}
  .carga__brillo{animation:none;opacity:0}
  .carga__marca img{animation:none;opacity:1}
}
</style>
<script>/* Ya la vio en esta sesión: no repetirla en cada página */
try{if(sessionStorage.getItem('dacars-visto'))document.documentElement.className+=' sin-carga'}catch(e){}</script>

<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Saira:ital,wght@0,500;0,600;0,700;1,700;1,800;1,900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="css/style.css">

<script type="application/ld+json">
@@JSONLD@@
</script>
</head>

<body>
<div id="carga" role="status" aria-live="polite" aria-label="Cargando DACARS">
  <div class="carga__in">
    <div class="carga__marca">
      <i class="carga__rayo carga__rayo--a"></i><i class="carga__rayo carga__rayo--b"></i>
      <i class="carga__rayo carga__rayo--c"></i><i class="carga__rayo carga__rayo--d"></i>
      <span class="carga__chispa carga__chispa--i"></span><span class="carga__chispa carga__chispa--d"></span>
      <img src="statics/logo-wordmark.png" alt="" width="600" height="117" fetchpriority="high">
      <span class="carga__brillo"></span>
    </div>
  </div>
</div>
<noscript><style>#carga{display:none}</style></noscript>
<script>/* cargaRespaldo: si js/app.js no llega (404, red caída, bloqueador de scripts),
la pantalla se retira igual. Va en línea porque no puede depender de un archivo externo. */
setTimeout(function(){var c=document.getElementById('carga');
if(c&&!c.hidden){c.classList.add('se-va');setTimeout(function(){c.hidden=true},600);}},4000);</script>

<a class="skip" href="#contenido">Saltar al contenido</a>

<div class="topbar">
  <div class="wrap topbar__in">
    <span class="topbar__item">
      <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 21s7-6.2 7-11a7 7 0 1 0-14 0c0 4.8 7 11 7 11Z"/><circle cx="12" cy="10" r="2.6"/></svg>
      @@DIR@@ &middot; Villavicencio, Meta
    </span>
    <span class="topbar__item topbar__item--hide">Especialistas en personalización de vehículos</span>
    <a class="topbar__item topbar__link" href="https://wa.me/@@WANUM@@" target="_blank" rel="noopener">
      <svg class="marca" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
      311 262 9406
    </a>
  </div>
</div>

<header class="head" id="head">
  <div class="wrap head__in">
    <a class="brand" href="index.html" aria-label="DACARS — inicio">
      <img src="statics/logo-wordmark.png" alt="DACARS Villavicencio" width="600" height="117">
    </a>
    <nav class="nav" id="nav" aria-label="Navegación principal">
@@NAV@@
    </nav>
    <button class="burger" id="burger" aria-label="Abrir menú" aria-expanded="false" aria-controls="nav">
      <span></span><span></span><span></span>
    </button>
  </div>
</header>

<main id="contenido">

<nav class="migas" aria-label="Ruta de navegación">
  <div class="wrap">
    <ol>
      <li><a href="index.html">Inicio</a></li>
      <li><a href="index.html#servicios">Servicios</a></li>
      <li aria-current="page">@@H1@@</li>
    </ol>
  </div>
</nav>

<section class="shero">
  <div class="shero__bg" aria-hidden="true"><span class="grid"></span><span class="glow glow--a"></span></div>
  <div class="wrap">
    <p class="tag" data-reveal>@@NOMBRE@@ &middot; Villavicencio, Meta</p>
    <h1 class="shero__title" data-reveal><span class="chrome">@@H1@@</span></h1>
    <p class="shero__sub" data-reveal>@@H1SUB@@</p>
    <p class="shero__lead" data-reveal>@@LEAD@@</p>
    <div class="hero__cta" data-reveal>
      <a class="btn btn--primary" href="@@WA@@" target="_blank" rel="noopener">
        <svg class="marca" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
        Cotizar por WhatsApp
      </a>
      <a class="btn btn--ghost" href="#faq">Preguntas frecuentes</a>
    </div>
  </div>
</section>

<section class="sec">
  <div class="wrap sec__narrow">
@@INTRO@@
  </div>
</section>
@@VIDEO@@

<section class="sec@@ALT1@@">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Alcance</p>
      <h2 class="sec__title chrome" data-reveal>@@INCLUYE_TITULO@@</h2>
    </header>
    <ul class="checks checks--2" data-reveal>
@@INCLUYE@@
    </ul>
  </div>
</section>

<section class="sec">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Contexto local</p>
      <h2 class="sec__title chrome" data-reveal>@@RAZONES_TITULO@@</h2>
    </header>
    <div class="cards cards--3">
@@RAZONES@@
    </div>
  </div>
</section>

<section class="sec sec--alt">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Cómo trabajamos</p>
      <h2 class="sec__title chrome" data-reveal>El paso a paso</h2>
    </header>
    <ol class="steps">
@@PASOS@@
    </ol>
  </div>
</section>

<section class="sec">
  <div class="wrap sec__narrow">
    <header class="sec__head">
      <p class="tag" data-reveal>Cotización</p>
      <h2 class="sec__title chrome" data-reveal>@@PRECIO_TITULO@@</h2>
      <p class="sec__lead" data-reveal>No publicamos listas de precios porque cada vehículo es distinto y preferimos no prometer cifras que después cambien. Estos son los factores que definen tu cotización:</p>
    </header>
    <ul class="factores" data-reveal>
@@PRECIO@@
    </ul>
    <p class="sec__foot" data-reveal>
      <a class="link" href="@@WA@@" target="_blank" rel="noopener">Pide tu cotización por WhatsApp &rarr;</a>
    </p>
  </div>
</section>

<section class="sec sec--alt" id="faq">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Preguntas frecuentes</p>
      <h2 class="sec__title chrome" data-reveal>@@NOMBRE@@ en Villavicencio: lo que más nos preguntan</h2>
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
      <h2 class="sec__title chrome" data-reveal>Dónde estamos y a quién atendemos</h2>
      <p class="sec__lead" data-reveal>
        El taller queda en la <strong>@@DIR@@</strong>, en Villavicencio. Estamos a pocos minutos
        de buena parte de la ciudad, así que si vives o trabajas en cualquiera de estas zonas, llegar es fácil.
      </p>
    </header>
    <p class="zonas" data-reveal><b>Barrios y zonas de Villavicencio:</b> @@BARRIOS@@ y el resto de la ciudad.</p>
    <p class="zonas" data-reveal><b>¿Vienes de otro municipio del Meta?</b> Recibimos vehículos de @@MUNICIPIOS@@ y demás municipios de la región. Escríbenos antes de viajar y coordinamos la cita para que aproveches el desplazamiento.</p>
    <div class="mapa-mini" data-reveal>
      <iframe title="Ubicación de DACARS en Villavicencio"
        src="https://www.google.com/maps?q=Carrera%2033%20%2324-60%20Barrio%20San%20Francisco%20Villavicencio%20Meta&amp;z=16&amp;output=embed"
        loading="lazy" referrerpolicy="no-referrer-when-downgrade" allowfullscreen></iframe>
    </div>
  </div>
</section>

<section class="sec sec--alt">
  <div class="wrap">
    <header class="sec__head">
      <p class="tag" data-reveal>Más servicios</p>
      <h2 class="sec__title chrome" data-reveal>Todo en el mismo taller</h2>
      <p class="sec__lead" data-reveal>Aprovecha la visita y resuelve varias cosas de una. Combinar servicios sale mejor que entrar al taller tres veces.</p>
    </header>
    <div class="otros">
@@OTROS@@
    </div>
  </div>
</section>

<section class="cierre">
  <div class="wrap cierre__in">
    <h2 class="chrome" data-reveal>@@H1@@</h2>
    <p data-reveal>Cuéntanos tu vehículo y qué necesitas. Te cotizamos y te damos tiempos reales.</p>
    <a class="btn btn--primary" href="@@WA@@" target="_blank" rel="noopener" data-reveal>
      <svg class="marca" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
      Escribir por WhatsApp
    </a>
  </div>
</section>

</main>

<footer class="foot">
  <div class="wrap foot__in">
    <div class="foot__brand">
      <img src="statics/logo-dacars-sm.png" alt="DACARS Villavicencio" width="420" height="306" loading="lazy">
      <p>Especialistas en personalización de vehículos.<br>@@DIR@@<br>Villavicencio, Meta &mdash; Colombia.</p>
    </div>
    <nav class="foot__col" aria-label="Servicios en Villavicencio">
      <h4>Servicios</h4>
      <a href="lujos-y-accesorios-villavicencio.html">Lujos y accesorios</a>
      <a href="accesorios-4x4-villavicencio.html">Accesorios 4x4</a>
      <a href="ppf-villavicencio.html">PPF</a>
      <a href="detailing-villavicencio.html">Detailing</a>
      <a href="polarizados-villavicencio.html">Polarizados</a>
      <a href="pdr-desabolladura-sin-pintura-villavicencio.html">PDR</a>
    </nav>
    <nav class="foot__col" aria-label="Más servicios">
      <h4>También</h4>
      <a href="iluminacion-para-carros-villavicencio.html">Iluminación</a>
      <a href="sonido-para-carros-villavicencio.html">Sonido</a>
      <a href="llantas-villavicencio.html">Llantas</a>
      <a href="index.html#nosotros">Nosotros</a>
      <a href="index.html#faq">Preguntas frecuentes</a>
    </nav>
    <div class="foot__col">
      <h4>Contacto</h4>
      <a href="https://wa.me/@@WANUM@@" target="_blank" rel="noopener">WhatsApp @@WATEL@@</a>
      <a href="https://www.google.com/maps/search/?api=1&amp;query=Carrera+33+%2324-60+Barrio+San+Francisco+Villavicencio+Meta" target="_blank" rel="noopener">@@DIR@@</a>
      <a href="https://www.instagram.com/dacarslujosvillavicencio/" target="_blank" rel="noopener">Instagram</a>
      <a href="https://www.facebook.com/Dacars.accesorios/" target="_blank" rel="noopener">Facebook</a>
    </div>
  </div>
  <div class="wrap foot__bar">
    <p>&copy; <span id="year">2026</span> DACARS VILLAVICENCIO S.A.S. &middot; NIT 901.798.060 &middot; Villavicencio, Meta.</p>
    <p class="foot__made">Hecho en Villavicencio, Meta.</p>
  </div>
</footer>

<a class="wa" href="@@WA@@" target="_blank" rel="noopener" aria-label="Escribir por WhatsApp">
  <svg class="marca" viewBox="0 0 24 24" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
  <span>Cotizar</span>
</a>

<script src="js/app.js" defer></script>
</body>
</html>
"""

    reemplazos = {
        "@@TITLE@@": esc(s["title"]),
        "@@DESC@@": esc(s["desc"]),
        "@@KEYWORDS@@": esc(s["keywords"]),
        "@@URL@@": url,
        "@@SITE@@": SITE,
        "@@LAT@@": str(LAT),
        "@@LON@@": str(LON),
        "@@JSONLD@@": jsonld(s),
        "@@NAV@@": nav_html(s["slug"]),
        "@@H1@@": esc(s["h1"]),
        "@@H1SUB@@": esc(s["h1_sub"]),
        "@@LEAD@@": esc(s["lead"]),
        "@@NOMBRE@@": s["nombre"],
        "@@INTRO@@": intro,
        "@@INCLUYE_TITULO@@": esc(s["incluye_titulo"]),
        "@@INCLUYE@@": incluye,
        "@@RAZONES_TITULO@@": esc(s["razones_titulo"]),
        "@@RAZONES@@": razones,
        "@@PASOS@@": pasos,
        "@@PRECIO_TITULO@@": esc(s["precio_titulo"]),
        "@@PRECIO@@": precio,
        "@@FAQ@@": faq,
        "@@OTROS@@": otros_servicios(s["slug"]),
        "@@BARRIOS@@": barrios,
        "@@MUNICIPIOS@@": munis,
        "@@DIR@@": DIR_CALLE,
        "@@WA@@": wa,
        "@@WANUM@@": WA,
        "@@WATEL@@": WA_TEL,
    }

    if s["slug"] in VIDEOS:
        vslug, vnombre, _, _, vtexto = VIDEOS[s["slug"]]
        seccion = (VIDEO_TPL.replace("@@VSLUG@@", vslug)
                            .replace("@@VNOMBRE@@", esc(vnombre))
                            .replace("@@VTEXTO@@", esc(vtexto))
                            .replace("@@WA@@", wa))
        reemplazos["@@VIDEO@@"] = seccion
        reemplazos["@@ALT1@@"] = ""          # el video ya usa el fondo alterno
    else:
        reemplazos["@@VIDEO@@"] = ""
        reemplazos["@@ALT1@@"] = " sec--alt"
    for k, v in reemplazos.items():
        html = html.replace(k, v)
    return html


def main():
    for s in SERVICIOS:
        destino = os.path.join(ROOT, s["slug"] + ".html")
        io.open(destino, "w", encoding="utf-8", newline="\n").write(build(s))
        print("generada  %s.html" % s["slug"])
    print("\n%d paginas de servicio listas." % len(SERVICIOS))


if __name__ == "__main__":
    main()
