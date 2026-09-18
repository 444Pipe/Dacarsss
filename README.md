# DACARS — Sitio web

Sitio de **DACARS VILLAVICENCIO S.A.S.** (Villavicencio, Meta — Colombia).
Especialistas en personalización de vehículos: lujos, accesorios 4x4, PPF, detailing,
polarizados, iluminación, sonido, llantas y PDR.

Estático: HTML + CSS + JavaScript, sin dependencias ni build. Se sube tal cual.

---

## Estructura

```
index.html                                    Portada
ppf-villavicencio.html                        ┐
polarizados-villavicencio.html                │
detailing-villavicencio.html                  │
accesorios-4x4-villavicencio.html             │ 9 landing pages de servicio,
lujos-y-accesorios-villavicencio.html         │ una por palabra clave local
iluminacion-para-carros-villavicencio.html    │
sonido-para-carros-villavicencio.html         │
llantas-villavicencio.html                    │
pdr-desabolladura-sin-pintura-villavicencio.html ┘
404.html                                      Página de error con la marca

css/style.css       Estilos y sistema de diseño
js/app.js           Menú móvil, reveals, nav activa, video, formulario → WhatsApp

statics/
  logo-*.png          Logotipos
  og-image.jpg        Imagen para redes
  hero video/         Los 5 reels originales (material fuente, NO se publica)
  video/              Lo que sí se publica:
    hero-16x9.mp4       Fondo del hero, escritorio (3,0 MB)
    hero-9x16.mp4       Fondo del hero, móvil (2,8 MB)
    hero-poster-*.jpg   Poster de cada uno
    reel-*.mp4          Los 5 reels listos para web + su poster

tools/
  build.py              Corre todo el pipeline en orden. EMPIEZA POR ACÁ.
  generar-servicios.py  Las 9 landings
  patch-index.py        SEO local en la portada
  patch-video.py        Hero, reels y testimonio
  patch-carga.py        Pantalla de carga
  fix-iconos.py         Glifos de marca
  usar-cloudinary.py    Reescribe las URLs del sitio a Cloudinary
  versionar-assets.py   Huella de contenido en css/js
  subir-cloudinary.py   Sube statics/ a Cloudinary (necesita .env, fuera del pipeline)
  cloudinary-map.json   Inventario de assets subidos (sin secretos, se commitea)
  generar-video.py      Procesa los reels con ffmpeg (fuera del pipeline)
  set-dominio.py        Cambia el dominio en todo el sitio

.env                Credenciales de Cloudinary. NO se commitea.
.env.example        Plantilla sin secretos.

Dockerfile  Caddyfile  .dockerignore  railway.json   Despliegue en Railway
sitemap.xml  robots.txt  manifest.webmanifest  .htaccess
```

## Ver en local

```bash
python -m http.server 5173
# http://localhost:5173
```

> El mapa de Google, las fuentes y **todos los assets (imágenes y video, que ahora
> vienen de Cloudinary)** necesitan internet. Si cambias el CSS y no ves los cambios,
> refresca con Ctrl+F5 (el navegador cachea la hoja de estilos).
>
> Para trabajar sin conexión: `python tools/usar-cloudinary.py --revertir` vuelve a
> las rutas locales de `statics/`, y `python tools/build.py` las devuelve a Cloudinary.
> El ida y vuelta es exacto: deja los archivos byte a byte como estaban.

---

## Identidad visual

Tomada del logotipo de la marca:

| Elemento | Valor |
|---|---|
| Fondo base | `#04060c` → `#071020` (negro azulado) |
| Azul de marca | `#0a5cff` |
| Azul claro | `#3d8bff` |
| Cian neón | `#00c8ff` |
| Texto | `#e9eef8` / secundario `#93a0b8` |
| Titulares | Saira, itálica 800/900, mayúsculas |
| Cuerpo | Inter |
| Efecto cromo | clase `.chrome` |

Todos los colores son variables CSS en `:root` dentro de [css/style.css](css/style.css).
Cambiar la marca completa = cambiar esas variables.

---

## Despliegue en Railway

El sitio se sirve con **Caddy** dentro de un contenedor. No hay build ni backend:
el contenido se copia tal cual y Caddy lo entrega.

