# -*- coding: utf-8 -*-
"""
Agrega (o actualiza) la pantalla de carga en todas las paginas.

La animacion es el logotipo armandose: los cuatro rayos de neon entran desde
fuera de cuadro y convergen sobre el wordmark, destellan al llegar, y un brillo
cromado barre las letras. Luego los rayos se retraen y el ciclo se repite.
Sin barra ni porcentaje: la animacion sola indica que algo esta pasando.

Decisiones que vale la pena conocer antes de tocar esto:

1. El CSS va EN LINEA en el <head>, antes de las fuentes. Si estuviera en
   style.css la pantalla apareceria tarde, justo cuando ya no hace falta.

2. Solo se ve una vez por sesion. El sitio tiene 11 paginas: una pantalla de
   carga en cada clic interno seria insoportable. Un script diminuto en el
   <head> marca el <html> y la oculta antes de que pinte.

3. Tiene tres redes de seguridad, porque una pantalla de carga que no se va
   deja el sitio inservible:
     - js/app.js la retira entre 0,85 y 2,2 s. Camino normal.
     - Un setTimeout EN LINEA la retira a los 4 s si app.js nunca llego
       (404, red caida, bloqueador). Va en linea justamente porque no puede
       depender del archivo que podria estar fallando.
     - <noscript> la oculta si no hay JavaScript del todo.

4. El brillo cromado se recorta con la silueta del propio logotipo usando
   mask-image, asi que barre las letras y no un rectangulo. Si cambias la
   altura del <img>, cambia tambien ALTO o el brillo se desalinea.

    python tools/patch-carga.py

Idempotente y actualizable: si ya hay una pantalla de carga puesta, la quita y
pone la de este archivo. Toca las .html y tools/generar-servicios.py.
"""

import io
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ALTO = "44px"   # alto del wordmark; el mask-size del brillo debe coincidir

ESTILO = """<!-- Pantalla de carga: en línea a propósito, para que pinte antes que nada -->
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
.carga__marca img{height:@@ALTO@@;width:auto;opacity:0;
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
  -webkit-mask-size:auto @@ALTO@@;mask-size:auto @@ALTO@@;
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
""".replace("@@ALTO@@", ALTO)

MARCA = """<div id="carga" role="status" aria-live="polite" aria-label="Cargando DACARS">
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

"""

ANCLA_HEAD = '<link rel="preconnect" href="https://fonts.googleapis.com">'
ANCLA_BODY = "<body>\n"

# Para poder reemplazar una pantalla de carga anterior por la de este archivo
RE_HEAD = re.compile(r'<!-- Pantalla de carga:.*?</script>\n\n(?=<link rel="preconnect")', re.S)
RE_BODY = re.compile(r'<div id="carga".*?cargaRespaldo.*?</script>\n\n', re.S)


def parchar(ruta, etiqueta):
    txt = io.open(ruta, encoding="utf-8").read()
    original = txt

    # si ya habia una, se quita para poner la nueva
    txt = RE_HEAD.sub("", txt)
    txt = RE_BODY.sub("", txt)

    if ANCLA_HEAD not in txt or ANCLA_BODY not in txt:
        print("  !! %s: no encontré dónde insertar" % etiqueta)
        return False

    txt = txt.replace(ANCLA_HEAD, ESTILO + "\n" + ANCLA_HEAD, 1)
    txt = txt.replace(ANCLA_BODY, ANCLA_BODY + MARCA, 1)

    if txt == original:
        return False
    io.open(ruta, "w", encoding="utf-8", newline="\n").write(txt)
    print("  %s" % etiqueta)
    return True


def main():
    n = 0
    for f in sorted(os.listdir(ROOT)):
        # 404.html queda fuera a propósito: no carga js/app.js, así que la
        # pantalla se quedaría los 4 s del respaldo en línea. En una página de
        # error lo que se quiere es que aparezca de una.
        if f.endswith(".html") and f != "404.html":
            n += parchar(os.path.join(ROOT, f), f)

    gen = os.path.join(ROOT, "tools", "generar-servicios.py")
    if os.path.exists(gen):
        n += parchar(gen, "tools/generar-servicios.py")

    print("\n%d archivos actualizados" % n if n else "\n(sin cambios)")


if __name__ == "__main__":
    main()
