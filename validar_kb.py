
"""Validador lógico de la base de conocimiento.

No valida la exactitud clínica de los diagnósticos.

Uso: python validar_kb.py
Requiere base_conocimiento.json en la misma carpeta.
Genera reporte_validacion_kb.json.
"""

import json
import re
from collections import defaultdict
from pathlib import Path


BASE = Path(__file__).resolve().parent
RUTA = BASE / "base_conocimiento.json"
REPORTE = BASE / "reporte_validacion_kb.json"

NOMBRE_VALIDO = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


# ==========================================================
# 1. CASOS CLÍNICOS
# ==========================================================

CASOS = [
    (
        "Gripe",
        "Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular "
        "Inicio_Subito Tos_Seca",
        "Dx_Gripe",
        True
    ),
    (
        "COVID-19",
        "Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular "
        "Inicio_Subito Perdida_Olfato_Gusto",
        "Dx_COVID19",
        True
    ),
    (
        "Neumonia con alerta",
        "Fiebre Dificultad_Respiratoria Taquipnea "
        "Crepitantes_Pulmonares Tos_Productiva Dolor_Toracico "
        "Saturacion_Oxigeno_Baja",
        "Alerta_Gravedad_Extrema",
        True
    ),
    (
        "Tuberculosis con alerta",
        "Perdida_Peso Sudoracion_Nocturna Fatiga Perdida_Apetito "
        "Tos_Prolongada Hemoptisis",
        "Alerta_Riesgo_Alto",
        True
    ),
    (
        "No demostrable",
        "Fiebre Escalofrios Tos_Seca",
        "Dx_COVID19",
        False
    ),
    (
        "Resfriado con alerta",
        "Dolor_Garganta Congestion_Nasal Tos_Seca Fatiga "
        "Dificultad_Respiratoria",
        "Alerta_Complicacion_Respiratoria",
        True
    ),
    (
        "Bronquitis con alerta",
        "Tos_Productiva Sibilancias Congestion_Nasal Dolor_Garganta "
        "Dificultad_Respiratoria Dolor_Toracico",
        "Alerta_Progresion_Pulmonar",
        True
    ),
    (
        "Asma con alerta",
        "Sibilancias Episodios_Recurrentes Tos_Seca "
        "Dificultad_Respiratoria Saturacion_Oxigeno_Baja",
        "Alerta_Crisis_Asmatica_Grave",
        True
    ),
    (
        "Neumonia: cianosis y confusion",
        "Fiebre Dificultad_Respiratoria Taquipnea "
        "Crepitantes_Pulmonares Tos_Productiva Dolor_Toracico "
        "Cianosis Confusion",
        "Alerta_Gravedad_Extrema",
        True
    ),
    (
        "COVID-19 con alerta",
        "Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular "
        "Inicio_Subito Perdida_Olfato_Gusto "
        "Dificultad_Respiratoria Saturacion_Oxigeno_Baja",
        "Alerta_Gravedad_Extrema",
        True
    ),
    (
        "Gripe con alerta",
        "Fiebre Escalofrios Dolor_Muscular Cefalea Dolor_Articular "
        "Inicio_Subito Tos_Seca Dificultad_Respiratoria",
        "Alerta_Complicacion_Respiratoria",
        True
    ),
]


# ==========================================================
# 2. INFERENCIA INDEPENDIENTE PARA VALIDAR LA KB
# ==========================================================

def inferir(reglas, hechos):
    """
    Aplica reglas Horn positivas hasta alcanzar un punto fijo.

    Retorna:
    - memoria: hechos iniciales y derivados
    - traza: orden de nuevos hechos inferidos
    - activadas: identificadores de reglas cuyos antecedentes
      se cumplieron
    """

    memoria = set(hechos)
    traza = []
    activadas = set()

    while True:
        cambio = False

        for regla in reglas:
            antecedentes = set(regla["antecedentes"])

            if antecedentes.issubset(memoria):
                activadas.add(regla["id"])

                consecuente = regla["consecuente"]

                if consecuente not in memoria:
                    memoria.add(consecuente)

                    traza.append({
                        "regla": regla["id"],
                        "hecho": consecuente
                    })

                    cambio = True

        if not cambio:
            return memoria, traza, activadas


