"""Comparación forward vs backward sobre los casos clínicos (Persona 4).

Uso: python comparar_motores.py
  - Imprime la comparación por consola.
  - Genera comparacion_motores.md (en VS Code: Ctrl+Shift+V para ver la
    vista previa). No requiere instalar nada.
"""

import json
from pathlib import Path
from time import perf_counter

from proyecto_inferencia import MotorInferencia

BASE = Path(__file__).resolve().parent
KB = BASE / "base_conocimiento.json"
REPORTE = BASE / "reporte_validacion_kb.json"
SALIDA_MD = BASE / "comparacion_motores.md"
REPETICIONES = 2000  # para que el tiempo (microsegundos) sea medible


# ----------------------------------------------------------
# 1. DATOS
# ----------------------------------------------------------
def medir(funcion, *args):
    """Tiempo promedio por ejecución en microsegundos."""
    inicio = perf_counter()
    for _ in range(REPETICIONES):
        funcion(*args)
    return (perf_counter() - inicio) / REPETICIONES * 1e6


def calcular_filas():
    motor = MotorInferencia(str(KB))
    casos = json.loads(REPORTE.read_text(encoding="utf-8"))["casos_clinicos"]
    filas = []
    for i, c in enumerate(casos, 1):
        h, o = c["hechos"], c["objetivo"]
        r_f = motor.ejecutar_inferencia(h, o)
        pasadas, disparos = motor.num_pasadas, len(motor.traza_explicacion)
        r_b = motor.ejecutar_inferencia_atras(h, o)
        llamadas, prof = motor.num_llamadas, motor.profundidad_maxima
        reglas_b = len(motor.reglas_usadas_atras)
        t_f = medir(motor.ejecutar_inferencia, h, o)
        t_b = medir(motor.ejecutar_inferencia_atras, h, o)
        filas.append({"n": i, "caso": c["nombre"], "objetivo": o,
                      "r_f": r_f, "pasadas": pasadas, "disparos": disparos,
                      "t_f": t_f, "r_b": r_b, "llamadas": llamadas,
                      "reglas_b": reglas_b, "prof": prof, "t_b": t_b})
    return motor, filas


def promedio(filas, clave):
    return sum(f[clave] for f in filas) / len(filas)


# ----------------------------------------------------------
# 2. TABLAS (las mismas para consola y Markdown)
# ----------------------------------------------------------
def construir_tablas(filas):
    """Devuelve [(titulo, encabezados, filas, alineaciones)].
    Alineación: 'l' izquierda, 'c' centro, 'r' derecha."""
    si_no = lambda v: "True" if v else "False"

    casos = (
        "Casos clínicos",
        ["#", "Caso", "Objetivo", "Forward", "Backward"],
        [[f["n"], f["caso"], f["objetivo"], si_no(f["r_f"]), si_no(f["r_b"])]
         for f in filas],
        "rllcc")

    fwd = (
        "Motor hacia adelante (Forward)",
        ["#", "Caso", "Pasadas", "Reglas disparadas", "Tiempo (us)"],
        [[f["n"], f["caso"], f["pasadas"], f["disparos"], f'{f["t_f"]:.1f}']
         for f in filas]
        + [["", "Promedio", f'{promedio(filas, "pasadas"):.1f}',
            f'{promedio(filas, "disparos"):.1f}',
            f'{promedio(filas, "t_f"):.1f}']],
        "rlccr")

    bwd = (
        "Motor hacia atrás (Backward)",
        ["#", "Caso", "Llamadas", "Reglas en la prueba", "Profundidad máx.",
         "Tiempo (us)"],
        [[f["n"], f["caso"], f["llamadas"], f["reglas_b"], f["prof"],
          f'{f["t_b"]:.1f}'] for f in filas]
        + [["", "Promedio", f'{promedio(filas, "llamadas"):.1f}',
            f'{promedio(filas, "reglas_b"):.1f}',
            f'{promedio(filas, "prof"):.1f}',
            f'{promedio(filas, "t_b"):.1f}']],
        "rlcccr")

    resumen = (
        "Resumen (promedio por caso)",
        ["Métrica", "Forward", "Backward"],
        [["Reglas aplicadas", f'{promedio(filas, "disparos"):.1f}',
          f'{promedio(filas, "reglas_b"):.1f}'],
         ["Tiempo (us)", f'{promedio(filas, "t_f"):.1f}',
          f'{promedio(filas, "t_b"):.1f}']],
        "lcc")
    return [casos, fwd, bwd, resumen]


def a_consola(titulo, enc, filas, alin):
    filas = [[str(v) for v in f] for f in filas]
    ancho = [max(len(enc[i]), *(len(f[i]) for f in filas))
             for i in range(len(enc))]

    def alinear(texto, i):
        return {"l": texto.ljust(ancho[i]), "r": texto.rjust(ancho[i]),
                "c": texto.center(ancho[i])}[alin[i]]

    sep = "+" + "+".join("-" * (w + 2) for w in ancho) + "+"
    linea = lambda f: "| " + " | ".join(
        alinear(v, i) for i, v in enumerate(f)) + " |"
    out = [f"\n{titulo}", sep, linea(enc), sep]
    out += [linea(f) for f in filas]
    out.append(sep)
    return "\n".join(out)


def a_markdown(titulo, enc, filas, alin):
    filas = [[str(v) for v in f] for f in filas]
    # La fila "Promedio" va en negrita en Markdown.
    filas = [[f"**{v}**" if v != "" and f[1] == "Promedio" else v for v in f]
             if len(f) > 1 and f[1] == "Promedio" else f for f in filas]
    ancho = [max(len(enc[i]), *(len(f[i]) for f in filas))
             for i in range(len(enc))]
    ancho = [max(w, 3) for w in ancho]

    def alinear(texto, i):
        return {"l": texto.ljust(ancho[i]), "r": texto.rjust(ancho[i]),
                "c": texto.center(ancho[i])}[alin[i]]

    def divisor(i):
        w = ancho[i]
        return {"l": ":" + "-" * (w + 1), "r": "-" * (w + 1) + ":",
                "c": ":" + "-" * w + ":"}[alin[i]]

    linea = lambda f: "| " + " | ".join(
        alinear(v, i) for i, v in enumerate(f)) + " |"
    out = [f"## {titulo}", "", linea(enc),
           "|" + "|".join(divisor(i) for i in range(len(enc))) + "|"]
    out += [linea(f) for f in filas]
    return "\n".join(out)


# ----------------------------------------------------------
# 3. SALIDA
# ----------------------------------------------------------
if __name__ == "__main__":
    motor, filas = calcular_filas()
    tablas = construir_tablas(filas)
    coinciden = all(f["r_f"] == f["r_b"] for f in filas)
    veredicto = (f"Resultados idénticos en los {len(filas)} casos: "
                 f"{'sí' if coinciden else 'NO'}.")
    cabecera = (f"KB de {len(motor.reglas)} reglas | {len(filas)} casos "
                f"clínicos | tiempos: promedio de {REPETICIONES} ejecuciones")

    # Consola
    print("COMPARACIÓN FORWARD VS BACKWARD")
    print(cabecera)
    for t in tablas:
        print(a_consola(*t))
    print(f"\n{veredicto}")

    # Markdown
    md = ["# Comparación Forward vs Backward", "", cabecera.replace("|", "·"),
          ""]
    for t in tablas:
        md += [a_markdown(*t), ""]
    md.append(veredicto)
    SALIDA_MD.write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nMarkdown guardado en {SALIDA_MD.name} ")