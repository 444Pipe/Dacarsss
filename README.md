# DACARS — Sitio, catálogo y panel

Sitio de **DACARS VILLAVICENCIO S.A.S.** (Villavicencio, Meta — Colombia).
Personalización de vehículos: lujos, accesorios 4x4, PPF, detailing, polarizados,
iluminación, sonido, llantas y PDR.

**Django 5 + PostgreSQL + Cloudinary.** El sitio público, el catálogo de productos,
el inventario y el panel de administración corren en un solo servicio.

---

## Arrancar en local

```bash
pip install -r requirements.txt
cp .env.example .env          # y poné DEBUG=1
python manage.py migrate
python manage.py categorias_iniciales   # crea las 8 categorías del catálogo
python manage.py createsuperuser
python manage.py runserver
```

- Sitio: <http://localhost:8000>
- Panel: <http://localhost:8000/admin/>

Sin `DATABASE_URL` usa SQLite, y sin `CLOUDINARY_URL` guarda las fotos en `media/`.
Se puede trabajar sin ninguna credencial.

---

## Qué hay adentro

```
dacars/           Configuración del proyecto
  settings.py       Todo sale de variables de entorno; lee .env en local
  urls.py           El mapa de URLs
  admin.py          El AdminSite de DACARS (tablero con alertas)

sitio/            Las páginas que no salen de la base de datos
  paginas.py        Índice de las landings y el hub del Meta
  views.py          Portada, landings, robots.txt, manifest
  sitemaps.py       Sitemap vivo: suma solos los productos nuevos
  templatetags/     pesos, foto (Cloudinary), whatsapp, json_txt
  tests.py          Que la migración no rompió el sitio indexado

catalogo/         Categorías, marcas, productos, fotos y variantes
inventario/       Movimientos de stock. Lo único que toca las existencias
pedidos/          Carrito (sesión), pedido y su ciclo de estados

templates/
  sitio/            base.html, los parciales y las páginas del sitio
  tienda/base.html  Base de las páginas nuevas (hereda de sitio/base.html)
  catalogo/         Listado, ficha, tarjeta y la franja para las landings
  pedidos/          Carrito, checkout y confirmación
  admin/            base_site (marca), login (entrada) y el tablero

static/css/style.css      El sistema de diseño (sin cambios desde el sitio viejo)
static/css/catalogo.css   Solo lo nuevo. Las landings no lo descargan
static/css/panel.css      La marca aplicada al admin de Django
static/js/app.js          Menú, reveals, video, formulario → WhatsApp

tools/            Lo que sigue sirviendo
  fotos-catalogo.py     Foto del mostrador -> foto de estudio del catálogo
  subir-cloudinary.py   Sube statics/ a Cloudinary
  generar-video.py      Reprocesa los reels con ffmpeg
  set-dominio.py        Cambia el dominio en las plantillas
  cloudinary-map.json   Inventario de assets subidos

legacy/           El sitio estático anterior. Referencia, no corre
  html/             Los 11 HTML originales
  tools/            El pipeline de generación + el script de migración
  css/ js/          Las copias viejas de los assets
```

---

## Las URLs

Esto es lo más importante para el SEO y conviene no perderlo de vista.

| URL | Qué sirve |
|---|---|
| `/` | Portada |
| `/ppf-villavicencio` y las otras 11 | Las landings de servicio |
| `/personalizacion-de-vehiculos-meta` | El hub del departamento del Meta |
| `/<página>.html` y `/<página>/` | Redirigen 301 a `/<página>` |
| `/index.html` | Redirige 301 a `/` |
| `/catalogo/` | El catálogo completo |
| `/catalogo/<categoria>/` | Una categoría |
| `/producto/<slug>/` | La ficha de un producto |
| `/carrito/`, `/pedido/` | Carrito y checkout (`noindex`) |
| `/admin/` | El panel |
| `/sitemap.xml`, `/robots.txt`, `/manifest.webmanifest` | Generados por Django |

**Las páginas van sin `.html`** desde septiembre de 2026, cuando el sitio pasó a
`www.dacarslujos.com`. Las direcciones viejas con `.html` no se rompen:
responden 301 a la limpia y conservan el `?utm_` de las campañas. Son las que
ya circulan en Google, en Google Business, en Instagram y en los chats, y el
301 es lo que le dice a Google que traspase lo que la vieja había ganado.

