"""Pruebas del motor hacia atrás (Persona 4).

Uso: python pruebas_backward.py
Requiere en la misma carpeta: proyecto_inferencia.py, base_conocimiento.json
y reporte_validacion_kb.json.

Genera trazas_backward.txt con la traza (con sangría) de cada caso clínico.
"""

import json
import sys
import tempfile
from pathlib import Path

from proyecto_inferencia import MotorInferencia

BASE = Path(__file__).resolve().parent
KB = BASE / "base_conocimiento.json"
REPORTE = BASE / "reporte_validacion_kb.json"
SALIDA = BASE / "trazas_backward.txt"

fallos = []


def verificar(nombre, condicion):
    print(f"{'OK   ' if condicion else 'ERROR'} | {nombre}")
    if not condicion:
        fallos.append(nombre)


def motor_con_reglas(reglas):
    """Crea un motor con una KB temporal (para probar ciclos y profundidad)."""
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False,
                                     encoding="utf-8") as f:
        json.dump({"reglas": reglas}, f)
    return MotorInferencia(f.name)


# ----------------------------------------------------------
# 1. CASOS BASE
# ----------------------------------------------------------
print("=== Casos base ===")
motor = MotorInferencia(str(KB))

verificar("Objetivo ya en los hechos -> True",
          motor.ejecutar_inferencia_atras(["Fiebre"], "Fiebre") is True)
verificar("  sin reglas usadas", motor.reglas_usadas_atras == [])

verificar("Hechos vacíos -> False",
          motor.ejecutar_inferencia_atras([], "Dx_Gripe") is False)

verificar("Objetivo inexistente en la KB -> False",
          motor.ejecutar_inferencia_atras(["Fiebre"], "Dx_Inventado") is False)

verificar("Objetivo alcanzable -> True",
          motor.ejecutar_inferencia_atras(["Fiebre", "Escalofrios"],
                                          "Sig_Cuadro_Febril") is True)
verificar("  usa solo RESP_01", motor.reglas_usadas_atras == ["RESP_01"])

verificar("Antecedentes parciales -> False",
          motor.ejecutar_inferencia_atras(["Dolor_Muscular", "Cefalea"],
                                          "Sig_Dolor_Sistemico") is False)

hechos = ["Fiebre", "Escalofrios"]
motor.ejecutar_inferencia_atras(hechos, "Sig_Cuadro_Febril")
verificar("No modifica la lista de entrada",
          hechos == ["Fiebre", "Escalofrios"])

motor.ejecutar_inferencia_atras(hechos, "Sig_Cuadro_Febril")
n1 = len(motor.traza_atras)
motor.ejecutar_inferencia_atras(hechos, "Sig_Cuadro_Febril")
verificar("Traza reiniciada entre ejecuciones", len(motor.traza_atras) == n1)

# Varias reglas concluyen lo mismo (OR): RESP_08 falla (falta Inicio_Subito)
# y el motor debe probar la siguiente regla (RESP_50) en vez de rendirse.
verificar("OR entre reglas: RESP_08 falla, RESP_50 prueba el síndrome",
          motor.ejecutar_inferencia_atras(
              ["Fiebre", "Dolor_Muscular", "Escalofrios", "Cefalea"],
              "Sin_Sindrome_Gripal") is True)
verificar("  la prueba usa RESP_50 y no RESP_08",
          "RESP_50" in motor.reglas_usadas_atras
          and "RESP_08" not in motor.reglas_usadas_atras)
verificar("OR entre reglas: RESP_44 prueba el síndrome",
          motor.ejecutar_inferencia_atras(
              ["Fiebre", "Dolor_Muscular", "Cefalea", "Inicio_Subito"],
              "Sin_Sindrome_Gripal") is True)

# ----------------------------------------------------------
# 2. CICLOS Y PROFUNDIDAD (KB temporales, la real es acíclica)
# ----------------------------------------------------------
print("\n=== Ciclos y profundidad ===")
ciclo = motor_con_reglas([
    {"id": "C1", "antecedentes": ["A"], "consecuente": "B"},
    {"id": "C2", "antecedentes": ["B"], "consecuente": "A"},
])
verificar("Ciclo A<->B termina y retorna False",
          ciclo.ejecutar_inferencia_atras(["X"], "A") is False)
