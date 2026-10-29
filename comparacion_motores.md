# Comparación Forward vs Backward

KB de 50 reglas · 13 casos clínicos · tiempos: promedio de 2000 ejecuciones

## Casos clínicos

|   # | Caso                                 | Objetivo                         | Forward | Backward |
|----:|:-------------------------------------|:---------------------------------|:-------:|:--------:|
|   1 | Gripe                                | Dx_Gripe                         |   True  |   True   |
|   2 | COVID-19                             | Dx_COVID19                       |   True  |   True   |
|   3 | Neumonia con alerta                  | Alerta_Gravedad_Extrema          |   True  |   True   |
|   4 | Tuberculosis con alerta              | Alerta_Riesgo_Alto               |   True  |   True   |
|   5 | No demostrable                       | Dx_COVID19                       |  False  |  False   |
|   6 | Resfriado con alerta                 | Alerta_Complicacion_Respiratoria |   True  |   True   |
|   7 | Bronquitis con alerta                | Alerta_Progresion_Pulmonar       |   True  |   True   |
|   8 | Asma con alerta                      | Alerta_Crisis_Asmatica_Grave     |   True  |   True   |
|   9 | Neumonia: cianosis y confusion       | Alerta_Gravedad_Extrema          |   True  |   True   |
|  10 | COVID-19 con alerta                  | Alerta_Gravedad_Extrema          |   True  |   True   |
|  11 | Gripe con alerta                     | Alerta_Complicacion_Respiratoria |   True  |   True   |
|  12 | Neumonia sin dificultad respiratoria | Dx_Neumonia                      |   True  |   True   |
|  13 | Tuberculosis por deterioro general   | Dx_Tuberculosis                  |   True  |   True   |

## Motor hacia adelante (Forward)

|   # | Caso                                 | Pasadas | Reglas disparadas | Tiempo (us) |
|----:|:-------------------------------------|:-------:|:-----------------:|------------:|
|   1 | Gripe                                |    2    |         7         |        23.7 |
|   2 | COVID-19                             |    2    |         7         |        21.2 |
|   3 | Neumonia con alerta                  |    2    |         7         |        23.7 |
|   4 | Tuberculosis con alerta              |    2    |         6         |        23.2 |
|   5 | No demostrable                       |    2    |         1         |        23.0 |
|   6 | Resfriado con alerta                 |    2    |         6         |        21.2 |
|   7 | Bronquitis con alerta                |    2    |         8         |        24.6 |
|   8 | Asma con alerta                      |    2    |         6         |        20.5 |
|   9 | Neumonia: cianosis y confusion       |    2    |         7         |        18.1 |
|  10 | COVID-19 con alerta                  |    2    |         8         |        27.4 |
|  11 | Gripe con alerta                     |    2    |         8         |        31.8 |
|  12 | Neumonia sin dificultad respiratoria |    3    |         6         |        30.9 |
|  13 | Tuberculosis por deterioro general   |    3    |         5         |        21.0 |
|     | **Promedio**                         | **2.2** |      **6.3**      |    **23.9** |

## Motor hacia atrás (Backward)

|   # | Caso                                 | Llamadas | Reglas en la prueba | Profundidad máx. | Tiempo (us) |
|----:|:-------------------------------------|:--------:|:-------------------:|:----------------:|------------:|
|   1 | Gripe                                |    12    |          5          |        4         |        56.3 |
|   2 | COVID-19                             |    12    |          5          |        4         |        83.4 |
|   3 | Neumonia con alerta                  |    12    |          5          |        5         |        62.8 |
|   4 | Tuberculosis con alerta              |    11    |          5          |        5         |        61.9 |
|   5 | No demostrable                       |    3     |          0          |        2         |        38.6 |
|   6 | Resfriado con alerta                 |    17    |          5          |        5         |        89.7 |
|   7 | Bronquitis con alerta                |    10    |          5          |        5         |        62.6 |
|   8 | Asma con alerta                      |    10    |          5          |        5         |        64.1 |
|   9 | Neumonia: cianosis y confusion       |    14    |          5          |        5         |        85.6 |
|  10 | COVID-19 con alerta                  |    20    |          6          |        5         |       120.7 |
|  11 | Gripe con alerta                     |    14    |          6          |        5         |        73.0 |
|  12 | Neumonia sin dificultad respiratoria |    14    |          4          |        4         |        51.0 |
|  13 | Tuberculosis por deterioro general   |    11    |          4          |        4         |        57.5 |
|     | **Promedio**                         | **12.3** |       **4.6**       |     **4.5**      |    **69.8** |

## Resumen (promedio por caso)

| Métrica          | Forward | Backward |
|:-----------------|:-------:|:--------:|
| Reglas aplicadas |   6.3   |   4.6    |
| Tiempo (us)      |   23.9  |   69.8   |

Resultados idénticos en los 13 casos: sí.
