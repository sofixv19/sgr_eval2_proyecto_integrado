/* SGR v3.0 — gráficos del dashboard (Chart.js 4, servido localmente).
 * Paleta validada (CVD y contraste): serie 1 #A8323D, serie 2 #2F78B4.
 * El semáforo usa los colores de estado y siempre va con texto en la tabla. */
(function () {
  'use strict';
  var el = document.getElementById('datos-graficos');
  if (!el || typeof Chart === 'undefined') { return; }
  var d = JSON.parse(el.textContent);
  var S1 = '#A8323D', S2 = '#2F78B4', TEXTO = '#4A4044', GRILLA = 'rgba(74,64,68,0.10)';
  Chart.defaults.font.family = "'Public Sans', Arial, sans-serif";
  Chart.defaults.color = TEXTO;
  Chart.defaults.plugins.legend.labels.boxWidth = 12;
  Chart.defaults.maintainAspectRatio = false;

  function ejes(horizontal, max, sufijo) {
    var valor = { beginAtZero: true, grid: { color: GRILLA }, border: { display: false },
                  ticks: { precision: 0, callback: function (v) { return v + (sufijo || ''); } } };
    if (max) { valor.suggestedMax = max; }
    var cat = { grid: { display: false }, border: { display: false } };
    return horizontal ? { x: valor, y: cat } : { x: cat, y: valor };
  }
  function barra(id, etiquetas, datasets, opciones) {
    var c = document.getElementById(id);
    if (!c) { return; }
    opciones = opciones || {};
    new Chart(c, {
      type: 'bar',
      data: { labels: etiquetas, datasets: datasets.map(function (ds) {
        return Object.assign({ borderRadius: 4, borderSkipped: 'start', maxBarThickness: 26,
                               borderColor: '#fff', borderWidth: 1 }, ds);
      }) },
      options: {
        indexAxis: opciones.horizontal ? 'y' : 'x',
        scales: Object.assign(ejes(opciones.horizontal, opciones.max, opciones.sufijo),
                              opciones.apilado ? { } : {}),
        plugins: { legend: { display: datasets.length > 1, position: 'top', align: 'start' },
                   tooltip: { callbacks: { label: function (ctx) {
                     var v = opciones.horizontal ? ctx.parsed.x : ctx.parsed.y;
                     return (ctx.dataset.label ? ctx.dataset.label + ': ' : '') + v + (opciones.sufijo || '');
                   } } } }
      }
    });
    if (opciones.apilado) {
      var ch = Chart.getChart(c);
      ch.options.scales.x.stacked = true; ch.options.scales.y.stacked = true; ch.update();
    }
  }

  var f = d.por_funcionario;
  barra('g-funcionarios', f.etiquetas, [{ label: 'Cumplimiento', data: f.valores, backgroundColor: f.colores }],
        { horizontal: true, max: 120, sufijo: ' %' });
  var dg = d.por_delegacion;
  barra('g-delegaciones', dg.etiquetas, [{ label: 'Cumplimiento', data: dg.valores, backgroundColor: dg.colores }],
        { horizontal: true, max: 120, sufijo: ' %' });
  var cg = d.carga;
  barra('g-carga', cg.etiquetas, [
    { label: 'Actividades', data: cg.actividades, backgroundColor: S1 },
    { label: 'Gestiones sociales', data: cg.sociales, backgroundColor: S2 }
  ], { horizontal: true, apilado: true });
  barra('g-compromisos', d.compromisos.etiquetas, [{ label: 'Compromisos', data: d.compromisos.valores, backgroundColor: S2 }]);
  barra('g-validacion', d.validacion.etiquetas, [{ label: 'Registros', data: d.validacion.valores, backgroundColor: S1 }],
        { horizontal: true });

  var t = d.tendencia, ct = document.getElementById('g-tendencia');
  if (ct) {
    new Chart(ct, {
      type: 'line',
      data: { labels: t.etiquetas, datasets: [
        { label: 'Ingresados', data: t.ingresados, borderColor: S1, backgroundColor: S1, borderWidth: 2,
          pointRadius: 4, pointHoverRadius: 6, tension: 0 },
        { label: 'Aprobados', data: t.aprobados, borderColor: S2, backgroundColor: S2, borderWidth: 2,
          pointRadius: 4, pointHoverRadius: 6, pointStyle: 'rectRot', tension: 0 }
      ] },
      options: { interaction: { mode: 'index', intersect: false }, scales: ejes(false),
                 plugins: { legend: { position: 'top', align: 'start' } } }
    });
  }
})();