# ==========================================================
# 3. PRUEBAS DE CASOS LÍMITE
# ==========================================================

def casos_limite(reglas, entradas):
    """
    Comprueba propiedades básicas de las reglas Horn.
    """

    pruebas = []

    objetivo = "Objetivo_Sin_Regla_Para_Probar"

    if any(r["consecuente"] == objetivo for r in reglas):
        objetivo = "Objetivo_Imposible_999999"

    hechos, _, _ = inferir(reglas, ["Hecho_De_Prueba"])

    # Caso 1: un hecho inicial debe permanecer en memoria.
    pruebas.append({
        "nombre": "Objetivo ya es hecho inicial",
        "aprobado": "Hecho_De_Prueba" in hechos
    })

    # Caso 2: no se debe inventar una conclusión.
    pruebas.append({
        "nombre": "Objetivo sin regla ni hecho inicial",
        "aprobado": objetivo not in hechos
    })

    # Caso 3: una regla no se activa si falta un antecedente.
    regla = next(
        (r for r in reglas if len(r["antecedentes"]) >= 2),
        None
    )

    if regla:
        hechos_parciales = regla["antecedentes"][:-1]

        memoria, _, activadas = inferir(
            [regla],
            hechos_parciales
        )

        pruebas.append({
            "nombre": "Regla con antecedente faltante",
            "aprobado": (
                regla["id"] not in activadas
                and regla["consecuente"] not in memoria
            )
        })

    # Caso 4: agregar hechos no debe eliminar conclusiones.
    muestra = set(sorted(entradas)[:5])

    memoria_1, _, _ = inferir(reglas, muestra)
    memoria_2, _, _ = inferir(
        reglas,
        muestra | set(entradas)
    )

    pruebas.append({
        "nombre": "Monotonia al agregar hechos",
        "aprobado": memoria_1.issubset(memoria_2)
    })

    return pruebas


# ==========================================================
# 4. VALIDACIÓN ESTRUCTURAL Y LÓGICA
# ==========================================================