verificar("  se detectó el ciclo",
          any(t["evento"] == "CICLO" for t in ciclo.traza_atras))

# Ciclo, pero con una vía alternativa válida: no debe dar falso negativo
ciclo2 = motor_con_reglas([
    {"id": "C1", "antecedentes": ["A"], "consecuente": "B"},
    {"id": "C2", "antecedentes": ["B"], "consecuente": "A"},
    {"id": "C3", "antecedentes": ["X"], "consecuente": "A"},
])
verificar("Ciclo con vía alternativa -> True",
          ciclo2.ejecutar_inferencia_atras(["X"], "B") is True)

cadena = [{"id": f"L{i}", "antecedentes": [f"N{i}"], "consecuente": f"N{i+1}"}
          for i in range(10)]
largo = motor_con_reglas(cadena)
verificar("Cadena de 10 niveles con límite amplio -> True",
          largo.ejecutar_inferencia_atras(["N0"], "N10") is True)
verificar("Cadena de 10 niveles con max_profundidad=5 -> False",
          largo.ejecutar_inferencia_atras(["N0"], "N10",
                                          max_profundidad=5) is False)
verificar("  se reportó corte por PROFUNDIDAD",
          any(t["evento"] == "PROFUNDIDAD" for t in largo.traza_atras))

# ----------------------------------------------------------
# 3. CASOS CLÍNICOS: backward debe coincidir con forward y con Sara
# ----------------------------------------------------------
print("\n=== Casos clínicos (backward vs forward vs reporte) ===")
casos = json.loads(REPORTE.read_text(encoding="utf-8"))["casos_clinicos"]

with open(SALIDA, "w", encoding="utf-8") as f:
    f.write("TRAZAS DEL MOTOR HACIA ATRÁS (BACKWARD CHAINING)\n")
    f.write("=" * 50 + "\n\n")
    for i, caso in enumerate(casos, 1):
        atras = motor.ejecutar_inferencia_atras(caso["hechos"], caso["objetivo"])
        adelante = motor.ejecutar_inferencia(caso["hechos"], caso["objetivo"])
        verificar(f"Caso {i}: {caso['nombre']} "
                  f"(esperado={caso['esperado']}, atrás={atras}, "
                  f"adelante={adelante})",
                  atras == caso["esperado"] == adelante)

        # Reejecutar atrás (el forward pisó solo su propio estado, pero así
        # la traza escrita corresponde sin duda a este caso).
        motor.ejecutar_inferencia_atras(caso["hechos"], caso["objetivo"])
        f.write(f"Caso {i}: {caso['nombre']}\n")
        f.write(f"Hechos iniciales: {', '.join(caso['hechos'])}\n")
        f.write(f"Objetivo: {caso['objetivo']}\n")
        f.write(f"Resultado: {atras} | llamadas: {motor.num_llamadas} "
                f"| profundidad máx: {motor.profundidad_maxima} "
                f"| reglas en la prueba: {len(motor.reglas_usadas_atras)}\n")
        f.write(f"Reglas de la prueba (orden): "
                f"{', '.join(motor.reglas_usadas_atras) or '(ninguna)'}\n")
        for t in motor.traza_atras:
            r = f" [{t['regla']}]" if t["regla"] else ""
            f.write(f"  {'  ' * t['nivel']}{t['evento']}: {t['meta']}{r}\n")
        f.write("\n")

# Equivalencia en TODOS los diagnósticos/alertas con los hechos de cada caso
print("\n=== Equivalencia forward/backward sobre todas las metas ===")
metas = sorted({r.consecuente for r in motor.reglas})
discrepancias = 0
for caso in casos:
    for meta in metas:
        if motor.ejecutar_inferencia(caso["hechos"], meta) != \
           motor.ejecutar_inferencia_atras(caso["hechos"], meta):
            discrepancias += 1
verificar(f"0 discrepancias en {len(casos) * len(metas)} comparaciones",
          discrepancias == 0)

print(f"\nTrazas guardadas en {SALIDA.name}")
if fallos:
    print(f"\n{len(fallos)} PRUEBA(S) FALLARON:")
    for n in fallos:
        print("  -", n)
    sys.exit(1)
print("TODAS LAS PRUEBAS APROBADAS")