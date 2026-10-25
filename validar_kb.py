"""Valida estructura y comportamiento lógico de la KB académica (no validez clínica).
Ejecutar: python validar_kb_formal.py
Lee base_conocimiento.json en la misma carpeta; exporta reporte_validacion_kb.json.
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
    """Saturación de reglas Horn positivas hasta punto fijo; traza de nuevos hechos."""
    memoria = set(hechos)
    traza = []
    activadas = set()
    while True:
        cambio = False
        for r in reglas:
            if set(r['antecedentes']) <= memoria:
                activadas.add(r['id'])
                if r['consecuente'] not in memoria:
                    memoria.add(r['consecuente'])
                    traza.append({'regla': r['id'], 'hecho': r['consecuente']})
                    cambio = True
        if not cambio:
            return memoria, traza, activadas

def validar():
    errores = []
    if not RUTA.is_file():
        raise FileNotFoundError(f'Falta {RUTA.name}. Pon este script junto a base_conocimiento.json')
    datos = json.loads(RUTA.read_text(encoding='utf-8-sig'))
    reglas = datos.get('reglas') if isinstance(datos, dict) else None
    if not isinstance(reglas, list):
        raise ValueError('El JSON debe contener una lista en la clave "reglas"')
    if len(reglas) < 50:
        errores.append(f'Hay {len(reglas)} reglas: se requieren al menos 50')
    ids, firmas = set(), set()
    grafo = defaultdict(set)
    consecuentes = set()
    antecedentes = set()
    reglas_validas = []
    for n, r in enumerate(reglas, 1):
        if not isinstance(r, dict) or set(r) != {'id', 'antecedentes', 'consecuente'}:
            errores.append(f'Regla {n}: se esperan claves id, antecedentes, consecuente')
            continue
        ident, ant, cons = r['id'], r['antecedentes'], r['consecuente']
        if not isinstance(ident, str) or not NOMBRE_VALIDO.fullmatch(ident):
            errores.append(f'Regla {n}: identificador inválido')
            continue
        if ident in ids:
            errores.append(f'ID duplicado: {ident}')
        ids.add(ident)
        if not isinstance(ant, list) or not ant or not all(isinstance(a, str) and NOMBRE_VALIDO.fullmatch(a) for a in ant):
            errores.append(f'{ident}: antecedentes inválidos (lista no vacía de átomos)')
            continue
        if not isinstance(cons, str) or not NOMBRE_VALIDO.fullmatch(cons):
            errores.append(f'{ident}: consecuente inválido (átomo positivo único)')
            continue
        if len(ant) != len(set(ant)):
            errores.append(f'{ident}: antecedentes repetidos')
        firma = (tuple(sorted(ant)), cons)
        if firma in firmas:
            errores.append(f'{ident}: regla duplicada')
        firmas.add(firma)
        for a in ant:
            grafo[a].add(cons)
        consecuentes.add(cons)
        antecedentes.update(ant)
        reglas_validas.append(r)
    if len(reglas_validas) != len(reglas):
        errores.append('Algunas reglas no permiten análisis de grafo/pruebas')
    else:
        color = {}  # 0 sin visitar, 1 en pila, 2 visitado
        ciclos = []
        def visitar(nodo, pila):
            estado = color.get(nodo, 0)
            if estado == 1:
                ciclos.append(' -> '.join(pila[pila.index(nodo):] + [nodo]))
                return
            if estado == 2:
                return
            color[nodo] = 1
            for siguiente in sorted(grafo[nodo]):
                visitar(siguiente, pila + [siguiente])
            color[nodo] = 2
        for n in sorted(antecedentes | consecuentes):
            if color.get(n, 0) == 0:
                visitar(n, [n])
        if ciclos:
            errores.extend(f'Ciclo: {c}' for c in ciclos)
    entradas = antecedentes - consecuentes
    memoria_global, _, activadas_global = inferir(reglas_validas, entradas) if len(reglas_validas) == len(reglas) else (set(), [], set())
    sin_alcance = sorted(ids - activadas_global)
    if sin_alcance:
        errores.append('Reglas no activables desde hechos base: ' + ', '.join(sin_alcance))
    # Mayor profundidad posible de una prueba; las alternativas pueden tener rutas más cortas.
    profundidad = {a: 0 for a in entradas}
    if not any('Ciclo:' in e for e in errores):
        for _ in range(len(consecuentes) + 1):
            hubo = False
            for r in reglas_validas:
                if all(a in profundidad for a in r['antecedentes']):
                    valor = 1 + max(profundidad[a] for a in r['antecedentes'])
                    if valor > profundidad.get(r['consecuente'], -1):
                        profundidad[r['consecuente']] = valor
                        hubo = True
            if not hubo:
                break
    diagnosticos = sorted(c for c in consecuentes if c.startswith('Dx_'))
    diag_cortos = [d for d in diagnosticos if profundidad.get(d, -1) < 4]
    if diag_cortos:
        errores.append('Diagnósticos sin ruta de cuatro pasos: ' + ', '.join(diag_cortos))
    resultados = []
    cobertura_casos = set()
    for nombre, hechos, objetivo, esperado in CASOS:
        memoria, traza, activadas = inferir(reglas_validas, hechos.split())
        obtenido = objetivo in memoria
        cobertura_casos.update(activadas)
        resultados.append({'nombre': nombre, 'hechos': hechos.split(), 'objetivo': objetivo,
                           'esperado': esperado, 'obtenido': obtenido, 'aprobado': esperado == obtenido,
                           'traza': traza, 'reglas_activadas': sorted(activadas)})
        if obtenido != esperado:
            errores.append(f'Caso {nombre}: esperado {esperado}, obtenido {obtenido}')
    reporte = {
        'archivo': RUTA.name, 'total_reglas': len(reglas), 'hechos_base': len(entradas),
        'diagnosticos_profundidad_maxima': {d: profundidad.get(d) for d in diagnosticos},
        'reglas_activables_desde_hechos_base': len(activadas_global),
        'casos': resultados, 'cobertura_5_casos': {
            'reglas_activadas': len(cobertura_casos), 'total_reglas': len(reglas),
            'porcentaje': round(100 * len(cobertura_casos) / len(reglas), 2) if reglas else 0,
            'reglas_no_activadas': sorted(ids - cobertura_casos),
        },
        'errores': errores, 'aprobado': not errores,
        'advertencia': 'Validación lógica y sintáctica, no verificación de exactitud médica. La profundidad reportada es máxima entre rutas posibles.'
    }
    REPORTE.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'REGLAS: {len(reglas)} | HECHOS BASE: {len(entradas)} | ACTIVABLES: {len(activadas_global)}/{len(reglas)}')
    print('PROFUNDIDAD MÁXIMA DE DIAGNÓSTICOS:', reporte['diagnosticos_profundidad_maxima'])
    for c in resultados:
        print(f"{'OK' if c['aprobado'] else 'ERROR'} | {c['nombre']} | esperado={c['esperado']} | obtenido={c['obtenido']}")
    print(f"COBERTURA 5 CASOS: {len(cobertura_casos)}/{len(reglas)} reglas activables en las pruebas")
    print(f"{'VALIDACIÓN APROBADA' if not errores else 'VALIDACIÓN CON ERRORES'} | Reporte: {REPORTE.name}")
    for error in errores:
        print('ERROR:', error)
    return not errores

if __name__ == '__main__':
    raise SystemExit(0 if validar() else 1)
