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
        
        Estrategia: punto fijo guiado por datos (data-driven).
        Se repiten pasadas completas sobre las reglas. En cada pasada se
        dispara toda regla que cumpla DOS condiciones:
          (a) todos sus antecedentes están en memoria_trabajo, y
          (b) su consecuente todavía NO está en memoria_trabajo.
        El algoritmo se detiene con True apenas el objetivo aparece en la
        memoria, o con False cuando una pasada completa no agrega ningún
        hecho nuevo (punto fijo).
 
        Cada disparo se registra en self.traza_explicacion como un diccionario
        con el mismo formato que usará el motor hacia atrás:
            {"paso": n, "regla": id, "antecedentes": [...], "hecho": nuevo}
        
        """
        # Memoria de trabajo propia: copia de los hechos iniciales.
        # set() elimina duplicados y evita modificar la lista del llamador.
        
        self.memoria_trabajo = set(hechos_iniciales)

        # La traza se reinicia en CADA ejecución. Si no, la traza de un caso
        # se mezclaría con la del caso anterior (se crea una sola vez en __init__).
        self.traza_explicacion = []
 
        # Contador de pasadas completas sobre la KB (útil para la comparación
        # forward vs backward del informe).
        self.num_pasadas = 0
 
        # Aviso explícito: cargar_kb devuelve [] si el JSON falla, y sin reglas
        # todo daría False sin ninguna explicación.
        if not self.reglas:
            print("ADVERTENCIA: la Base de Conocimiento está vacía; "
                  "no se puede inferir nada.")
 
        # Caso base: si el objetivo ya es un hecho inicial, es consecuencia
        # lógica trivial. Devuelve True con la traza vacía.
        if objetivo in self.memoria_trabajo:
            return True
 
        while True:
            self.num_pasadas += 1
            agrego_hecho = False  # ¿esta pasada agregó algo nuevo?
 
            for regla in self.reglas:
                # No disparar reglas cuyo consecuente ya se conoce:
                # evita trazas repetidas y trabajo inútil.
                if regla.consecuente in self.memoria_trabajo:
                    continue
 
                # Modus Ponens: la regla se dispara solo si TODOS sus
                # antecedentes están en memoria (<= es "subconjunto" en sets).
                # Con antecedentes parciales la condición es falsa y no dispara.
                if regla.antecedentes <= self.memoria_trabajo:
                    self.memoria_trabajo.add(regla.consecuente)
                    agrego_hecho = True
 
                    # sorted(): los antecedentes son un set y su orden al
                    # imprimir no es estable. Se ordena aquí sin tocar la
                    # clase Regla (Parte 1, "no modificar").
                    self.traza_explicacion.append({
                        "paso": len(self.traza_explicacion) + 1,
                        "regla": regla.id_regla,
                        "antecedentes": sorted(regla.antecedentes),
                        "hecho": regla.consecuente,
                    })
 
                    # Parada temprana: el objetivo acaba de ser deducido.
                    if objetivo in self.memoria_trabajo:
                        return True
 
            # Punto fijo: una pasada completa sin hechos nuevos significa que
            # no se puede derivar nada más, y el objetivo no apareció.
            if not agrego_hecho:
                return False
 
    def imprimir_traza(self):
        """Imprime la traza de la última ejecución forward de forma legible."""
        if not self.traza_explicacion:
            print("  (traza vacía: no se disparó ninguna regla)")
            return
        for t in self.traza_explicacion:
            antecedentes = " AND ".join(t["antecedentes"])
            print(f"  Paso {t['paso']}: {t['regla']}: "
                  f"{antecedentes} -> {t['hecho']}")
 
    def exportar_traza(self, ruta, encabezado=""):
        """Guarda la traza de la última ejecución forward en un .txt."""
        with open(ruta, "w", encoding="utf-8") as f:
            if encabezado:
                f.write(encabezado + "\n\n")
            if not self.traza_explicacion:
                f.write("(traza vacía: no se disparó ninguna regla)\n")
            for t in self.traza_explicacion:
                antecedentes = " AND ".join(t["antecedentes"])
                f.write(f"Paso {t['paso']}: {t['regla']}: "
                        f"{antecedentes} -> {t['hecho']}\n")
 
    def ejecutar_inferencia_atras(self, hechos_iniciales, objetivo):
        """
        Motor de Encadenamiento hacia Atrás (Backward Chaining).
        Debe retornar True si el objetivo puede ser probado, False en caso contrario.
        Debe manejar adecuadamente la recursividad (goal-driven) y los casos base.
        """
 
        # TODO : implementar la lógica recursiva orientada
        # a objetivos. Pegar aquí su versión al integrar.
        
        return False # Cambiar por el resultado lógico

# ==========================================================
# PARTE 3: EJECUCIÓN (PUEDEN MODIFICAR PARA PRUEBAS)
# ==========================================================
if __name__ == "__main__":
    # 1. Inicializar el motor con el archivo de reglas
    motor = MotorInferencia("base_conocimiento.json")

    # 2. Definir caso clínico de prueba
    sintomas = ["Fiebre","Dificultad_Respiratoria", "Taquipnea",
                "Crepitantes_Pulmonares", "Tos_Productiva", "Dolor_Toracico",
                "Saturacion_Oxigeno_Baja"]
    hipotesis = "Alerta_Gravedad_Extrema"

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