Los enlaces internos, el canonical, el `og:url`, el JSON-LD y el sitemap van
todos a la URL limpia: un enlace interno que pase por la redirección funciona,
pero le cuesta un salto a cada visita. Las pruebas lo vigilan.

Hay un juego de pruebas que verifica las reglas de las que depende la búsqueda
local:

```bash
python manage.py test sitio
```

Comprueba, en cada página del sitio, que haya un solo `h1`, que el `title` y
la `description` sean únicos y quepan en el fragmento de Google, que el canonical
apunte al dominio configurado, que el JSON-LD parsee y traiga `WebPage`,
`FAQPage`, `Service` y `BreadcrumbList`, y que ningún enlace interno esté roto.

Es la red de seguridad del SEO: **no se borra.** Si alguien edita una plantilla y
se lleva por delante un pedazo de JSON-LD, esa prueba falla.

Antes comparaba línea por línea contra los HTML de `legacy/html/`. Cumplió su
trabajo —con ella se verificó la migración a Django— pero una prueba que exige
que la salida sea idéntica a la de antes también impide mejorarla: al acortar
las `description` y sumar páginas nuevas, las diez dejaron de coincidir con el
archivo congelado, y no por un error. Se cambió el texto congelado por las
reglas, que es lo que de verdad había que proteger.

---

## El catálogo

### Producto y variante

**Lo que se vende es la variante, no el producto.** Una llanta no se vende: se
vende una medida (265/65R17). Una película no se vende: se vende un porcentaje.

- El **producto** agrupa y describe: nombre, fotos, descripción, compatibilidad.
- La **variante** tiene el SKU, el precio y las existencias.

Un producto sin medidas que se quiera vender con carrito necesita una variante
(la «única»); el SKU se genera solo.

### A cotizar

**Un producto sin variantes activas se publica «a cotizar».** En vez de precio y
carrito, la tarjeta y la ficha muestran «Cotizar por WhatsApp», con un mensaje
que ya lleva el nombre del producto y el enlace de su ficha, y deja empezada la
frase «Mi vehículo es:». Es como sale hoy todo el catálogo: DACARS no publica
precios porque dependen del vehículo y de la instalación (lo mismo que dicen las
landings).

El día que a un producto se le carga una variante con precio, pasa solo a
venderse con carrito. No hay casilla que marcar.

Dos cosas cambian con un producto a cotizar:

- **No lleva JSON-LD de `Product`.** Google exige `offers` con precio, y un
  `Product` sin oferta le aparece a Search Console como error en cada ficha. Las
  migas (`BreadcrumbList`) salen igual.
- **No dice «agotado».** No tiene existencias cargadas, y decir agotado de algo
  que está en la vitrina sería mentir.

### Fotos: el producto y el producto instalado

Cada foto tiene un **tipo** («El producto» o «Instalado en un carro») y una
casilla de **imagen de referencia**. La tarjeta del listado muestra la primera
foto de tipo *instalado* al pasar el mouse, y la ficha le pone la etiqueta
«Imagen de referencia» a las que la tengan marcada.

La casilla es para las imágenes que no son una foto real de ese producto: las
generadas con IA (Higgsfield) y las del fabricante. Una escena generada muestra
cómo queda algo parecido instalado, no esa unidad, y la etiqueta evita prometer
algo que no es exactamente así.

### El catálogo inicial

Los 19 productos fotografiados en el local en septiembre de 2026 viven en
`catalogo/semillas/`: el texto en `catalogo.json` y las fotos en `fotos/`. El
contenedor los carga solo en el arranque (`catalogo_inicial --si-vacio`), en
segundo plano y **solo si no hay ningún producto**: corre una vez, y un
producto borrado a propósito no reaparece en el siguiente despliegue. Es todo o
nada: si una foto no sube a Cloudinary no queda nada a medias y el próximo
arranque lo reintenta.

En local:

```bash
python manage.py catalogo_inicial
```