| Archivo | Para qué |
|---|---|
| `Dockerfile` | Imagen basada en `caddy:2-alpine`. Valida el Caddyfile durante el build, así un error de sintaxis falla ahí y no en producción. |
| `Caddyfile` | Puerto (`$PORT` de Railway), compresión, caché, cabeceras de seguridad y la 404 con la marca. |
| `.dockerignore` | Deja fuera de la imagen `tools/`, `.htaccess`, el `README`, el `.env` y **todo `statics/`** (los assets los sirve Cloudinary). La imagen queda en ~0,4 MB. |
| `railway.json` | Le dice a Railway que use el Dockerfile, con healthcheck en `/`. |

### Desplegar

Conectando el repo desde el panel de Railway (recomendado): **New Project →
Deploy from GitHub repo → `444Pipe/Dacarsss`**. Detecta el `railway.json` y el
`Dockerfile` solo. Cada push a `main` redespliega.

O desde la terminal:

```bash
railway login
railway init          # crea el proyecto
railway up            # sube y despliega
railway domain        # genera la URL pública
```

### ⚠️ Después del primer despliegue: ajustar el dominio

El `canonical`, el Open Graph, el `sitemap.xml` y todo el JSON-LD apuntan hoy a
`https://www.dacars.com.co`. **Si el sitio va a vivir en la URL de Railway, hay que
cambiarlos**, porque un canonical que apunta a un dominio inexistente hace que
Google no indexe nada.

Es un solo comando con la URL que te dé `railway domain`:

```bash
python tools/set-dominio.py https://TU-URL.up.railway.app
git commit -am "Apuntar el sitio al dominio de producción"
git push
```

El script actualiza las 11 páginas, el sitemap, el robots, el `.htaccess` y los
scripts de `tools/` para que lo que regeneres después siga apuntando bien.
Cuando conecten `dacars.com.co`, se corre otra vez con ese dominio.

### Probar la imagen en local

```bash
docker build -t dacars-web .
docker run --rm -p 8080:8080 dacars-web
# http://localhost:8080
```

### Nota sobre el costo

Railway cobra por contenedor corriendo. Este sitio es 100% estático, así que en
**Cloudflare Pages, Netlify o GitHub Pages sería gratis** y con CDN global (mejor
latencia desde Villavicencio). Si eligieron Railway por tener todo en un mismo
lugar, perfecto — pero vale saber que hay alternativas sin costo para este caso.

---

## Pantalla de carga

El logotipo armándose: los cuatro rayos de neón entran desde fuera de cuadro y
convergen sobre el wordmark, destellan al llegar, y un brillo cromado barre las
letras de derecha a izquierda. Luego los rayos se retraen y el ciclo se repite
cada 2,4 s. **Sin barra ni porcentaje**: la animación sola indica que algo pasa.

### Lo que hay que saber antes de tocarla

**El CSS va en línea en el `<head>`, antes de las fuentes.** Si estuviera en
`style.css` aparecería tarde, justo cuando ya no hace falta.

**Solo se ve una vez por sesión.** El sitio tiene 11 páginas; una pantalla de
carga en cada clic interno sería insoportable. Un script diminuto marca el
`<html>` y la oculta antes de que pinte.

**El ancho es fijo (400 px) a propósito.** La posición de los rayos está
calculada en píxeles para que sus extremos se junten justo en el destello. Con
un ancho elástico la geometría se desarma, así que en pantallas chicas se escala
entera con `transform`.

**El brillo se recorta con la silueta del logotipo** (`mask-image`), por eso
barre las letras y no un rectángulo. La banda es angosta a propósito: con el
fondo a 250 % un 8 % son ~80 px. Más ancha que eso no barre, solo ilumina el
wordmark entero. Si cambias la altura del `<img>`, cambia también `ALTO` en
`tools/patch-carga.py` o el brillo se desalinea.

**La 404 no la lleva.** No carga `js/app.js`, así que la pantalla se quedaría los
4 s del respaldo en línea. En una página de error lo que se quiere es que
aparezca de una.

### Las redes de seguridad

Una pantalla de carga que no se va deja el sitio inservible, así que hay tres
caminos independientes para retirarla:

| Cuándo | Qué la retira | Verificado |
|---|---|---|
| 0,85–2,2 s | `js/app.js` — camino normal | sí, DOM |
| 4 s | `setTimeout` **en línea**, si `app.js` nunca llegó | sí, DOM |
| siempre | `<noscript>`, si no hay JavaScript | sí, render sin JS |

El `setTimeout` va en línea justamente porque no puede depender del archivo que
podría estar fallando.

### Ajustes

Los tiempos de salida están en `js/app.js` (`MINIMO`, `TOPE`); la animación y la
geometría, en `tools/patch-carga.py`. Se aplica con:

```bash
python tools/patch-carga.py     # idempotente; si ya hay una, la reemplaza
python tools/versionar-assets.py  # después de tocar css o js
```

Para quitarla de todo el sitio, borra el `<div id="carga">` y su `<style>`;
nada más depende de ella.

---

## Video

### Fondo del hero

Es un montaje de **12 tomas** sacadas de 4 de los reels, intercaladas en rotación
pareja (PPF → LED → Hummer → volante, tres vueltas), con disolvencias de 0,35 s.
Dura 21,9 s y arranca y termina en negro, así el loop no se nota.

El material se gradúa en el encode (`curves` levanta sombras y medios, con techo
en 0,96 para que ningún fotograma se vaya a blanco puro). El CSS **no vuelve a
oscurecerlo**: `.hero__video` solo ajusta saturación y contraste, y el trabajo de
legibilidad lo hace `.hero__veil`, que abre el centro y oscurece únicamente las
bandas con interfaz — el header arriba y el paso al marquee abajo.

**Encuadre.** El material es vertical (720x1280) y el hero es ancho. Recortar una
franja 16:9 a ancho completo solo deja 405 px de alto — el 32% de la escena, que en
pantalla se lee como un zoom enorme. En su lugar, de cada reel se toma una ventana
alta, se centra en el lienzo a su tamaño y el sobrante se rellena con una copia
ampliada y desenfocada del mismo fotograma, fundida con un degradado de 56 px para
que la unión no se lea como un borde. El campo de visión pasa del 32% al 52% en
escritorio, y en móvil el recorte lateral de `object-fit:cover` baja del 41% al 21%.

El tope de cada ventana lo marcan los subtítulos y la marca de agua quemados en los
reels: reel 1 hasta el 79%, reels 2 y 3 hasta el 80%, y el reel 5 solo hasta el 55%
(sus subtítulos van a media altura). Si cambias los tiempos, revisa el encuadre.

Se generan dos versiones y `js/app.js` elige según la pantalla:

| Archivo | Uso | Peso |
|---|---|---|
| `hero-16x9.mp4` | pantallas ≥ 861 px | 3,0 MB |
| `hero-9x16.mp4` | pantallas < 861 px | 2,8 MB |

**No se descarga el video** si el visitante tiene activado *reducir movimiento* o
*ahorro de datos*, ni si su conexión es 2G: en esos casos queda el poster, que
además va precargado. El video también se pausa solo al salir de pantalla.

> Los reels traen subtítulos quemados y la marca de agua DACARS. Cada recorte está
> calculado para dejarlos fuera de cuadro; por eso el del video de la Hummer es
> distinto (ahí los subtítulos van a media altura, no abajo). Si cambias los
> tiempos en el script, **revisa el encuadre antes de publicar**.

### Galería de reels

Los 5 videos completos están en la página, con `preload="none"`: no pesan nada
hasta que alguien le da play. Cuatro van en «Trabajos» y el testimonio del cliente
tiene su propia sección. Al reproducir uno se pausan los demás, y se pausan solos
al salir de pantalla.

### Regenerar el video

```bash
python tools/generar-video.py          # hero + reels
python tools/generar-video.py hero     # solo el fondo del hero
python tools/generar-video.py reels    # solo la galería
```

Requiere **ffmpeg** en el PATH. Los tiempos de cada toma están en la lista
`SECUENCIA` del script, comentados uno por uno.

### ⚠️ Falta la fecha de publicación de los videos

El schema `VideoObject` está completo salvo por `uploadDate`, que **Google exige**
para mostrar resultados enriquecidos de video. No la inventamos. Cuando tengas la
fecha real de cada reel en Instagram, agrégala en la lista `VIDEOS` de
`tools/patch-index.py` y `tools/generar-servicios.py`, y vuelve a correr los scripts.

---

## Cloudinary

