import json

# ==========================================================
# PARTE 1: ESTRUCTURA DE DATOS (NO MODIFICAR)
# ==========================================================
class Regla:
    def __init__(self, id_regla, antecedentes, consecuente):
        self.id_regla = id_regla
        self.antecedentes = set(antecedentes)  
        self.consecuente = consecuente

    def __str__(self):
        return f"{self.id_regla}: {' AND '.join(self.antecedentes)} -> {self.consecuente}"

class MotorInferencia:
    def __init__(self, ruta_kb):
        self.reglas = self.cargar_kb(ruta_kb)
        self.memoria_trabajo = set()
        self.traza_explicacion = [] # Sugerencia para almacenar el orden de las reglas activadas

    def cargar_kb(self, ruta):
        """Carga las reglas desde un archivo JSON."""
        try:
            with open(ruta, 'r', encoding='utf-8') as f:
                datos = json.load(f)
            return [Regla(r.get('id'), r['antecedentes'], r['consecuente']) for r in datos['reglas']]
        except Exception as e:
            print(f"Error al cargar la Base de Conocimiento: {e}")
            return []

    # ==========================================================
    # PARTE 2: MOTORES DE INFERENCIA (A DESARROLLAR)
    # ==========================================================
    def ejecutar_inferencia(self, hechos_iniciales, objetivo):
        """
        Motor de Encadenamiento hacia Adelante (Forward Chaining).
        Debe retornar True si el objetivo es consecuencia lógica, False en caso contrario.
        Además, debe registrar la traza de explicación.
        """
        self.memoria_trabajo = set(hechos_iniciales)
        
        # TODO: Implementar la lógica iterativa basada en el punto fijo.
        
        return False # Cambiar por el resultado lógico

    def ejecutar_inferencia_atras(self, hechos_iniciales, objetivo):
        """
        Motor de Encadenamiento hacia Atrás (Backward Chaining).
        Debe retornar True si el objetivo puede ser probado, False en caso contrario.
        Debe manejar adecuadamente la recursividad (goal-driven) y los casos base.
        """
        
        # TODO: Implementar la lógica recursiva orientada a objetivos.
        
        return False # Cambiar por el resultado lógico

# ==========================================================
# PARTE 3: EJECUCIÓN (PUEDEN MODIFICAR PARA PRUEBAS)
# ==========================================================
if __name__ == "__main__":
    # 1. Inicializar el motor con el archivo de reglas
    motor = MotorInferencia("base_conocimiento.json")

    # 2. Definir caso clínico de prueba
    sintomas = ["Fiebre", "Tos", "Dificultad_Respiratoria"]
    hipotesis = "Neumonia"

    print(f"--- Sistema Experto de Diagnóstico ---")
    print(f"Síntomas iniciales: {sintomas}")
    print(f"Objetivo a verificar: {hipotesis}\n")

    # 3. Ejecutar Inferencia hacia Adelante
    print("--- Motor Hacia Adelante ---")
    resultado_adelante = motor.ejecutar_inferencia(sintomas, hipotesis)
    print(f"¿Es consecuencia lógica?: {resultado_adelante}\n")

    # 4. Ejecutar Inferencia hacia Atrás
    print("--- Motor Hacia Atrás ---")
    resultado_atras = motor.ejecutar_inferencia_atras(sintomas, hipotesis)
    print(f"¿Es demostrable?: {resultado_atras}")