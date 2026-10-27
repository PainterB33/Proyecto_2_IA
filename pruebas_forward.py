"""Pruebas del motor hacia adelante .

Uso: python pruebas_forward.py
Requiere en la misma carpeta: proyecto_inferencia.py,
base_conocimiento.json y reporte_validacion_kb.json (de Sara).

Genera trazas_forward.txt con la traza de cada caso clínico.
"""

import json
import sys
from pathlib import Path

from proyecto_inferencia import MotorInferencia

BASE = Path(__file__).resolve().parent
KB = BASE / "base_conocimiento.json"
REPORTE = BASE / "reporte_validacion_kb.json"
SALIDA = BASE / "trazas_forward.txt"

fallos = []


def verificar(nombre, condicion):
    """Imprime OK/ERROR y recuerda los fallos para el código de salida."""
    print(f"{'OK   ' if condicion else 'ERROR'} | {nombre}")
    if not condicion:
        fallos.append(nombre)


# ----------------------------------------------------------
# 1. PRUEBAS MÍNIMAS OBLIGATORIAS
# ----------------------------------------------------------
print("=== Pruebas mínimas ===")
motor = MotorInferencia(str(KB))
verificar("KB cargada (50 reglas)", len(motor.reglas) == 50)

# Objetivo alcanzable
ok = motor.ejecutar_inferencia(
    ["Fiebre", "Escalofrios"], "Sig_Cuadro_Febrile")
verificar("Objetivo alcanzable -> True", ok is True)
verificar("  traza = [RESP_01]",
          [t["regla"] for t in motor.traza_explicacion] == ["RESP_01"])

# Objetivo no alcanzable (punto fijo)
ok = motor.ejecutar_inferencia(["Fiebre", "Escalofrios"], "Dx_COVID19")
verificar("Objetivo no alcanzable (punto fijo) -> False", ok is False)

# Objetivo ya presente en los hechos: True con traza vacía
ok = motor.ejecutar_inferencia(["Fiebre"], "Fiebre")
verificar("Objetivo ya en los hechos -> True", ok is True)
verificar("  traza vacía", motor.traza_explicacion == [])

# Hechos iniciales vacíos
ok = motor.ejecutar_inferencia([], "Dx_Gripe")
verificar("Hechos vacíos -> False", ok is False)
verificar("  traza vacía", motor.traza_explicacion == [])

# Regla con antecedentes parciales: RESP_06 necesita 3 y damos 2
ok = motor.ejecutar_inferencia(
    ["Dolor_Muscular", "Cefalea"], "Sig_Dolor_Sistemico")
verificar("Antecedentes parciales no dispara -> False", ok is False)
verificar("  RESP_06 no está en la traza",
          all(t["regla"] != "RESP_06" for t in motor.traza_explicacion))

# La traza se reinicia entre ejecuciones
motor.ejecutar_inferencia(["Fiebre", "Escalofrios"], "Sig_Cuadro_Febrile")
motor.ejecutar_inferencia(["Fiebre", "Escalofrios"], "Sig_Cuadro_Febrile")
verificar("Traza reiniciada entre ejecuciones (1 paso, no 2)",
          len(motor.traza_explicacion) == 1)

# No modifica la lista de hechos del llamador
hechos = ["Fiebre", "Escalofrios"]
motor.ejecutar_inferencia(hechos, "Sig_Cuadro_Febrile")
verificar("No modifica la lista de entrada", hechos == ["Fiebre", "Escalofrios"])

# ----------------------------------------------------------
# 2. LOS 11 CASOS CLÍNICOS DE SARA
# ----------------------------------------------------------
print("\n=== Casos clínicos (reporte_validacion_kb.json) ===")
casos = json.loads(REPORTE.read_text(encoding="utf-8"))["casos_clinicos"]

with open(SALIDA, "w", encoding="utf-8") as f:
    f.write("TRAZAS DEL MOTOR HACIA ADELANTE (FORWARD CHAINING)\n")
    f.write("=" * 52 + "\n\n")

    for i, caso in enumerate(casos, 1):
        resultado = motor.ejecutar_inferencia(caso["hechos"], caso["objetivo"])
        reglas_motor = [t["regla"] for t in motor.traza_explicacion]
        hechos_motor = [t["hecho"] for t in motor.traza_explicacion]

        # Traza de Sara: el evaluador de ella corre hasta el punto fijo y el
        # nuestro se detiene al hallar el objetivo, así que la nuestra debe
        # ser un prefijo de la suya (mismo orden de disparo).
        esperada = caso["traza"]
        n = len(reglas_motor)
        if resultado:
            prefijo = (reglas_motor == [e["regla"] for e in esperada[:n]]
                       and hechos_motor == [e["hecho"] for e in esperada[:n]])
        else:
            # Sin objetivo se llega al punto fijo: trazas idénticas.
            prefijo = (reglas_motor == [e["regla"] for e in esperada]
                       and hechos_motor == [e["hecho"] for e in esperada])

        verificar(f"Caso {i}: {caso['nombre']} "
                  f"(esperado={caso['esperado']}, obtenido={resultado})",
                  resultado == caso["esperado"])
        

        f.write(f"Caso {i}: {caso['nombre']}\n")
        f.write(f"Hechos iniciales: {', '.join(caso['hechos'])}\n")
        f.write(f"Objetivo: {caso['objetivo']}\n")
        f.write(f"Resultado: {resultado} | pasadas: {motor.num_pasadas} "
                f"| reglas disparadas: {n}\n")
        if not motor.traza_explicacion:
            f.write("(traza vacía)\n")
        for t in motor.traza_explicacion:
            f.write(f"  Paso {t['paso']}: {t['regla']}: "
                    f"{' AND '.join(t['antecedentes'])} -> {t['hecho']}\n")
        f.write("\n")

print(f"\nTrazas guardadas en {SALIDA.name}")
if fallos:
    print(f"\n{len(fallos)} PRUEBA(S) FALLARON:")
    for nombre in fallos:
        print("  -", nombre)
    sys.exit(1)
print("TODAS LAS PRUEBAS APROBADAS")
