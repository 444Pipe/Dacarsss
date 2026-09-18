/* =========================================================
   DACARS — interacciones del sitio
   ========================================================= */
(function () {
  'use strict';

  var WHATSAPP = '573112629406';

  /* ---------- Pantalla de carga ---------- */
  (function () {
    var carga = document.getElementById('carga');
    if (!carga || document.documentElement.className.indexOf('sin-carga') > -1) return;

    var barra = document.getElementById('cargaBarra');
    var texto = document.getElementById('cargaPct');
    var inicio = Date.now();
    var MINIMO = 500;   // para que no parpadee en conexiones rápidas
    var TOPE = 2200;    // nunca retiene el sitio más que esto, pase lo que pase
    var valor = 0, meta = 0, domListo = false;

    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', function () { domListo = true; });
    } else {
      domListo = true;
    }

    // Solo cuentan las imágenes que bloquean la primera vista. Las lazy no:
    // no cargan hasta que el visitante baje, y esperarlas sería esperar para siempre.
    var criticas = Array.prototype.filter.call(document.images, function (img) {
      return img.loading !== 'lazy';
    });

    function medir() {
      var listas = 0;
      for (var i = 0; i < criticas.length; i++) if (criticas[i].complete) listas++;
      var prop = criticas.length ? listas / criticas.length : 1;
      meta = Math.round((domListo ? 45 : 12) + prop * 55);
    }

    function pintar() {
      medir();
      valor += (meta - valor) * 0.16;
      if (meta - valor < 0.6) valor = meta;
      if (barra) barra.style.width = valor.toFixed(1) + '%';
      if (texto) texto.textContent = Math.round(valor);

      var t = Date.now() - inicio;
      if ((valor >= 99.4 && t >= MINIMO) || t >= TOPE) { salir(); return; }
      requestAnimationFrame(pintar);
    }

    function salir() {
      if (barra) barra.style.width = '100%';
      if (texto) texto.textContent = '100';
      try { sessionStorage.setItem('dacars-visto', '1'); } catch (e) {}
      requestAnimationFrame(function () {
        carga.classList.add('se-va');
        setTimeout(function () { carga.hidden = true; }, 550);
      });
    }

    requestAnimationFrame(pintar);
  })();

  /* ---------- Año del footer ---------- */
  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  /* ---------- Header: sombra al hacer scroll ---------- */
  var head = document.getElementById('head');
  function onScroll() {
    if (head) head.classList.toggle('is-stuck', window.scrollY > 12);
  }
  onScroll();
  window.addEventListener('scroll', onScroll, { passive: true });

  /* ---------- Menú móvil ---------- */
  var burger = document.getElementById('burger');
  var nav = document.getElementById('nav');

  function closeNav() {
    if (!nav || !burger) return;
    nav.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
    burger.setAttribute('aria-label', 'Abrir menú');
  }

  if (burger && nav) {
    burger.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      burger.setAttribute('aria-expanded', String(open));
      burger.setAttribute('aria-label', open ? 'Cerrar menú' : 'Abrir menú');
    });

    nav.addEventListener('click', function (e) {
      if (e.target.closest('a')) closeNav();
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') closeNav();
    });

    window.addEventListener('resize', function () {
      if (window.innerWidth > 940) closeNav();
    });
  }

  /* ---------- Reveal al entrar en pantalla ---------- */
  var revealables = document.querySelectorAll('[data-reveal]');

  if (!('IntersectionObserver' in window)) {
    revealables.forEach(function (el) { el.classList.add('is-in'); });
  } else {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry, i) {
        if (!entry.isIntersecting) return;
        var el = entry.target;
        // Escalona los elementos que aparecen juntos
        el.style.transitionDelay = Math.min(i * 70, 280) + 'ms';
        el.classList.add('is-in');
        io.unobserve(el);
      });
    }, { threshold: 0.12, rootMargin: '0px 0px -8% 0px' });

    revealables.forEach(function (el) { io.observe(el); });
  }

  /* ---------- Enlace activo en la navegación ---------- */
  var sections = Array.prototype.slice.call(
    document.querySelectorAll('main section[id]')
  );
  var navLinks = Array.prototype.slice.call(
    document.querySelectorAll('.nav > a[href^="#"]')
  );

  if (sections.length && navLinks.length && 'IntersectionObserver' in window) {
    var spy = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (!entry.isIntersecting) return;
        var id = entry.target.id;
        navLinks.forEach(function (a) {
          a.classList.toggle('is-active', a.getAttribute('href') === '#' + id);
        });
      });
    }, { rootMargin: '-45% 0px -50% 0px' });

    sections.forEach(function (s) { spy.observe(s); });
  }

  /* ---------- Galería: si no hay foto aún, deja el panel de marca ---------- */
  document.querySelectorAll('.gal__i img').forEach(function (img) {
    function fail() { img.closest('.gal__i').classList.add('no-img'); }
    img.addEventListener('error', fail);
    // Imágenes ya fallidas antes de registrar el listener
    if (img.complete && img.naturalWidth === 0) fail();
  });

  /* ---------- Formulario → WhatsApp ---------- */
  var form = document.getElementById('form');
  var note = document.getElementById('form-note');

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      var nombre = form.nombre.value.trim();
      var vehiculo = form.vehiculo.value.trim();
      var servicio = form.servicio.value;
      var mensaje = form.mensaje.value.trim();

      var faltantes = [
        { el: form.nombre, ok: nombre.length > 1 },
        { el: form.vehiculo, ok: vehiculo.length > 1 },
        { el: form.servicio, ok: servicio !== '' }
      ];

      var primerError = null;
      faltantes.forEach(function (f) {
        f.el.closest('.field').classList.toggle('is-bad', !f.ok);
        if (!f.ok && !primerError) primerError = f.el;
      });

      if (primerError) {
        if (note) {
          note.textContent = 'Completa tu nombre, el vehículo y el servicio para continuar.';
          note.classList.add('is-bad');
        }
        primerError.focus();
        return;
      }

      if (note) {
        note.textContent = 'Abriendo WhatsApp…';
        note.classList.remove('is-bad');
      }

      var lineas = [
        '¡Hola DACARS! Quiero cotizar un servicio.',
        '',
        'Nombre: ' + nombre,
        'Vehículo: ' + vehiculo,
        'Servicio: ' + servicio
      ];
      if (mensaje) lineas.push('Detalle: ' + mensaje);

      var url = 'https://wa.me/' + WHATSAPP + '?text=' +
                encodeURIComponent(lineas.join('\n'));

      window.open(url, '_blank', 'noopener');
    });

    // Limpia el estado de error al corregir
    form.addEventListener('input', function (e) {
      var field = e.target.closest('.field');
      if (field) field.classList.remove('is-bad');
    });
  }

  /* ---------- Fondo de video del hero ---------- */
  var hero = document.getElementById('heroVideo');

  if (hero) {
    var sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    var conexion = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    var ahorroDatos = !!(conexion && (conexion.saveData ||
                       /^(slow-2g|2g)$/.test(conexion.effectiveType || '')));
    var vertical = window.matchMedia('(max-width: 860px)').matches;

    hero.poster = vertical
      ? 'statics/video/hero-poster-3x4.jpg'
      : 'statics/video/hero-poster-16x9.jpg';

    if (sinMovimiento || ahorroDatos) {
      // Queda el poster: ni se descarga el video.
      hero.classList.add('is-on');
    } else {
      hero.src = vertical ? hero.dataset.srcAlto : hero.dataset.srcAncho;
      hero.load();

      hero.addEventListener('loadeddata', function () {
        hero.classList.add('is-on');
      });

      var arranque = hero.play();
      if (arranque && arranque.catch) {
        arranque.catch(function () {
          // Autoplay bloqueado por el navegador: se queda el poster, sin romper nada.
          hero.classList.add('is-on');
        });
      }

      // No gastar batería ni CPU con el hero fuera de pantalla
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) { hero.play().catch(function () {}); }
            else { hero.pause(); }
          });
        }, { threshold: 0.05 }).observe(hero);
      }
    }
  }

  /* ---------- Reels: reproducir con sonido al hacer clic ---------- */
  var clips = Array.prototype.slice.call(document.querySelectorAll('.clip'));

  function pausarClips(menos) {
    clips.forEach(function (c) {
      if (c === menos) return;
      var v = c.querySelector('video');
      if (v && !v.paused) { v.pause(); }
      c.classList.remove('is-playing');
      if (v) { v.controls = false; }
    });
  }

  clips.forEach(function (clip) {
    var video = clip.querySelector('video');
    var boton = clip.querySelector('.clip__btn');
    if (!video || !boton) return;

    boton.addEventListener('click', function () {
      pausarClips(clip);
      clip.classList.add('is-playing');
      video.controls = true;
      video.muted = false;
      video.play().catch(function () {
        // Si el navegador no deja reproducir con sonido, al menos que se vea.
        video.muted = true;
        video.play().catch(function () {});
      });
    });

    // Clic sobre el video: pausa / reanuda
    video.addEventListener('click', function () {
      if (video.paused) { video.play().catch(function () {}); }
      else { video.pause(); }
    });

    video.addEventListener('pause', function () {
      if (video.currentTime === 0 || video.ended) {
        clip.classList.remove('is-playing');
        video.controls = false;
      }
    });

    video.addEventListener('ended', function () {
      clip.classList.remove('is-playing');
      video.controls = false;
      video.currentTime = 0;
    });
  });

  // Pausa el reel que se sale de la pantalla
  if (clips.length && 'IntersectionObserver' in window) {
    var obsClips = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) return;
        var v = e.target.querySelector('video');
        if (v && !v.paused) {
          v.pause();
          e.target.classList.remove('is-playing');
          v.controls = false;
        }
      });
    }, { threshold: 0.25 });
    clips.forEach(function (c) { obsClips.observe(c); });
  }

})();
