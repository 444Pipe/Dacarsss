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
  paginas.py        Índice de las 9 landings
  views.py          Portada, landings, robots.txt, manifest
  sitemaps.py       Sitemap vivo: suma solos los productos nuevos
  templatetags/     pesos, foto (Cloudinary), whatsapp, json_txt
  tests.py          Que la migración no rompió el sitio indexado

catalogo/         Categorías, marcas, productos, fotos y variantes
inventario/       Movimientos de stock. Lo único que toca las existencias
pedidos/          Carrito (sesión), pedido y su ciclo de estados

templates/
  sitio/            base.html, los parciales y las 10 páginas migradas
  tienda/base.html  Base de las páginas nuevas (hereda de sitio/base.html)
  catalogo/         Listado, ficha, tarjeta y la franja para las landings
  pedidos/          Carrito, checkout y confirmación
  admin/            base_site (marca), login (entrada) y el tablero

static/css/style.css      El sistema de diseño (sin cambios desde el sitio viejo)
static/css/catalogo.css   Solo lo nuevo. Las landings no lo descargan
static/css/panel.css      La marca aplicada al admin de Django
static/js/app.js          Menú, reveals, video, formulario → WhatsApp

tools/            Lo que sigue sirviendo
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

## Las URLs no cambiaron

Esto es lo más importante de la migración y conviene no perderlo de vista.

| URL | Qué sirve |
|---|---|
| `/` | Portada |
| `/ppf-villavicencio.html` y las otras 8 | Las landings de servicio |
| `/index.html` | Redirige 301 a `/` |
| `/catalogo/` | El catálogo completo |
| `/catalogo/<categoria>/` | Una categoría |
| `/producto/<slug>/` | La ficha de un producto |
| `/carrito/`, `/pedido/` | Carrito y checkout (`noindex`) |
| `/admin/` | El panel |
| `/sitemap.xml`, `/robots.txt`, `/manifest.webmanifest` | Generados por Django |

**El `.html` del final se conserva a propósito.** Son las URLs que Google tiene
indexadas y a las que apunta el canonical de cada página. Cambiarlas obliga a
redirigir y a esperar semanas de reindexado, a cambio de nada.

Hay una prueba que compara, línea por línea, lo que sirve Django contra los HTML
de `legacy/html/`:

```bash
python manage.py test sitio
```

Si alguien edita una plantilla y se lleva por delante un pedazo de JSON-LD, esa
prueba falla. Es la red de seguridad del SEO: no se borra.

---

## El catálogo

### Producto y variante

**Lo que se vende es la variante, no el producto.** Una llanta no se vende: se
vende una medida (265/65R17). Una película no se vende: se vende un porcentaje.

- El **producto** agrupa y describe: nombre, fotos, descripción, compatibilidad.
- La **variante** tiene el SKU, el precio y las existencias.

Un producto sin medidas igual necesita una variante (la «única»); el panel exige
al menos una y el SKU se genera solo.

**Un producto sin variantes activas no se publica.** No tiene precio, así que no
se puede comprar, y publicarlo solo consigue que alguien pregunte por algo que no
se le puede vender. El tablero avisa cuáles están así.

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
mínimo, productos sin foto y productos sin precio. Cada ficha es un enlace a la
lista ya filtrada.

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
4. En **Fotos**: la de menor número es la principal.
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

### Agregar el Postgres

En el panel de Railway: **New → Database → PostgreSQL**. Queda en el mismo
proyecto y `DATABASE_URL` aparece sola en las variables del servicio web.

### El primer superusuario

```bash
railway run python manage.py createsuperuser
railway run python manage.py categorias_iniciales
```

### Después del primer despliegue: el dominio

El canonical, el Open Graph y el JSON-LD de las 10 páginas migradas apuntan hoy a
`https://www.dacars.com.co`. Si el sitio va a vivir en la URL de Railway, hay que
cambiarlos: **un canonical que apunta a un dominio inexistente hace que Google no
indexe nada.**

```bash
python tools/set-dominio.py https://TU-URL.up.railway.app
git commit -am "Apuntar el sitio al dominio de producción"
git push
```

Y en Railway → Variables: `DOMINIO=TU-URL.up.railway.app`. Son dos pasos porque
son dos fuentes: las plantillas migradas traen el dominio escrito a mano (herencia
del sitio estático), y todo lo nuevo lo arma con esa variable.

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
versiones que elige `app.js` según la pantalla: `hero-16x9.mp4` (3,0 MB) para
≥ 861 px y `hero-9x16.mp4` (2,8 MB) para menos.

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

- Las 10 URLs con `.html` responden 200 y `/index.html` redirige 301.
- Cada landing conserva su canonical, su JSON-LD y la pantalla de carga.
- El HTML servido es **idéntico** al del sitio estático.
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

- **No cambiar las URLs con `.html`.** Ver arriba.
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