Todos los assets (logos, `og-image`, posters y los 7 `.mp4`) se sirven desde
Cloudinary. Ningún HTML apunta ya a `statics/`, y `statics/` está excluido de la
imagen Docker vía [.dockerignore](.dockerignore).

**Cloud name:** `a0e9tgif` — es público, va en las URLs y no es un secreto.

### Credenciales

El API key y el API secret **solo** los usan los scripts de `tools/`. El sitio
publicado nunca los necesita: las URLs de entrega solo llevan el cloud name.

```bash
cp .env.example .env
# y pone el valor real de CLOUDINARY_URL
```

`.env` está en [.gitignore](.gitignore) y en `.dockerignore`. **Nunca se commitea
ni entra a la imagen.** Si el secreto se filtra (una captura, un chat, un pegado),
rotalo en <https://console.cloudinary.com> → Settings → API Keys y actualizá el `.env`.

### Flujo

```bash
python tools/subir-cloudinary.py     # sube statics/ y deja el inventario
python tools/build.py                # el paso 6 reescribe las URLs
python tools/usar-cloudinary.py --revertir   # vuelve a rutas locales
```

`subir-cloudinary.py` **no** está en `build.py`: necesita red y credenciales, y
solo hace falta cuando cambian los archivos de `statics/`. Deja
[tools/cloudinary-map.json](tools/cloudinary-map.json) con el `public_id` y la
versión de cada asset. **Ese archivo sí se commitea**: no tiene secretos y es lo
que `usar-cloudinary.py` necesita para construir las URLs.

Los `public_id` son fijos y derivan de la ruta, así que resubir sobrescribe en el
mismo sitio en vez de duplicar. **Después de resubir hay que correr `build.py`**,
o las URLs del sitio siguen apuntando a la versión anterior.

### Política de entrega (medida, no supuesta)

| Tipo | Transformación | Por qué |
|---|---|---|
| Imágenes | `f_auto,q_auto,c_limit,w_<ancho natural>` | WebP/AVIF automático |
| Iconos (favicon, manifest) | `f_png` | Declaran `type="image/png"` |
| `og-image` | `q_auto`, sin `f_auto` | Crawlers sociales |
| Video | **ninguna** | Ya viene optimizado de ffmpeg |

Las tres excepciones no son caprichos, son cosas que se midieron y salieron mal:

- **`c_limit` es obligatorio.** Sin él, Cloudinary *amplía*. Los posters de reel
  (608 px de ancho) servidos a `w_1080` pesaban **62% más** que el original.
- **Video sin transformar.** `q_auto` reencoda lo que `generar-video.py` ya había
  comprimido con ffmpeg: el testimonio pasaba de 6,9 a **9,3 MB**. Acá la ganancia
  es el CDN y sacar los MB del contenedor, no recomprimir.
- **`f_png` en los iconos.** Con `f_auto`, el favicon se entregaba como WebP
  mientras el `<link>` declaraba `type="image/png"`.

### Resultado medido

| | Antes | Después |
|---|---|---|
| Imágenes (las 11) | 1.047 KB | 536 KB (**−49%**) |
| `logo-dacars.png` | 465 KB | 149 KB (**−68%**) |
| Contexto Docker | 28,5 MB | 0,4 MB (**−98%**) |

> Refinamiento posible: `logo-dacars` se sirve a su ancho natural (1000 px) para
> que coincida con el `width`/`height` del JSON-LD, pero nunca se muestra a más de
> 380 px. Capándolo a `w_760` bajaría de 149 a 91 KB; habría que ajustar las
> dimensiones del JSON-LD a 760×554.

---

## SEO local implementado

### En cada página

- `<title>` y meta description con la palabra clave + «Villavicencio», todos bajo 70 caracteres.
- `<h1>` único que contiene la palabra clave exacta del servicio.
- Meta geográficas: `geo.region` (CO-MET), `geo.placename`, `geo.position`, `ICBM`.
- `canonical`, `hreflang` es-co y x-default, `robots` con `max-image-preview:large`.
- Open Graph y Twitter Card completos, con dimensiones y `alt` de la imagen.
- `alt` de imágenes con contexto local («PPF instalado en Villavicencio por DACARS»).

### Datos estructurados (JSON-LD)