def validar():

    errores = []

    if not RUTA.is_file():
        raise FileNotFoundError(
            f"Falta {RUTA.name}; coloca el script junto al JSON"
        )

    datos = json.loads(
        RUTA.read_text(encoding="utf-8-sig")
    )

    reglas = (
        datos.get("reglas")
        if isinstance(datos, dict)
        else None
    )

    if not isinstance(reglas, list):
        raise ValueError(
            'Se requiere un objeto JSON con una lista en "reglas"'
        )

    # Verificar cantidad mínima de reglas.
    if len(reglas) < 50:
        errores.append(
            f"Se requieren 50 reglas como mínimo; hay {len(reglas)}"
        )

    ids = set()
    firmas = set()

    grafo = defaultdict(set)

    consecuentes = set()
    antecedentes = set()

    reglas_validas = []

    # ------------------------------------------------------
    # 4.1 Validación de estructura y duplicados
    # ------------------------------------------------------

    for numero, regla in enumerate(reglas, 1):

        if (
            not isinstance(regla, dict)
            or set(regla) != {
                "id",
                "antecedentes",
                "consecuente"
            }
        ):
            errores.append(
                f"Regla {numero}: claves inválidas"
            )
            continue

        ident = regla["id"]
        ant = regla["antecedentes"]
        cons = regla["consecuente"]

        if (
            not isinstance(ident, str)
            or not NOMBRE_VALIDO.fullmatch(ident)
        ):
            errores.append(
                f"Regla {numero}: ID inválido"
            )
            continue

        if ident in ids:
            errores.append(
                f"ID repetido: {ident}"
            )

        ids.add(ident)

        if (
            not isinstance(ant, list)
            or not ant
            or not all(
                isinstance(a, str)
                and NOMBRE_VALIDO.fullmatch(a)
                for a in ant
            )
        ):
            errores.append(
                f"{ident}: antecedentes inválidos"
            )
            continue

        if (
            not isinstance(cons, str)
            or not NOMBRE_VALIDO.fullmatch(cons)
        ):
            errores.append(
                f"{ident}: consecuente inválido"
            )
            continue

        if len(ant) != len(set(ant)):
            errores.append(
                f"{ident}: antecedente repetido"
            )

        firma = (tuple(sorted(ant)), cons)

        if firma in firmas:
            errores.append(
                f"{ident}: regla idéntica duplicada"
            )

        firmas.add(firma)

        for antecedente in ant:
            grafo[antecedente].add(cons)

        consecuentes.add(cons)
        antecedentes.update(ant)

        reglas_validas.append(regla)

    estructuralmente_validas = (
        len(reglas_validas) == len(reglas)
        and not any(
            any(
                termino in error
                for termino in [
                    "inválid",
                    "repetid",
                    "duplicad"
                ]
            )
            for error in errores
        )
    )

    # ------------------------------------------------------
    # 4.2 Detección de ciclos mediante DFS
    # ------------------------------------------------------

    nodos = antecedentes | consecuentes

    color = {}
    ciclos = []

    def dfs(nodo, pila):

        if color.get(nodo) == 1:
            ciclos.append(
                " -> ".join(
                    pila[pila.index(nodo):] + [nodo]
                )
            )
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
        errores.extend(
            "Ciclo: " + ciclo
            for ciclo in ciclos
        )

    # ------------------------------------------------------
    # 4.3 Alcanzabilidad y profundidad
    # ------------------------------------------------------

    entradas = antecedentes - consecuentes

    activadas_global = set()

    profundidad_min = {}
    profundidad_max = {}

    if estructuralmente_validas and not ciclos:

        _, _, activadas_global = inferir(
            reglas_validas,
            entradas
        )

        no_activables = sorted(
            ids - activadas_global
        )

        if no_activables:
            errores.append(
                "Reglas sin alcance: "
                + ", ".join(no_activables)
            )

        profundidad_min = {
            hecho: 0 for hecho in entradas
        }

        profundidad_max = {
            hecho: 0 for hecho in entradas
        }

        for _ in range(len(nodos) + 1):

            cambio = False

            for regla in reglas_validas:

                ant = regla["antecedentes"]
                cons = regla["consecuente"]

                if all(
                    a in profundidad_min
                    for a in ant
                ):
                    distancia = 1 + max(
                        profundidad_min[a]
                        for a in ant
                    )

                    if distancia < profundidad_min.get(
                        cons,
                        float("inf")
                    ):
                        profundidad_min[cons] = distancia
                        cambio = True

                if all(
                    a in profundidad_max
                    for a in ant
                ):
                    distancia = 1 + max(
                        profundidad_max[a]
                        for a in ant
                    )

                    if distancia > profundidad_max.get(
                        cons,
                        -1
                    ):
                        profundidad_max[cons] = distancia
                        cambio = True

            if not cambio:
                break

    # ------------------------------------------------------
    # 4.4 Verificar profundidad de diagnósticos
    # ------------------------------------------------------

    diagnosticos = sorted(
        cons
        for cons in consecuentes
        if cons.startswith("Dx_")
    )

    if estructuralmente_validas and not ciclos:

        cortos = [
            d for d in diagnosticos
            if profundidad_min.get(d, -1) < 4
        ]

        inalcanzables = [
            d for d in diagnosticos
            if d not in profundidad_min
        ]

        if cortos:
            errores.append(
                "Diagnósticos con prueba de menos de 4 pasos: "
                + ", ".join(cortos)
            )

        if inalcanzables:
            errores.append(
                "Diagnósticos inalcanzables: "
                + ", ".join(inalcanzables)
            )

    # ------------------------------------------------------
    # 4.5 Ejecutar los casos clínicos
    # ------------------------------------------------------

    resultados = []
    cobertura = set()
    limites = []

    if estructuralmente_validas:

        for nombre, hechos, objetivo, esperado in CASOS:

            memoria, traza, activadas = inferir(
                reglas_validas,
                hechos.split()
            )

            obtenido = objetivo in memoria

            cobertura.update(activadas)

            resultados.append({
                "nombre": nombre,
                "hechos": hechos.split(),
                "objetivo": objetivo,
                "esperado": esperado,
                "obtenido": obtenido,
                "aprobado": obtenido == esperado,
                "traza": traza,
                "reglas_activadas": sorted(activadas)
            })

            if obtenido != esperado:
                errores.append(
                    f"Caso {nombre}: "
                    f"esperado={esperado}, obtenido={obtenido}"
                )

        # Ejecutar pruebas de casos límite.
        limites = casos_limite(
            reglas_validas,
            entradas
        )

        for prueba in limites:

            if not prueba["aprobado"]:
                errores.append(
                    "Caso límite falló: "
                    + prueba["nombre"]
                )

    # ------------------------------------------------------
    # 4.6 Generar reporte de validación
    # ------------------------------------------------------

    reporte = {
        "archivo": RUTA.name,
        "total_reglas": len(reglas),
        "hechos_base": len(entradas),
        "reglas_activables": len(activadas_global),

        "profundidad_minima_diagnosticos": {
            d: profundidad_min.get(d)
            for d in diagnosticos
        },

        "profundidad_maxima_diagnosticos": {
            d: profundidad_max.get(d)
            for d in diagnosticos
        },

        "cantidad_casos_clinicos": len(CASOS),
        "casos_clinicos": resultados,
        "casos_limite": limites,

        "cobertura_casos": {
            "activadas": len(cobertura),
            "total": len(reglas),
            "porcentaje": (
                round(
                    100 * len(cobertura) / len(reglas),
                    2
                )
                if reglas else 0
            ),
            "no_activadas": sorted(
                ids - cobertura
            )
        },

        "errores": errores,
        "aprobado": not errores,

        "nota": (
            "Validacion formal de un modelo academico; "
            "no confirma diagnosticos ni exactitud clinica. "
            "Se usa un evaluador Forward independiente, "
            "no los motores del equipo."
        )
    }

    REPORTE.write_text(
        json.dumps(
            reporte,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    # ------------------------------------------------------
    # 4.7 Mostrar resultados en la terminal
    # ------------------------------------------------------

    print(f"CASOS CLINICOS: {len(CASOS)}")

    print(
        f"REGLAS: {len(reglas)} | "
        f"ACTIVABLES: {len(activadas_global)}/{len(reglas)}"
    )

    print(
        "PROFUNDIDAD MÍNIMA:",
        reporte["profundidad_minima_diagnosticos"]
    )

    print(
        "PROFUNDIDAD MÁXIMA:",
        reporte["profundidad_maxima_diagnosticos"]
    )

    for caso in resultados:

        estado = (
            "OK" if caso["aprobado"] else "ERROR"
        )

        print(
            f"{estado} | {caso['nombre']} | "
            f"esperado={caso['esperado']} | "
            f"obtenido={caso['obtenido']}"
        )

    for prueba in limites:

        estado = (
            "OK" if prueba["aprobado"] else "ERROR"
        )

        print(
            f"{estado} | Límite: {prueba['nombre']}"
        )

    porcentaje = reporte[
        "cobertura_casos"
    ]["porcentaje"]

    print(
        f"COBERTURA: {len(cobertura)}/{len(reglas)} "
        f"({porcentaje}%)"
    )

    if errores:
        print("VALIDACIÓN CON ERRORES")
    else:
        print("VALIDACIÓN APROBADA")

    print("Reporte:", REPORTE.name)

    for error in errores:
        print("ERROR:", error)

    return not errores


# ==========================================================
# 5. EJECUCIÓN
# ==========================================================

if __name__ == "__main__":
    raise SystemExit(
        0 if validar() else 1
    )