Las fotos salen de [tools/fotos-catalogo.py](tools/fotos-catalogo.py), que
recorta la caja de la foto del mostrador (sin la mano ni el local), la endereza
y la pone sobre un fondo de estudio con los colores del sitio. Las fotos
originales están en la carpeta PRODUCTOS del Drive. Los textos se armaron con
lo que dice cada caja y lo que se pudo confirmar en la web; lo que no se pudo
confirmar quedó fuera. Los prompts para generar las versiones con Higgsfield
(estudio e instalado) están en `tools/higgsfield-prompts.json`.

### Existencias

Tres números por variante:

| Campo | Qué es |
|---|---|
| `stock` | Unidades físicas en el local |
| `reservado` | Unidades comprometidas por pedidos sin confirmar |
| `disponible` | `stock − reservado`. Es lo que se ofrece en la web |

Sin esa resta, dos clientes compran la última unidad el mismo día.

### Ciclo del pedido

```
nuevo       reserva      sube `reservado`, no toca `stock`
confirmado  vende        baja `stock` y `reservado`, deja movimiento
entregado   —            solo seguimiento
cancelado   libera       baja `reservado`   (si no se había confirmado)
            devuelve     sube `stock`       (si ya se había descontado)
```

El campo `stock_descontado` decide cuál de las dos vueltas corresponde. Sin él
habría que adivinarlo a partir del estado, y el día que alguien agregue un estado
nuevo la cuenta se rompe en silencio.

---

## El panel

Es el admin de Django con la marca de DACARS y un tablero de entrada que muestra
lo que hay que atender hoy: pedidos sin responder, agotados, existencias bajo el
mínimo y productos sin foto. También cuenta los productos a cotizar (sin
precio), que no es una alerta sino cómo sale hoy el catálogo. Cada ficha es un
enlace a la lista ya filtrada.

### Cómo está hecha la apariencia

El admin de Django se tematiza por variables CSS, así que
[static/css/panel.css](static/css/panel.css) es sobre todo redefinirlas con la
paleta de la marca. Se declaran en los cuatro selectores de tema (`:root` más
los tres `data-theme`) a propósito: Django define la versión clara y la oscura
con la misma especificidad y, como esta hoja carga después, gana la nuestra en
los tres modos. El panel se ve igual siempre, que es lo que se quiere de una
herramienta de trabajo — por eso el selector claro/oscuro está escondido. Para
devolverlo, borrá la regla `.theme-toggle` de esa hoja.

Los colores que el panel pinta desde Python (las columnas de existencias, el
estado de cada pedido) están en [dacars/colores.py](dacars/colores.py), y son
las versiones claras de la paleta: sobre el fondo oscuro del panel, un rojo
`#b91c1c` no se lee.

`templates/admin/login.html` es la pantalla de entrada, sin la barra de
encabezado del admin: ahí todavía no hay dónde navegar.

### Cargar un producto

1. **Catálogo → Productos → Agregar**
2. Nombre, categoría, resumen (la línea que se lee en la tarjeta).
3. En **Precios y existencias**: una fila por medida. El SKU se genera solo.
   Sin ninguna fila, el producto sale «a cotizar».
4. En **Fotos**: la de menor número es la principal. Si hay una del producto
   instalado, marcale el tipo «Instalado en un carro»; si es generada con IA o
   del fabricante, marcá también «imagen de referencia».
5. Guardar. Ya está en `/catalogo/`.

### Cuándo llega mercancía

**Inventario → Movimientos → Agregar**, tipo «Entrada». Suma al stock y queda
anotado con quién lo cargó y cuándo.

### Cambiar existencias a mano

Se puede, en **Variantes y existencias**, escribiendo el número directo en la
lista. No es un atajo por fuera del sistema: el panel compara con lo que había y
manda la diferencia como un **ajuste**, con tu nombre y la fecha.

> Ese es el motivo por el que existe `inventario/servicios.py`. **Nada en el
> proyecto escribe `variante.stock = ...` directamente.** Todo pasa por ahí, que
> bloquea la fila, hace la cuenta y deja el movimiento. Si se permitiera el
> atajo, el historial tendría huecos justo donde más se lo necesita: el día que
> falten tres llantas.

### Los pedidos

Las líneas de un pedido son de **solo lectura**: el precio quedó congelado al
momento de la compra y las unidades ya están reservadas o descontadas. Si un
pedido cambia, se cancela (la mercancía vuelve sola) y se arma de nuevo.

