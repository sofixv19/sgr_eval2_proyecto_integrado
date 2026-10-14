"""
Ejecuta todas las pruebas unitarias del proyecto y genera la matriz de
ejecución del Plan de Pruebas en 'resultados_pruebas.csv'.

Cada prueba indica su caso en la primera línea del docstring
(por ejemplo "CP-LOGIN-001: ..."), así el resultado queda ligado al ID del
plan.

Uso:
    python plan_pruebas.py
"""
import csv
import os
import sys
import time
import unittest
from datetime import datetime

import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sgr_evaluacion.settings')
django.setup()

from django.test.runner import DiscoverRunner  # noqa: E402

RESULTADOS = []


class ResultadoPlan(unittest.TextTestResult):
    def startTest(self, test):
        self._inicio = time.perf_counter()
        super().startTest(test)

    def _registrar(self, test, estado, detalle=''):
        doc = (test._testMethodDoc or '').strip().split('\n')[0]
        caso, _, descripcion = doc.partition(':')
        RESULTADOS.append({
            'id': caso.strip() if caso.startswith('CP-') else '',
            'descripcion': descripcion.strip() or doc,
            'prueba': f'{test.__class__.__module__}.{test.__class__.__name__}.{test._testMethodName}',
            'estado': estado,
            'segundos': f'{time.perf_counter() - self._inicio:.3f}',
            'detalle': detalle,
        })

    def addSuccess(self, test):
        super().addSuccess(test)
        self._registrar(test, 'Aprobado')

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._registrar(test, 'Reprobado', str(err[1])[:300])

    def addError(self, test, err):
        super().addError(test, err)
        self._registrar(test, 'Reprobado', f'Error: {err[1]}'[:300])

    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        self._registrar(test, 'No ejecutado', reason)


class RunnerPlan(DiscoverRunner):
    def get_resultclass(self):
        return ResultadoPlan


if __name__ == '__main__':
    runner = RunnerPlan(verbosity=1)
    fallas = runner.run_tests(['comun', 'cuentas', 'delegaciones', 'organizacion', 'gestion'])
    RESULTADOS.sort(key=lambda r: r['id'])
    with open('resultados_pruebas.csv', 'w', newline='', encoding='utf-8') as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(RESULTADOS[0].keys()))
        escritor.writeheader()
        escritor.writerows(RESULTADOS)
    aprobados = sum(r['estado'] == 'Aprobado' for r in RESULTADOS)
    print(f'\n{datetime.now():%d/%m/%Y %H:%M} · {len(RESULTADOS)} casos · {aprobados} aprobados · '
          f'{len(RESULTADOS) - aprobados} reprobados/no ejecutados')
    for r in RESULTADOS:
        print(f"  {r['id']:<13} {r['estado']:<10} {r['descripcion'][:90]}")
    print('Matriz guardada en resultados_pruebas.csv')
    sys.exit(bool(fallas))
