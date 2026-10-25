"""Validador lógico de la base de conocimiento (no valida exactitud clínica).

Uso: python validar_kb.py
Requiere base_conocimiento.json en la misma carpeta.
Genera reporte_validacion_kb.json.
"""
import json
import re
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
RUTA = BASE / 'base_conocimiento.json'
REPORTE = BASE / 'reporte_validacion_kb.json'
NOMBRE_VALIDO = re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')

CASOS = [
    ('Gripe', 'Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular Inicio_Subito Tos_Seca', 'Dx_Gripe', True),
    ('COVID-19', 'Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular Inicio_Subito Perdida_Olfato_Gusto', 'Dx_COVID19', True),
    ('Neumonia con alerta', 'Fiebre Dificultad_Respiratoria Taquipnea Crepitantes_Pulmonares Tos_Productiva Dolor_Toracico Saturacion_Oxigeno_Baja', 'Alerta_Gravedad_Extrema', True),
    ('Tuberculosis con alerta', 'Perdida_Peso Sudoracion_Nocturna Fatiga Perdida_Apetito Tos_Prolongada Hemoptisis', 'Alerta_Riesgo_Alto', True),
    ('No demostrable', 'Fiebre Escalofrios Tos_Seca', 'Dx_COVID19', False),
]


def inferir(reglas, hechos):
    """Aplica las reglas Horn positivas hasta punto fijo y registra hechos nuevos."""
    memoria = set(hechos)
    traza = []
    activadas = set()
    while True:
        cambio = False
        for regla in reglas:
            if set(regla['antecedentes']).issubset(memoria):
                activadas.add(regla['id'])
                if regla['consecuente'] not in memoria:
                    memoria.add(regla['consecuente'])
                    traza.append({'regla': regla['id'], 'hecho': regla['consecuente']})
                    cambio = True
        if not cambio:
            return memoria, traza, activadas


def casos_limite(reglas, entradas):
    """Pruebas de propiedades básicas, independientes de un diagnóstico particular."""
    pruebas = []
    objetivo = 'Objetivo_Sin_Regla_Para_Probar'
    if any(r['consecuente'] == objetivo for r in reglas):
        objetivo = 'Objetivo_Imposible_999999'
    hechos, _, _ = inferir(reglas, ['Hecho_De_Prueba'])
    pruebas.append({'nombre': 'Objetivo ya es hecho inicial',
                    'aprobado': 'Hecho_De_Prueba' in hechos})
    pruebas.append({'nombre': 'Objetivo sin regla ni hecho inicial',
                    'aprobado': objetivo not in hechos})
    # Propiedad Horn: si falta un antecedente, ESA regla no puede dispararse.
    # Se comprueba usando la regla aislada, porque otra regla podría derivar el mismo consecuente.
    r = next((r for r in reglas if len(r['antecedentes']) >= 2), None)
    if r:
        hechos_parciales = r['antecedentes'][:-1]
        memoria, _, activadas = inferir([r], hechos_parciales)
        pruebas.append({'nombre': 'Regla con antecedente faltante',
                        'aprobado': r['id'] not in activadas and r['consecuente'] not in memoria})
    # Monotonía: añadir hechos no debe hacer desaparecer conclusiones.
    muestra = set(sorted(entradas)[:5])
    m1, _, _ = inferir(reglas, muestra)
    m2, _, _ = inferir(reglas, muestra | set(entradas))
    pruebas.append({'nombre': 'Monotonia al agregar hechos', 'aprobado': m1.issubset(m2)})
    return pruebas