Confirmar descuenta del inventario. Cancelar devuelve. Da lo mismo hacerlo desde
las acciones de la lista o cambiando el estado en el formulario.

---

## Desplegar en Railway

```
Dockerfile     python:3.12-slim + gunicorn. collectstatic corre en el build
railway.json   Le dice a Railway que use el Dockerfile, healthcheck en /
```

Cada push a `main` redespliega, y `migrate` corre al arrancar el contenedor.

### Variables del servicio

| Variable | Para qué |
|---|---|
| `SECRET_KEY` | Obligatoria. `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DATABASE_URL` | La inyecta el plugin de Postgres |
| `CLOUDINARY_URL` | Las fotos que suba el comercio. Sin esto van al disco del contenedor y **se pierden en cada despliegue** |
| `DOMINIO` | El dominio, sin `https://` |
| `DEBUG` | No definirla, o `0` |
| `WHATSAPP` | Opcional. Por defecto `573112629406` |
| `ADMIN_USUARIO` / `ADMIN_CLAVE` | Solo para crear el primer usuario del panel. **Se borra `ADMIN_CLAVE` después** (ver abajo) |

### Agregar el Postgres

En el panel de Railway: **New → Database → PostgreSQL**. Queda en el mismo
proyecto y `DATABASE_URL` aparece sola en las variables del servicio web.

### El primer usuario del panel

La base vive **solo en la nube**. El Postgres de Railway no es alcanzable
desde afuera si el servicio no tiene proxy TCP publico, asi que
`createsuperuser` no se puede correr contra el desde una maquina de trabajo, y
`railway run` tampoco sirve: inyecta las variables pero el hostname interno
sigue sin resolver desde tu red.

Por eso el usuario se crea **desde adentro del contenedor**, en el arranque:

1. En el servicio web -> Variables, definir `ADMIN_USUARIO` y `ADMIN_CLAVE`
   (y opcionalmente `ADMIN_EMAIL`).
2. Railway redespliega solo. En el log aparece `Usuario «...» creado`.
3. Entrar al panel con esas credenciales.
4. **Borrar `ADMIN_CLAVE`.**

El punto 4 no es opcional. Mientras esa variable siga definida, cada
despliegue vuelve a escribir esa contrasena: si la cambias desde el panel, el
siguiente deploy la pisa. Y una contrasena no tiene por que quedar guardada en
las variables del servicio.

Sirve igual para recuperar el acceso: se vuelve a poner `ADMIN_CLAVE`, se
espera el redespliegue, se entra, y se borra otra vez.

Las 8 categorias del catalogo se siembran solas en el primer arranque, pero
solo si no hay ninguna. Una categoria borrada a proposito no reaparece en el
siguiente despliegue.

### Después del primer despliegue: el dominio

El canonical, el Open Graph y el JSON-LD salen todos de la variable `DOMINIO`.
Cambiar el dominio es **un solo paso**, en Railway → Variables:

```
DOMINIO=www.el-dominio-que-sea.com
```

**Un canonical que apunta a un dominio inexistente hace que Google no indexe
nada**, así que vale la pena confirmarlo después de desplegar:

```bash
curl -s https://tu-dominio/ | grep canonical
```

Antes eran dos fuentes y dos pasos: las plantillas migradas traían el dominio
escrito a mano, herencia del sitio estático, así que cambiar la variable movía el
sitemap pero **no** el canonical de las diez landings. Las 218 apariciones pasaron
a `{{ negocio.sitio }}`; `tools/set-dominio.py` ya no hace falta para esto.

### Nota sobre el costo

Antes esto era un contenedor de Caddy de 0,4 MB sirviendo HTML. Ahora es Django
con una base de datos: más consumo, y Postgres se factura aparte. Es el precio de
que el comercio pueda cargar productos sin tocar código.

---

## Cloudinary

Dos usos distintos en la misma cuenta (`a0e9tgif`, el cloud name es público):

| Carpeta | Qué guarda | Quién sube |
|---|---|---|
| `dacars/` | Logos, `og-image`, posters y los 7 `.mp4` | `tools/subir-cloudinary.py` |
| `dacars/catalogo/` | Las fotos de producto | El comercio, desde el panel |

