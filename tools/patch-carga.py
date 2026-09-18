# -*- coding: utf-8 -*-
"""
Agrega la pantalla de carga a todas las paginas.

Decisiones que vale la pena conocer antes de tocar esto:

1. El CSS va EN LINEA en el <head>, antes de las fuentes. Si estuviera en
   style.css la pantalla aparecería tarde, justo cuando ya no hace falta.

2. Solo se ve una vez por sesion. El sitio tiene 11 paginas: una pantalla de
   carga en cada clic interno seria insoportable. Un script diminuto en el
   <head> marca el <html> y la oculta antes de que pinte.

3. Tiene tres redes de seguridad, porque una pantalla de carga que no se va
   deja el sitio inservible:
     - js/app.js la retira a los 2,2 s como maximo. Camino normal.
     - Un setTimeout EN LINEA la retira a los 4 s si app.js nunca llego
       (404, red caida, bloqueador). Va en linea justamente porque no puede
       depender del archivo que podria estar fallando.
     - <noscript> la oculta si no hay JavaScript del todo.
   Queda ademas una animacion CSS a los 5 s como cuarto respaldo, pero no se
   confia en ella: no se pudo verificar (el reloj virtual de Chrome headless
   no avanza animaciones CSS, asi que la prueba no concluye).

4. El progreso es real: mira el estado del DOM y las imagenes que no son
   lazy. No es una barra decorativa que cuenta sola.

    python tools/patch-carga.py

Idempotente. Toca las .html y la plantilla de tools/generar-servicios.py.
"""

import io
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ESTILO = """<!-- Pantalla de carga: en línea a propósito, para que pinte antes que nada -->
<style>
#carga{position:fixed;inset:0;z-index:9999;display:grid;place-items:center;
  background:radial-gradient(75% 60% at 50% 45%,#0a1327 0%,#04060c 72%);
  transition:opacity .5s ease,visibility .5s ease;
  animation:cargaSeguro 0s linear 5s forwards}
#carga.se-va{opacity:0;visibility:hidden;pointer-events:none}
#carga[hidden]{display:none}
html.sin-carga #carga{display:none}
/* Red de seguridad: si el JS no llega, la pantalla se va igual */
@keyframes cargaSeguro{to{opacity:0;visibility:hidden;pointer-events:none}}

.carga__in{display:grid;justify-items:center;gap:28px;width:min(82vw,360px)}
.carga__marca{position:relative;display:grid;place-items:center;height:52px;width:100%}
.carga__marca img{height:42px;width:auto;opacity:0;
  animation:cargaMarca .8s cubic-bezier(.22,.61,.36,1) .08s forwards;
  filter:drop-shadow(0 0 20px rgba(10,92,255,.5))}
@keyframes cargaMarca{from{opacity:0;transform:scale(.94)}to{opacity:1;transform:none}}

/* Los rayos del logotipo, convergiendo sobre el wordmark */
.carga__rayo{position:absolute;width:2px;height:54px;border-radius:2px;
  background:linear-gradient(180deg,transparent,#00c8ff 35%,#0a5cff 72%,transparent);
  box-shadow:0 0 9px rgba(10,92,255,.9),0 0 26px rgba(10,92,255,.45);
  animation:cargaRayo 1.8s cubic-bezier(.4,0,.2,1) infinite}
.carga__rayo--a{left:4%;top:-14px;transform:rotate(-26deg)}
.carga__rayo--b{left:0;top:22px;transform:rotate(26deg);animation-delay:.12s}
.carga__rayo--c{right:4%;top:-14px;transform:rotate(26deg);animation-delay:.24s}
.carga__rayo--d{right:0;top:22px;transform:rotate(-26deg);animation-delay:.36s}
@keyframes cargaRayo{0%,100%{opacity:.14}50%{opacity:1}}

.carga__barra{width:100%;height:2px;border-radius:2px;
  background:rgba(122,163,255,.14);overflow:hidden}
.carga__barra i{display:block;height:100%;width:0;border-radius:2px;
  background:linear-gradient(90deg,#0a5cff,#00c8ff);
  box-shadow:0 0 10px rgba(0,200,255,.8)}
.carga__pct{margin:0;font:600 11px/1 'Saira',system-ui,-apple-system,sans-serif;
  letter-spacing:.26em;text-transform:uppercase;color:#6c7a93}

@media (prefers-reduced-motion:reduce){
  #carga{transition:none}
  .carga__rayo{animation:none;opacity:.65}
  .carga__marca img{animation:none;opacity:1}
}
</style>
<script>/* Ya la vio en esta sesión: no repetirla en cada página */
try{if(sessionStorage.getItem('dacars-visto'))document.documentElement.className+=' sin-carga'}catch(e){}</script>
"""

MARCA = """<div id="carga" role="status" aria-live="polite" aria-label="Cargando DACARS">
  <div class="carga__in">
    <div class="carga__marca">
      <i class="carga__rayo carga__rayo--a"></i><i class="carga__rayo carga__rayo--b"></i>
      <i class="carga__rayo carga__rayo--c"></i><i class="carga__rayo carga__rayo--d"></i>
      <img src="statics/logo-wordmark.png" alt="" width="600" height="117" fetchpriority="high">
    </div>
    <div class="carga__barra"><i id="cargaBarra"></i></div>
    <p class="carga__pct"><span id="cargaPct">0</span>%</p>
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


def parchar(ruta, etiqueta):
    txt = io.open(ruta, encoding="utf-8").read()
    if "id=\"carga\"" in txt:
        return False

    if ANCLA_HEAD not in txt or ANCLA_BODY not in txt:
        print("  !! %s: no encontré dónde insertar" % etiqueta)
        return False

    txt = txt.replace(ANCLA_HEAD, ESTILO + "\n" + ANCLA_HEAD, 1)
    txt = txt.replace(ANCLA_BODY, ANCLA_BODY + MARCA, 1)
    io.open(ruta, "w", encoding="utf-8", newline="\n").write(txt)
    print("  %s" % etiqueta)
    return True


def main():
    n = 0
    for f in sorted(os.listdir(ROOT)):
        if f.endswith(".html"):
            n += parchar(os.path.join(ROOT, f), f)

    # la plantilla, para que lo regenerado siga teniéndola
    gen = os.path.join(ROOT, "tools", "generar-servicios.py")
    if os.path.exists(gen):
        n += parchar(gen, "tools/generar-servicios.py")

    print("\n%d archivos con pantalla de carga" % n if n else "\n(ya estaban todos)")


if __name__ == "__main__":
    main()