def validar():
    errores = []
    if not RUTA.is_file():
        raise FileNotFoundError(f'Falta {RUTA.name}; coloca el script junto al JSON')
    datos = json.loads(RUTA.read_text(encoding='utf-8-sig'))
    reglas = datos.get('reglas') if isinstance(datos, dict) else None
    if not isinstance(reglas, list):
        raise ValueError('Se requiere un objeto JSON con una lista en "reglas"')
    if len(reglas) < 50:
        errores.append(f'Se requieren 50 reglas como mínimo; hay {len(reglas)}')

    ids, firmas = set(), set()
    grafo = defaultdict(set)
    consecuentes, antecedentes = set(), set()
    reglas_validas = []
    for numero, r in enumerate(reglas, 1):
        if not isinstance(r, dict) or set(r) != {'id', 'antecedentes', 'consecuente'}:
            errores.append(f'Regla {numero}: claves inválidas')
            continue
        ident, ant, cons = r['id'], r['antecedentes'], r['consecuente']
        if not isinstance(ident, str) or not NOMBRE_VALIDO.fullmatch(ident):
            errores.append(f'Regla {numero}: ID inválido')
            continue
        if ident in ids:
            errores.append(f'ID repetido: {ident}')
        ids.add(ident)
        if not isinstance(ant, list) or not ant or not all(isinstance(a, str) and NOMBRE_VALIDO.fullmatch(a) for a in ant):
            errores.append(f'{ident}: antecedentes inválidos')
            continue
        if not isinstance(cons, str) or not NOMBRE_VALIDO.fullmatch(cons):
            errores.append(f'{ident}: consecuente inválido')
            continue
        if len(ant) != len(set(ant)):
            errores.append(f'{ident}: antecedente repetido')
        firma = (tuple(sorted(ant)), cons)
        if firma in firmas:
            errores.append(f'{ident}: regla idéntica duplicada')
        firmas.add(firma)
        for a in ant:
            grafo[a].add(cons)
        consecuentes.add(cons)
        antecedentes.update(ant)
        reglas_validas.append(r)

    estructuralmente_validas = len(reglas_validas) == len(reglas) and not any(
        any(t in e for t in ['inválid', 'repetid', 'duplicad']) for e in errores
    )
    nodos = antecedentes | consecuentes
    color = {}
    ciclos = []

    def dfs(nodo, pila):
        if color.get(nodo) == 1:
            ciclos.append(' -> '.join(pila[pila.index(nodo):] + [nodo]))
            return
        if color.get(nodo) == 2:
            return
        color[nodo] = 1
        for siguiente in sorted(grafo[nodo]):
            dfs(siguiente, pila + [siguiente])
        color[nodo] = 2

    if estructuralmente_validas:
        for nodo in sorted(nodos):
            if not color.get(nodo):
                dfs(nodo, [nodo])
    if ciclos:
        errores.extend('Ciclo: ' + c for c in ciclos)

    entradas = antecedentes - consecuentes
    activadas_global = set()
    profundidad_min = {}
    profundidad_max = {}
    if estructuralmente_validas and not ciclos:
        _, _, activadas_global = inferir(reglas_validas, entradas)
        no_activables = sorted(ids - activadas_global)
        if no_activables:
            errores.append('Reglas sin alcance: ' + ', '.join(no_activables))
        # La profundidad de una prueba de una regla con AND viene determinada
        # por la rama más larga entre SUS antecedentes (se necesitan todos).
        # Al haber múltiples reglas para un mismo consecuente, se elige min/max
        # entre las pruebas alternativas. Base: hechos de entrada = 0 pasos.
        profundidad_min = {h: 0 for h in entradas}
        profundidad_max = {h: 0 for h in entradas}
        for _ in range(len(nodos) + 1):
            cambio = False
            for r in reglas_validas:
                ant = r['antecedentes']
                c = r['consecuente']
                if all(a in profundidad_min for a in ant):
                    d = 1 + max(profundidad_min[a] for a in ant)
                    if d < profundidad_min.get(c, float('inf')):
                        profundidad_min[c] = d
                        cambio = True
                if all(a in profundidad_max for a in ant):
                    d = 1 + max(profundidad_max[a] for a in ant)
                    if d > profundidad_max.get(c, -1):
                        profundidad_max[c] = d
                        cambio = True
            if not cambio:
                break

    diagnosticos = sorted(c for c in consecuentes if c.startswith('Dx_'))
    if estructuralmente_validas and not ciclos:
        cortos = [d for d in diagnosticos if profundidad_min.get(d, -1) < 4]
        inalcanzables = [d for d in diagnosticos if d not in profundidad_min]
        if cortos:
            errores.append('Diagnósticos con prueba de menos de 4 pasos: ' + ', '.join(cortos))
        if inalcanzables:
            errores.append('Diagnósticos inalcanzables: ' + ', '.join(inalcanzables))

    resultados = []
    cobertura = set()
    limites = []
    if estructuralmente_validas:
        for nombre, hechos, objetivo, esperado in CASOS:
            memoria, traza, activadas = inferir(reglas_validas, hechos.split())
            obtenido = objetivo in memoria
            cobertura.update(activadas)
            resultados.append({'nombre': nombre, 'hechos': hechos.split(), 'objetivo': objetivo,
                               'esperado': esperado, 'obtenido': obtenido, 'aprobado': obtenido == esperado,
                               'traza': traza, 'reglas_activadas': sorted(activadas)})
            if obtenido != esperado:
                errores.append(f'Caso {nombre}: esperado={esperado}, obtenido={obtenido}')
        limites = casos_limite(reglas_validas, entradas)
        for p in limites:
            if not p['aprobado']:
                errores.append('Caso límite falló: ' + p['nombre'])
    reporte = {
        'archivo': RUTA.name, 'total_reglas': len(reglas), 'hechos_base': len(entradas),
        'reglas_activables': len(activadas_global),
        'profundidad_minima_diagnosticos': {d: profundidad_min.get(d) for d in diagnosticos},
        'profundidad_maxima_diagnosticos': {d: profundidad_max.get(d) for d in diagnosticos},
        'casos_clinicos': resultados, 'casos_limite': limites,
        'cobertura_5_casos': {'activadas': len(cobertura), 'total': len(reglas),
                             'porcentaje': round(100 * len(cobertura) / len(reglas), 2) if reglas else 0,
                             'no_activadas': sorted(ids - cobertura)},
        'errores': errores, 'aprobado': not errores,
        'nota': 'Validación formal de un modelo académico; no confirma diagnósticos ni exactitud clínica. '
                'Se usa un evaluador Forward independiente, no los motores del equipo.'
    }
    REPORTE.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding='utf-8')
    print(f'REGLAS: {len(reglas)} | ACTIVABLES: {len(activadas_global)}/{len(reglas)}')
    print('PROFUNDIDAD MÍNIMA:', reporte['profundidad_minima_diagnosticos'])
    print('PROFUNDIDAD MÁXIMA:', reporte['profundidad_maxima_diagnosticos'])
    for c in resultados:
        print(f"{'OK' if c['aprobado'] else 'ERROR'} | {c['nombre']} | esperado={c['esperado']} | obtenido={c['obtenido']}")
    for p in limites:
        print(f"{'OK' if p['aprobado'] else 'ERROR'} | Límite: {p['nombre']}")
    print(f"COBERTURA: {len(cobertura)}/{len(reglas)} ({reporte['cobertura_5_casos']['porcentaje']}%)")
    print('VALIDACIÓN APROBADA' if not errores else 'VALIDACIÓN CON ERRORES')
    print('Reporte:', REPORTE.name)
    for e in errores:
        print('ERROR:', e)
    return not errores


if __name__ == '__main__':
    raise SystemExit(0 if validar() else 1)