Están separadas para que se pueda limpiar el catálogo sin tocar los logos ni el
video.

Las fotos de producto se entregan con `f_auto,q_auto,c_limit,w_<ancho>`, que aplica
el filtro `foto` de `sitio/templatetags/dacars.py`.

> **`c_limit` no es opcional.** Sin él Cloudinary *amplía* la imagen: los posters
> de reel (608 px de ancho) servidos a `w_1080` pesaban **62% más** que el
> original. Está medido.

Los assets del sitio (logos, video) siguen manejándose igual que antes:

```bash
python tools/subir-cloudinary.py   # sube statics/ y actualiza el inventario
```

---

## Identidad visual

Sin cambios respecto del sitio anterior. Todo son variables CSS en `:root` dentro
de [static/css/style.css](static/css/style.css); cambiar la marca completa =
cambiar esas variables.

| Elemento | Valor |
|---|---|
| Fondo base | `#04060c` → `#071020` |
| Azul de marca | `#0a5cff` |
| Azul claro | `#3d8bff` |
| Cian neón | `#00c8ff` |
| Texto | `#e9eef8` / secundario `#93a0b8` |
| Titulares | Saira, itálica 800/900, mayúsculas |
| Cuerpo | Inter |

[static/css/catalogo.css](static/css/catalogo.css) usa esas mismas variables y no
redefine ninguna. Lo cargan solo las páginas del catálogo, y las landings solo si
hay productos que mostrar.

---

## La pantalla de carga

Sigue funcionando igual, ahora en [templates/sitio/base.html](templates/sitio/base.html).

El logotipo armándose: los cuatro rayos de neón entran desde fuera de cuadro y
convergen sobre el wordmark, destellan al llegar, y un brillo cromado barre las
letras. El ciclo se repite cada 2,4 s.

Lo que conviene saber antes de tocarla:

- **El CSS va en línea en el `<head>`**, antes de las fuentes. En `style.css`
  aparecería tarde, justo cuando ya no hace falta.
- **Solo se ve una vez por sesión.** Un script diminuto marca el `<html>` y la
  oculta antes de que pinte.
- **El ancho es fijo (400 px) a propósito.** La posición de los rayos está
  calculada en píxeles; con un ancho elástico la geometría se desarma.
- **El brillo se recorta con la silueta del logotipo** (`mask-image`).

Tres caminos independientes la retiran, porque una pantalla de carga que no se va
deja el sitio inservible:

| Cuándo | Qué la retira |
|---|---|
| 0,85–2,2 s | `app.js`, el camino normal |
| 4 s | Un `setTimeout` **en línea**, si `app.js` nunca llegó |
| siempre | `<noscript>`, si no hay JavaScript |

---

## Video

Sin cambios. El fondo del hero es un montaje de 12 tomas sacadas de 4 reels
(21,9 s, arranca y termina en negro para que el loop no se note), en dos
versiones que elige `app.js` según la pantalla: `hero-16x9.mp4` (3,5 MB) para
≥ 861 px y `hero-3x4.mp4` (2,5 MB) para menos. Las URLs de video y poster
viven solo en el `<video>` de `templates/sitio/index.html` (`data-src-*` y
`data-poster-*`); `app.js` las lee de ahí.

Ojo: el `hero-9x16.mp4` que deja `generar-video.py` en `statics/video/` **no
está en Cloudinary**. Mientras el sitio lo pidió, el hero salía vacío en
celular (404 en video y poster). Para usarlo hay que subirlo primero con
`subir-cloudinary.py` y después cambiar las URLs con la versión del mapa.

No se descarga si el visitante tiene activado *reducir movimiento* o *ahorro de
datos*, ni en 2G. Se pausa solo al salir de pantalla.

```bash
python tools/generar-video.py          # hero + reels (necesita ffmpeg)
```

> Los reels traen subtítulos quemados y la marca de agua. Cada recorte está
> calculado para dejarlos fuera de cuadro. Si cambiás los tiempos en `SECUENCIA`,
> **revisá el encuadre antes de publicar.**

---

## Pruebas

