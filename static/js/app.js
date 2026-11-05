/* =========================================================
   DACARS — interacciones del sitio
   ========================================================= */
(function () {
  'use strict';

  var WHATSAPP = '573112629406';
  var sinMovimiento = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Pantalla de carga ---------- */
  (function () {
    var carga = document.getElementById('carga');
    if (!carga) return;

    var inicio = Date.now();
    var MINIMO = 850;   // deja que la animación alcance a entrar y barrer una vez
    var TOPE = 2200;    // nunca retiene el sitio más que esto, pase lo que pase

    function salir() {
      carga.classList.add('se-va');
      setTimeout(function () { carga.hidden = true; }, 600);
    }

    function revisar() {
      var t = Date.now() - inicio;
      if (t >= TOPE) { salir(); return; }

      if (document.readyState !== 'loading') {
        // Solo cuentan las imágenes que bloquean la primera vista. Las lazy no.
        var imgs = document.images, faltan = 0;
        for (var i = 0; i < imgs.length; i++) {
          if (imgs[i].loading !== 'lazy' && !imgs[i].complete) faltan++;
        }
        if (!faltan && t >= MINIMO) { salir(); return; }
      }
      setTimeout(revisar, 60);
    }

    revisar();
  })();

  /* ---------- Año del footer ---------- */
  var year = document.getElementById('year');
  if (year) year.textContent = new Date().getFullYear();

  /* ---------- Header: sombra al hacer scroll + barra de progreso ---------- */
  var head = document.getElementById('head');
  var progress = document.getElementById('progress');
  var pendiente = false;

  function onScroll() {
    if (head) head.classList.toggle('is-stuck', window.scrollY > 12);
    if (progress) {
      var doc = document.documentElement;
      var max = doc.scrollHeight - doc.clientHeight;
      var p = max > 0 ? Math.min(window.scrollY / max, 1) : 0;
      progress.style.transform = 'scaleX(' + p.toFixed(4) + ')';
    }
    pendiente = false;
  }
  onScroll();
  window.addEventListener('scroll', function () {
    if (!pendiente) { pendiente = true; requestAnimationFrame(onScroll); }
  }, { passive: true });

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

  /* ---------- Contadores: las cifras del hero suben al entrar ---------- */
  function contar(el) {
    var fin = parseInt(el.getAttribute('data-count'), 10);
    if (isNaN(fin)) return;
    if (sinMovimiento || !window.requestAnimationFrame) { el.textContent = fin; return; }
    var inicio = null, dur = 1400;
    function paso(t) {
      if (!inicio) inicio = t;
      var k = Math.min((t - inicio) / dur, 1);
      var e = 1 - Math.pow(1 - k, 3);
      el.textContent = Math.round(fin * e);
      if (k < 1) requestAnimationFrame(paso);
    }
    requestAnimationFrame(paso);
  }

  var contadores = document.querySelectorAll('[data-count]');
  if (contadores.length) {
    if ('IntersectionObserver' in window) {
      var ioc = new IntersectionObserver(function (entries) {
        entries.forEach(function (en) {
          if (!en.isIntersecting) return;
          contar(en.target);
          ioc.unobserve(en.target);
        });
      }, { threshold: 0.4 });
      contadores.forEach(function (el) { ioc.observe(el); });
    } else {
      contadores.forEach(contar);
    }
  }

  /* ---------- Carrusel de categorías (flechas) ---------- */
  document.querySelectorAll('.scroller').forEach(function (sc) {
    var pista = sc.querySelector('.rubros--scroll');
    var prev = sc.querySelector('[data-scroll="-1"]');
    var next = sc.querySelector('[data-scroll="1"]');
    if (!pista || !prev || !next) return;

    function estado() {
      prev.disabled = pista.scrollLeft <= 4;
      next.disabled = pista.scrollLeft + pista.clientWidth >= pista.scrollWidth - 4;
    }
    function mover(dir) {
      pista.scrollBy({ left: dir * pista.clientWidth * 0.8, behavior: sinMovimiento ? 'auto' : 'smooth' });
    }
    prev.addEventListener('click', function () { mover(-1); });
    next.addEventListener('click', function () { mover(1); });
    pista.addEventListener('scroll', estado, { passive: true });
    window.addEventListener('resize', estado);
    estado();
  });

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

  /* ---------- Video del hero ---------- */
  var hero = document.getElementById('heroVideo');

  if (hero) {
    var conexion = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
    var ahorroDatos = !!(conexion && (conexion.saveData ||
                       /^(slow-2g|2g)$/.test(conexion.effectiveType || '')));
    // La ventana del hero es 3:4 hasta 600 px y 4:3 de ahí en adelante
    // (ver .hero__frame en style.css): el video sigue la misma frontera.
    var vertical = window.matchMedia('(max-width: 600px)').matches;

    // Las URLs viven en la plantilla, junto a las del video.
    var poster = vertical ? hero.dataset.posterAlto : hero.dataset.posterAncho;
    if (poster) { hero.poster = poster; }

    // Enciende el fondo pase lo que pase: si el video no llega, el poster
    // tiene que quedar visible igual.
    var encender = function () { hero.classList.add('is-on'); };

    if (sinMovimiento || ahorroDatos) {
      encender();
    } else {
      hero.src = vertical ? hero.dataset.srcAlto : hero.dataset.srcAncho;
      hero.load();

      hero.addEventListener('loadeddata', encender);
      hero.addEventListener('error', encender);
      setTimeout(encender, 2500);

      var reproducir = function () {
        var intento = hero.play();
        return (intento && intento.catch) ? intento : null;
      };

      var silencioso = function () { var p = reproducir(); if (p) p.catch(function () {}); };

      hero.addEventListener('canplay', silencioso);

      var arranque = reproducir();
      if (arranque) {
        arranque.catch(function () {
          encender();
          var reintento = function () {
            silencioso();
            ['pointerdown', 'touchstart', 'keydown', 'scroll'].forEach(function (ev) {
              window.removeEventListener(ev, reintento);
            });
          };
          ['pointerdown', 'touchstart', 'keydown', 'scroll'].forEach(function (ev) {
            window.addEventListener(ev, reintento, { once: true, passive: true });
          });
        });
      }

      // No gastar batería ni CPU con el hero fuera de pantalla
      if ('IntersectionObserver' in window) {
        new IntersectionObserver(function (entries) {
          entries.forEach(function (e) {
            if (e.isIntersecting) { silencioso(); }
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
        video.muted = true;
        video.play().catch(function () {});
      });
    });

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
