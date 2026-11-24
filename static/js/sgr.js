/* SGR v3.0 — interacciones de la interfaz (sin dependencias externas).
 *  1. Autocompletar vecino: al escribir un RUT o nombre se buscan vecinos
 *     registrados y se completan el nombre y el teléfono del formulario.
 *  2. Búsqueda dinámica: las listas con [data-busqueda-dinamica] se filtran
 *     mientras se escribe (código, RUT o nombre del solicitante).
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
})();
