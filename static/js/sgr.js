/* SGR v3.0 — interacciones de la interfaz (sin dependencias externas).
 *  1. Autocompletar vecino: al escribir un RUT o nombre se buscan vecinos
 *     registrados y se completan el nombre y el teléfono del formulario.
 *  2. Búsqueda dinámica: las listas con [data-busqueda-dinamica] se filtran
 *     mientras se escribe (código, RUT o nombre del solicitante).
 *  3. (v3.0.1) Mensajes del sistema: aparecen arriba a la derecha y se
 *     cierran solos (éxito 4,5 s; aviso 7 s; error 9 s). Si el mouse está
 *     encima, esperan. Los que traen una contraseña (.fijo) quedan hasta
 *     cerrarlos con la X.
 *  4. (v3.0.1) Cambio de página: al hacer clic en un enlace interno o enviar
 *     un formulario, el contenido se desvanece antes de ir a la página nueva.
 */
(function () {
  'use strict';

  function debounce(fn, ms) {
    var t;
    return function () {
      var args = arguments, self = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(self, args); }, ms);
    };
  }

  // ------------------------------------------------ 1. Autocompletar vecino
  document.querySelectorAll('select[data-autocompletar="vecino"]').forEach(function (select) {
    var url = select.closest('form').getAttribute('data-url-vecinos') || '/territorio/vecinos/buscar/';
    var caja = document.createElement('input');
    caja.type = 'search';
    caja.className = 'form-control form-control-sm mb-1';
    caja.placeholder = 'Buscar vecino por RUT o nombre (mín. 3 letras)';
    caja.setAttribute('aria-label', 'Buscar vecino por RUT o nombre');
    caja.autocomplete = 'off';
    var lista = document.createElement('div');
    lista.className = 'list-group autocompletar-lista';
    select.parentNode.insertBefore(caja, select);
    select.parentNode.insertBefore(lista, select);

    function completar(v) {
      select.value = String(v.id);
      var nombre = document.getElementById('id_contacto');
      var fono = document.getElementById('id_telefono_contacto');
      if (nombre) { nombre.value = v.nombre; }
      if (fono) { fono.value = v.telefono; }
      caja.value = v.rut + ' · ' + v.nombre;
      lista.innerHTML = '';
    }

    caja.addEventListener('input', debounce(function () {
      var q = caja.value.trim();
      lista.innerHTML = '';
      if (q.length < 3) { return; }
      fetch(url + '?q=' + encodeURIComponent(q), { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(function (r) { return r.ok ? r.json() : { resultados: [] }; })
        .then(function (datos) {
          lista.innerHTML = '';
          if (!datos.resultados.length) {
            var vacio = document.createElement('div');
            vacio.className = 'list-group-item small text-muted';
            vacio.textContent = 'No hay vecinos con ese RUT o nombre. Regístrelo en Comunidad › Vecinos.';
            lista.appendChild(vacio);
            return;
          }
          datos.resultados.forEach(function (v) {
            var b = document.createElement('button');
            b.type = 'button';
            b.className = 'list-group-item list-group-item-action small';
            b.textContent = v.rut + ' · ' + v.nombre + ' · ' + v.telefono;
            b.addEventListener('click', function () { completar(v); });
            lista.appendChild(b);
          });
          if (datos.resultados.length === 1 && datos.resultados[0].rut.replace(/\./g, '') === q.replace(/\./g, '').toUpperCase()) {
            completar(datos.resultados[0]);
          }
        });
    }, 250));
  });

  // ------------------------------------------------ 2. Búsqueda dinámica
  function normalizar(texto) {
    return (texto || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/\./g, '');
  }

  document.querySelectorAll('[data-busqueda-dinamica]').forEach(function (caja) {
    var objetivo = document.querySelector(caja.getAttribute('data-busqueda-dinamica'));
    var contador = document.querySelector(caja.getAttribute('data-contador') || '#__sin_contador');
    if (!objetivo) { return; }
    var filas = objetivo.querySelectorAll('[data-buscar]');
    var filtrar = function () {
      var q = normalizar(caja.value.trim());
      var visibles = 0;
      filas.forEach(function (fila) {
        var coincide = !q || normalizar(fila.getAttribute('data-buscar')).indexOf(q) !== -1;
        fila.style.display = coincide ? '' : 'none';
        if (coincide) { visibles += 1; }
      });
      if (contador) { contador.textContent = visibles; }
    };
    caja.addEventListener('input', debounce(filtrar, 120));
    filtrar();
  });
  // ------------------------------------------------ 3. Mensajes que se cierran solos
  var DURACION = { success: 4500, info: 4500, warning: 7000, danger: 9000 };
  function cerrarMensaje(alerta) {
    if (alerta.classList.contains('saliendo')) return;
    alerta.classList.add('saliendo');
    var quitar = function () {
      var caja = alerta.parentNode;
      alerta.remove();
      if (caja && !caja.children.length) caja.remove();
    };
    alerta.addEventListener('animationend', quitar, { once: true });
    setTimeout(quitar, 400);  // por si el navegador no anima
  }
  document.querySelectorAll('.mensajes-sistema .alert').forEach(function (alerta, i) {
    var tipo = Object.keys(DURACION).filter(function (k) { return alerta.classList.contains('alert-' + k); })[0] || 'success';
    var restante = DURACION[tipo] + i * 600, inicio = Date.now(), reloj = null;
    alerta.style.setProperty('--duracion', (restante / 1000) + 's');
    var pausas = 0;
    function correr() {
      pausas = Math.max(0, pausas - 1);
      if (pausas || reloj) return;
      inicio = Date.now();
      reloj = setTimeout(function () { cerrarMensaje(alerta); }, Math.max(restante, 800));
    }
    function pausar() {
      pausas += 1;
      if (!reloj) return;
      clearTimeout(reloj); reloj = null;
      restante -= Date.now() - inicio;
    }
    alerta.addEventListener('mouseenter', pausar);
    alerta.addEventListener('mouseleave', correr);
    alerta.addEventListener('focusin', pausar);
    alerta.addEventListener('focusout', correr);
    var boton = alerta.querySelector('.btn-close');
    if (boton) {
      boton.removeAttribute('data-bs-dismiss');
      boton.addEventListener('click', function () { clearTimeout(reloj); cerrarMensaje(alerta); });
    }
    if (alerta.classList.contains('fijo')) return;  // credenciales: se cierra solo con la X
    pausas = 1;
    correr();
  });
  // ------------------------------------------------ 4. Salida suave al cambiar de página
  var contenido = document.querySelector('main.page-content');
  function salir() {
    if (!contenido) return;
    contenido.classList.add('saliendo');
    // si la navegación no ocurre (descarga de Excel, error), se vuelve a mostrar
    setTimeout(function () { contenido.classList.remove('saliendo'); }, 1500);
  }
  window.addEventListener('pageshow', function () { if (contenido) contenido.classList.remove('saliendo'); });
  document.addEventListener('click', function (e) {
    var a = e.target.closest('a[href]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    var href = a.getAttribute('href');
    if (!href || href.charAt(0) === '#' || a.target === '_blank' || a.hasAttribute('download') ||
        a.hasAttribute('data-bs-toggle') || a.origin !== location.origin || /exportar|descargar|\/media\//.test(a.pathname)) return;
    if (a.pathname === location.pathname && a.search === location.search && a.hash) return;
    e.preventDefault();
    salir();
    setTimeout(function () { location.href = a.href; }, 200);
  });
  document.addEventListener('submit', function (e) {
    var f = e.target;
    if (e.defaultPrevented || f.method.toLowerCase() === 'get' && /exportar/.test(f.action)) return;
    if (f.querySelector('input[type=file]')) return;  // la subida de archivos muestra su propio avance
    salir();
  });
  // ------------------------------------------------ 5. Mostrar u ocultar la contraseña (pantalla de acceso)
  document.querySelectorAll('[data-ver-clave]').forEach(function (boton) {
    var campo = document.getElementById(boton.getAttribute('data-ver-clave'));
    if (!campo) return;
    campo.setAttribute('data-visible', '');
    boton.addEventListener('click', function () {
      var ver = campo.type === 'password';
      campo.type = ver ? 'text' : 'password';
      boton.setAttribute('aria-pressed', ver ? 'true' : 'false');
      boton.setAttribute('aria-label', ver ? 'Ocultar contraseña' : 'Mostrar contraseña');
      boton.title = boton.getAttribute('aria-label');
      campo.focus();
    });
  });
})();