```bash
python manage.py test           # las 62
python manage.py test sitio     # que el sitio viejo sigue igual
python manage.py test pedidos   # el ciclo del pedido y el stock
python manage.py test inventario
python manage.py test catalogo
```

Lo que cubren, por si hay que decidir qué no romper:

- Todas las URLs con `.html` responden 200 y `/index.html` redirige 301.
- Cada landing conserva su canonical, su JSON-LD y la pantalla de carga.
- Un solo `h1` por página; `title` y `description` únicos y dentro del corte.
- El JSON-LD parsea y trae los tipos que Google lee.
- Ningún enlace interno roto, y las páginas nuevas están enlazadas desde la
  portada (una landing sin enlaces entrantes se rastrea tarde y mal).
- Un pedido reserva, confirma y cancela moviendo el inventario como corresponde.
- Dos pedidos no se llevan la misma última unidad.
- Editar existencias en el panel deja un ajuste a nombre de quien lo hizo.
- El historial de inventario se puede mirar pero no editar ni borrar.
- Subir un precio no cambia un pedido viejo.
- El carrito suelta lo que se dio de baja o se agotó.
- Un pedido ajeno no se puede espiar por el número.
- El proyecto arranca aunque `CLOUDINARY_URL` venga mal escrita.
- Todas las pantallas del panel abren, con datos en todos sus estados.

---

## Lo que sigue faltando para que el SEO funcione

Esto no cambió con la migración: sigue siendo lo que más pesa y nada de eso está
en el código.

### 1. Google Business Profile (lo más importante)

Reclamar y completar la ficha en <https://business.google.com>. Sin eso el sitio
puede estar perfecto y no aparecer en el mapa cuando alguien busca «polarizados
villavicencio». Categoría, dirección, horario, fotos reales, los 9 servicios
cargados uno por uno, y **pedir reseñas**: es el factor que más mueve la aguja.

Cuando tengas la ficha, copiá sus coordenadas exactas y reemplazá `4.142, -73.634`
(hoy es el centro aproximado de Villavicencio, no la puerta del taller). Está en
`templates/sitio/*.html` y en `templates/tienda/base.html`.

### 2. Search Console

Verificar el dominio en <https://search.google.com/search-console> y enviar el
`sitemap.xml`.

### 3. Horarios

No están publicados porque no se encontró información confirmada. Cuando los
tengas, van en el JSON-LD de la portada
([templates/sitio/index.html](templates/sitio/index.html)), dentro del objeto del
negocio:

```json
"openingHoursSpecification": [{
  "@type": "OpeningHoursSpecification",
  "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
  "opens": "08:00", "closes": "18:00"
}]
```

### 4. Fecha de publicación de los videos

El schema `VideoObject` está completo salvo `uploadDate`, que Google exige para
mostrar resultados enriquecidos. No la inventamos. Cuando tengas la fecha real de
cada reel en Instagram, agregala en el JSON-LD de las plantillas.

### 5. Cobertura de municipios

Las páginas dicen que reciben vehículos de 12 municipios del Meta. Confirmá que
sea cierto.

---

## Cosas que conviene no hacer

- **No quitar las redirecciones de los `.html` ni renombrar un slug.** Ver
  arriba: romperían las direcciones que ya circulan.
- **No editar `variante.stock` fuera de `inventario/servicios.py`.** El número
  quedaría sin historia.
- **No volver a correr los scripts de `legacy/tools/`.** Sobrescriben las
  plantillas con el contenido del sitio viejo y se llevan puesto todo lo nuevo.
  Están archivados como referencia.
- **No editar las líneas de un pedido ya creado.** Cancelalo y armá otro.
- **No commitear el `.env`.** Está en `.gitignore` y en `.dockerignore`. Si el
  secreto de Cloudinary se filtra, rotalo en la consola y actualizá el `.env`.

---

## Accesibilidad y rendimiento

- Contraste alto sobre fondo oscuro, foco visible, enlace «saltar al contenido».
- Respeta `prefers-reduced-motion`.
- Sin librerías de JavaScript: solo dos familias de Google Fonts.
- Imágenes con `loading="lazy"` y dimensiones declaradas.
- La ficha de producto funciona sin JavaScript: el selector de medida es un
  `<input type=radio>` y el servidor revalida el stock igual.
