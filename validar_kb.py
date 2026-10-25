"""AuditorÃ­a estructural y pruebas de reglas Horn; no sustituye los motores del equipo."""
import json
from collections import defaultdict
from pathlib import Path

ruta = Path(__file__).with_name('base_conocimiento.json')
reglas = json.loads(ruta.read_text(encoding='utf-8'))['reglas']
ids = [r['id'] for r in reglas]
assert len(reglas) >= 50
assert len(ids) == len(set(ids)), 'ID duplicado'
assert len({(tuple(sorted(r['antecedentes'])),r['consecuente']) for r in reglas}) == len(reglas), 'Reglas duplicadas'
assert all(r['antecedentes'] and len(r['antecedentes']) == len(set(r['antecedentes'])) and isinstance(r['consecuente'],str) for r in reglas)
consecuentes = {r['consecuente'] for r in reglas}
entradas = {a for r in reglas for a in r['antecedentes']} - consecuentes

def razonar(hechos):
    memoria = set(hechos)
    traza = []
    while True:
        nuevas = False
        for regla in reglas:
            if set(regla['antecedentes']) <= memoria and regla['consecuente'] not in memoria:
                memoria.add(regla['consecuente'])
                traza.append((regla['id'], regla['consecuente']))
                nuevas = True
        if not nuevas:
            return memoria, traza

# DFS de dependencias: si A es antecedente de una regla que produce B, hay arista A -> B.
grafo=defaultdict(set)
for r in reglas:
    for a in r['antecedentes']:
        grafo[a].add(r['consecuente'])
visitando=set(); visitados=set()
def dfs(n):
    if n in visitando: raise AssertionError(f'Ciclo detectado en {n}')
    if n in visitados: return
    visitando.add(n)
    for vecino in grafo[n]: dfs(vecino)
    visitando.remove(n);visitados.add(n)
for nodo in list(grafo):dfs(nodo)

# Profundidad mÃ¡xima desde hechos base, en un DAG.
profundidades={x:0 for x in entradas}
for _ in range(len(reglas)+1):
    hubo_cambio=False
    for r in reglas:
        if all(x in profundidades for x in r['antecedentes']):
            nuevo=1+max(profundidades[x] for x in r['antecedentes'])
            if nuevo>profundidades.get(r['consecuente'],-1):
                profundidades[r['consecuente']]=nuevo;hubo_cambio=True
    if not hubo_cambio:break
assert consecuentes <= set(profundidades),'Hay reglas inalcanzables'
assert all(profundidades[x] >= 4 for x in consecuentes if x.startswith('Dx_'))

casos=[
('Gripe','Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular Inicio_Subito Tos_Seca','Dx_Gripe',True),
('COVID-19','Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular Inicio_Subito Perdida_Olfato_Gusto','Dx_COVID19',True),
('Alerta neumonÃ­a','Fiebre Dificultad_Respiratoria Taquipnea Crepitantes_Pulmonares Tos_Productiva Dolor_Toracico Saturacion_Oxigeno_Baja','Alerta_Gravedad_Extrema',True),
('Alerta tuberculosis','Perdida_Peso Sudoracion_Nocturna Fatiga Perdida_Apetito Tos_Prolongada Hemoptisis','Alerta_Riesgo_Alto',True),
('No demostrable','Fiebre Escalofrios Tos_Seca','Dx_COVID19',False),
]
print(f'Reglas: {len(reglas)} | SÃ­ntomas de entrada: {len(entradas)} | Sin ciclos | DiagnÃ³sticos con profundidad >= 4')
for nombre,sintomas,objetivo,esperado in casos:
    memoria,traza=razonar(sintomas.split())
    resultado=objetivo in memoria
    assert resultado == esperado, f'{nombre}: esperado={esperado}; obtenido={resultado}'
    print(f'\n{nombre} | Objetivo={objetivo} | Esperado={esperado} | Obtenido={resultado}')
    for id,consecuente in traza:
        print(f'  {id} -> {consecuente}')