| Página | Esquemas |
|---|---|
| Portada | `AutoPartsStore` + `AutoRepair`, `Organization`, `WebSite`, `WebPage`, `BreadcrumbList`, `ItemList` (servicios), `ItemList` de 5 `VideoObject`, `FAQPage` |
| Cada servicio | `Service`, `BreadcrumbList`, `FAQPage`, `WebPage` |
| PPF, 4x4, lujos, iluminación | además un `VideoObject` propio |

La ficha de negocio incluye NIT, dirección, teléfono, `geo`, `hasMap`, `serviceArea`
(radio de 80 km), `areaServed` con Villavicencio y 12 municipios del Meta, `sameAs`
de las redes y catálogo de los 9 servicios.

El `FAQPage` es el que puede hacer que Google muestre las preguntas desplegables
directamente en el resultado de búsqueda.

### Arquitectura de enlaces

Portada → 9 landings (desde cada tarjeta de servicio y desde el footer).
Cada landing → las otras 8 (bloque «Más servicios») y de vuelta a la portada.
Migas de pan visibles y marcadas con `BreadcrumbList`.

### Contenido

Cada landing tiene entre 700 y 900 palabras **únicas**: nada de copiar el mismo texto
cambiando el nombre del servicio, que es lo que Google penaliza como contenido delgado.
El ángulo local es real (grava de la vía al Llano, calor, trocha, municipios del Meta),
no relleno con el nombre de la ciudad repetido.

Sección de **Cobertura** en la portada y en cada landing, con 22 barrios de
Villavicencio y 12 municipios del Meta.

### Técnico

- `sitemap.xml` con las 10 URLs indexables y extensión de imágenes.
- `robots.txt` que permite a Google y a los rastreadores de IA (GPTBot, PerplexityBot).
- `manifest.webmanifest` para instalación en móvil.
- `.htaccess` con gzip, caché, HTTPS forzado, www forzado y 404 (solo Apache/cPanel;
  en Netlify o Vercel se ignora sin causar problemas).

---

## ⚠️ Qué falta hacer para que el SEO funcione de verdad

Lo de arriba es todo lo que se puede hacer **desde el código**. Pero en búsqueda local,
lo que más pesa no está en la web:

### 1. Google Business Profile (lo más importante de todo)

Reclamar y completar la ficha en <https://business.google.com>. Sin eso, el sitio
puede estar perfecto y aun así no aparecer en el mapa cuando alguien busca
«polarizados villavicencio». Hay que llenar:

- Categoría principal y secundarias (tienda de accesorios para automóviles, taller).
- Dirección exacta, horario, teléfono (el mismo de la web: 311 262 9406).
- Fotos reales del taller, del equipo y de trabajos.
- Los 9 servicios cargados uno por uno.
- **Pedir reseñas a los clientes.** Es el factor que más mueve la aguja.

Cuando tengas la ficha, copia sus coordenadas exactas y reemplaza en el código
`4.1420, -73.6340` (hoy es el centro aproximado de Villavicencio, no la puerta del taller).
Aparece en `tools/generar-servicios.py`, `tools/patch-index.py` y en el `<head>` de cada página.

### 2. Dominio

Reemplazar `https://www.dacars.com.co/` por el dominio real en:
`sitemap.xml`, `robots.txt`, `.htaccess`, los dos scripts de `tools/` y el `<head>` de cada página.

```bash
grep -rln "dacars.com.co" . --exclude-dir=.git
```

### 3. Search Console

Verificar el dominio en <https://search.google.com/search-console> y enviar el
`sitemap.xml`. Ahí se ve qué búsquedas traen gente y qué páginas no están indexadas.

### 4. Horarios

**No están publicados** porque no se encontró información pública confirmada, y no
queríamos inventarlos. Cuando los tengas, agrégalos al JSON-LD de la portada dentro
del objeto del negocio en `tools/patch-index.py`:

```json
"openingHoursSpecification": [{
  "@type": "OpeningHoursSpecification",
  "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"],
  "opens": "08:00", "closes": "18:00"
}]
```

### 5. Cobertura de municipios

Las páginas dicen que reciben vehículos de 12 municipios del Meta. **Confirma que
eso es cierto** y ajusta la lista `MUNICIPIOS` en los dos scripts de `tools/` si hace falta.

