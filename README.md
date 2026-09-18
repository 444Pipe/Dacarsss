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
    hero-16x9.mp4       Fondo del hero, escritorio (3,5 MB)
    hero-3x4.mp4        Fondo del hero, móvil (2,5 MB)
    hero-poster-*.jpg   Poster de cada uno
    reel-*.mp4          Los 5 reels listos para web + su poster

tools/              Scripts que generan las páginas y procesan el video

Dockerfile  Caddyfile  .dockerignore  railway.json   Despliegue en Railway
sitemap.xml  robots.txt  manifest.webmanifest  .htaccess
```

## Ver en local

```bash
python -m http.server 5173
# http://localhost:5173
```

> El mapa de Google y las fuentes necesitan internet. Si cambias el CSS y no ves
> los cambios, refresca con Ctrl+F5 (el navegador cachea la hoja de estilos).

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
| `.dockerignore` | Deja fuera de la imagen los originales de video, `tools/`, `.htaccess` y el `README`. |
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

Los rayos del logotipo convergiendo sobre el wordmark cromado, con una barra de
progreso real. Tres decisiones que conviene conocer antes de tocarla:

**1. El CSS va en línea en el `<head>`, antes de las fuentes.** Si estuviera en
`style.css` aparecería tarde, justo cuando ya no hace falta.

**2. Solo se ve una vez por sesión.** El sitio tiene 11 páginas; una pantalla de
carga en cada clic interno sería insoportable. Un script diminuto en el `<head>`
marca el `<html>` y la oculta antes de que pinte.

**3. El progreso es real**, no una barra decorativa que cuenta sola: mira el
estado del DOM y las imágenes que no son `lazy` (las lazy no cuentan, porque no
cargan hasta que el visitante baje y esperarlas sería esperar para siempre).

### Las redes de seguridad

Una pantalla de carga que no se va deja el sitio inservible, así que hay tres
caminos independientes para retirarla:

| Cuándo | Qué la retira | Verificado |
|---|---|---|
| ~0,5–2,2 s | `js/app.js`, camino normal | sí, DOM a 1 s |
| 4 s | `setTimeout` **en línea**, si `app.js` nunca llegó | sí, DOM a 4,8 s |
| siempre | `<noscript>`, si no hay JavaScript | sí, render sin JS |

El `setTimeout` va en línea justamente porque no puede depender del archivo que
podría estar fallando. Queda además una animación CSS a los 5 s como cuarto
respaldo, pero no se confía en ella: no se pudo verificar, porque el reloj
virtual de Chrome headless no avanza animaciones CSS.

### Ajustes

Los tiempos están en `js/app.js` (`MINIMO`, `TOPE`) y el respaldo en línea en el
bloque `cargaRespaldo` de cada página. Para quitarla de todo el sitio, borra el
`<div id="carga">` y su `<style>`; nada más depende de ella.

Se aplica con `python tools/patch-carga.py` (idempotente).

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

Se generan dos versiones y `js/app.js` elige según la pantalla:

| Archivo | Uso | Peso |
|---|---|---|
| `hero-16x9.mp4` | pantallas ≥ 861 px | 3,5 MB |
| `hero-3x4.mp4` | pantallas < 861 px | 2,5 MB |

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
# 2. regenera:
python tools/generar-servicios.py
```

[tools/patch-index.py](tools/patch-index.py) hace lo mismo con la capa de SEO de la
portada y [tools/patch-video.py](tools/patch-video.py) con el video. Los dos son
idempotentes: se pueden correr las veces que quieras sin duplicar nada.

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

Peso de lo que sí se publica: ~30 MB, de los cuales solo **3,5 MB se descargan al
abrir la página** (el fondo del hero). El resto son los reels, que esperan al play.

## Accesibilidad y rendimiento

- Contraste alto sobre fondo oscuro, foco visible, enlace «saltar al contenido».
- Respeta `prefers-reduced-motion`.
- Sin librerías externas: solo dos familias de Google Fonts.
- Imágenes con `loading="lazy"` y dimensiones declaradas.