### 6. Fotos de trabajos (opcional)

La sección «Trabajos» ahora muestra los videos reales, así que **se retiró la grilla
de 6 fotos** que estaba con marcadores vacíos: al lado del video se veía como relleno.

Si más adelante quieres sumar fotos, el CSS de esa grilla (`.gal`, `.gal__i`) sigue en
`css/style.css` y el respaldo por JS también. Solo hay que volver a poner el bloque
`<div class="gal">…</div>` dentro de `#trabajos` y dejar las imágenes en
`statics/galeria/` como `1.jpg` … `6.jpg` (cuadradas, mínimo 900×900).

---

## Cómo editar las páginas de servicio

Se generan desde [tools/generar-servicios.py](tools/generar-servicios.py), donde está
todo el contenido de las 9 páginas en la lista `SERVICIOS` (títulos, textos, procesos,
preguntas frecuentes). Para cambiar algo:

```bash
# 1. edita el contenido en tools/generar-servicios.py
# 2. regenera TODO el sitio, en orden:
python tools/build.py
```

**Usa `tools/build.py`, no los scripts sueltos.** El orden importa y antes no
estaba escrito en ningún lado: `generar-servicios.py` sobrescribe las 9 landings
desde cero, así que todo lo que las retoca tiene que correr después.

| # | Script | Qué hace |
|---|---|---|
| 1 | `generar-servicios.py` | Crea las 9 landings |
| 2 | `patch-index.py` | Capa de SEO local en la portada |
| 3 | `patch-video.py` | Hero, reels y testimonio |
| 4 | `patch-carga.py` | Pantalla de carga |
| 5 | `fix-iconos.py` | Glifos de marca (WhatsApp, IG, FB) |
| 6 | `usar-cloudinary.py` | Manda los assets a Cloudinary |
| 7 | `versionar-assets.py` | Huella de contenido en css/js — **siempre último** |

Dos dependencias de orden que no se pueden invertir:

- Los pasos 1–5 emiten rutas locales (`statics/…`) y el **6** las convierte. Si
  corres solo `generar-servicios.py`, las landings quedan apuntando a archivos que
  **no están en la imagen de producción**.
- El **7** va después del 6 porque `versionar-assets.py` calcula el md5 de
  `js/app.js`, y `usar-cloudinary.py` **modifica** ese archivo (le mete las URLs
  de los posters del hero). Al revés, el `?v=` del HTML llevaría el hash del
  `app.js` viejo y los navegadores se quedarían con la copia cacheada.

Todos son idempotentes: se pueden correr las veces que quieras sin duplicar nada.
`build.py` no toca `css/style.css`.

> Si prefieres editar los `.html` a mano, hazlo — pero entonces **no vuelvas a correr
> los scripts**, porque sobrescriben esos archivos.

---

## Formulario de contacto

No requiere backend: al enviar, arma un mensaje con nombre, vehículo, servicio y
detalle, y abre WhatsApp con el texto ya escrito.

Si el número cambia, búscalo y reemplázalo:

```bash
grep -rln "573112629406" . --exclude-dir=.git
```

En [js/app.js](js/app.js) está además en la constante `WHATSAPP`.

---

## Publicar en otro lado

El despliegue principal es Railway (ver arriba). Al ser estático también sirve:

- **Netlify / Vercel / Cloudflare Pages** — arrastra la carpeta o conecta el repo.
- **GitHub Pages** — activa Pages sobre `main`.
- **Hosting tradicional (cPanel)** — sube todo por FTP a `public_html/`, incluido el `.htaccess`.

**No subas `statics/hero video/`**: son los 5 reels originales (47 MB) y solo sirven
para regenerar los montajes. Ya están en el `.gitignore`. La carpeta `tools/` tampoco
hace falta en producción (`robots.txt` ya la excluye).

Peso de lo que sí se publica: ~30 MB, de los cuales solo **3,0 MB se descargan al
abrir la página** (el fondo del hero). El resto son los reels, que esperan al play.

## Accesibilidad y rendimiento

- Contraste alto sobre fondo oscuro, foco visible, enlace «saltar al contenido».
- Respeta `prefers-reduced-motion`.
- Sin librerías externas: solo dos familias de Google Fonts.
- Imágenes con `loading="lazy"` y dimensiones declaradas.
