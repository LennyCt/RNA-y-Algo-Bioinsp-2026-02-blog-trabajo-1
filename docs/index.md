---
layout: default
title: "Trabajo 1: Optimización numérica, metaheurística y combinatoria"
subtitle: "Reporte técnico · Redes neuronales y algoritmos bioinspirados · Universidad Nacional de Colombia · 2026-02"
---

**Autores:** [PENDIENTE: nombres del equipo] · **Fecha:** 2026-10-13 · **Código:** [PENDIENTE: URL del repositorio y hash del commit de entrega]

## Introducción y objetivos

El trabajo está dividido en dos partes y consiste en usar dos ramas de la optimización como son los métodos matemáticos que usan el gradiente y los métodos bioinspirados como el Ant Colony Optimization [ACO] y el Particle Swarm Optimization [PSO], entre otros, con el fin de optimizar funciones continuas y problemas combinatorios reales; Travelling Salesman Problem [TSP].

**Parte 1 (optimización numérica).** Los objetivos son:

1. Elegir dos funciones de prueba.
2. Optimizarlas en dos y tres dimensiones con descenso por gradiente, desde condiciones iniciales aleatorias.
3. Optimizar las mismas funciones con un algoritmo evolutivo, PSO y evolución diferencial.
4. Representar con un GIF el proceso de optimización del gradiente y de al menos un método heurístico.

Además, la comparación debe ser justa: se cuentan por separado las evaluaciones de f y de ∇f, y se repiten al menos 30 corridas independientes por caso.

**Parte 2 (optimización combinatoria).** Se busca el recorrido cerrado de menor costo por las 47 capitales de provincia de la España peninsular con colonia de hormigas (ACO) y con un algoritmo genético. El costo de cada tramo combina el tiempo de viaje valorado en euros por hora, los peajes y el combustible. Se estudia a partir de qué valor de la hora cambia la ruta óptima, y se documentan las fuentes y fechas de los datos.

Las secciones siguientes presentan la fundamentación matemática, el diseño experimental y los resultados de cada parte, cómo reproducirlos, el uso de IA y los errores que se detectaron en lo que ella generó.

## Fundamentación matemática

Todos los métodos minimizan una función objetivo; las fórmulas siguientes son las que implementa el código del repositorio.

### Funciones de prueba (parte 1)

Rosenbrock tiene un valle curvo y estrecho, con mínimo global f = 0 en (1, …, 1) y dominio [-2.048, 2.048]ᵈ. Rastrigin tiene una malla regular de mínimos locales, con mínimo global f = 0 en el origen y dominio [-5.12, 5.12]ᵈ.

$$
f_{\text{Rosenbrock}}(x) = \sum_{i=1}^{d-1} \left[ 100\,(x_{i+1} - x_i^2)^2 + (1 - x_i)^2 \right]
$$

$$
f_{\text{Rastrigin}}(x) = 10\,d + \sum_{i=1}^{d} \left[ x_i^2 - 10 \cos(2\pi x_i) \right]
$$

Sus gradientes, usados por el descenso, son analíticos y se verificaron contra diferencias centrales (`python main.py check`):

$$
\frac{\partial f_{\text{Rastrigin}}}{\partial x_i} = 2 x_i + 20\pi \sin(2\pi x_i)
$$

### Conteo justo de evaluaciones

Un gradiente por diferencias centrales cuesta 2d evaluaciones de f. Aunque el código usa el gradiente analítico por velocidad, se le cobra ese costo para que la comparación con los métodos sin gradiente sea justa. Todos los métodos reciben el mismo presupuesto C:

$$
C = n_f + 2\,d\,n_{\nabla f}
$$

### Descenso por gradiente con búsqueda de Armijo

Desde un punto aleatorio uniforme x₀ en el dominio, se itera con proyección al dominio (recorte por coordenada):

$$
x_{k+1} = \Pi\left(x_k - t_k \nabla f(x_k)\right)
$$

El paso t_k parte de 1 y se reduce por un factor β = 0.5 hasta cumplir la condición de Armijo (c = 10⁻⁴, hasta 30 reducciones):

$$
f(x_{k+1}) \le f(x_k) - c\,\nabla f(x_k)^{\top} (x_k - x_{k+1})
$$

Para cuando ‖∇f‖ < 10⁻⁸, cuando no encuentra paso de descenso o cuando agota el presupuesto.

### Algoritmo genético (codificación real)

Población de 50 individuos, selección por torneo de 3, cruce BLX-α con α = 0.5 aplicado al 90 % de los pares, mutación gaussiana de desviación 0.1 del ancho del dominio con probabilidad 1/d por gen, y elitismo de 2 individuos. En BLX-α cada gen del hijo se sortea uniformemente en:

$$
\left[\min(a_j,b_j) - \alpha\,\Delta_j,\; \max(a_j,b_j) + \alpha\,\Delta_j\right], \quad \Delta_j = |a_j - b_j|
$$

### PSO

Enjambre global de 30 partículas. Cada partícula actualiza su velocidad con su mejor posición personal p y la mejor del enjambre g, con r₁, r₂ uniformes en [0, 1] y la velocidad acotada a 0.2 veces el ancho del dominio:

$$
v \leftarrow w\,v + c_1 r_1 (p - x) + c_2 r_2 (g - x), \qquad x \leftarrow x + v
$$

Se usan w = 0.729 y c₁ = c₂ = 1.49445, los valores de constricción habituales.

### Evolución diferencial DE/rand/1/bin

Población de 40, F = 0.5 y CR = 0.9. Para cada individuo x_i se eligen tres distintos r₁, r₂, r₃, distintos de i, y se forma el vector mutante; el cruce binomial mezcla mutante y padre (con al menos un gen del mutante) y el hijo u reemplaza al padre si no es peor:

$$
v = x_{r_1} + F\,(x_{r_2} - x_{r_3}), \qquad x_i \leftarrow u \ \text{ si } f(u) \le f(x_i)
$$

### Problema del viajante con costo monetario (parte 2)

Se busca la permutación π de las 47 ciudades que minimiza el costo del circuito cerrado. El costo del tramo i → j no es simétrico, porque el tiempo y los peajes dependen del sentido:

$$
c_{ij}(h) = h\,t_{ij} + p_{ij} + d_{ij}\,\frac{l}{100}\,\pi_{\text{comb}}, \qquad C(\pi, h) = \sum_{k} c_{\pi_k \pi_{k+1}}(h)
$$

donde h es el valor de la hora (EUR/h), t_ij el tiempo (h), p_ij el peaje (EUR), d_ij la distancia (km), l el consumo (L/100 km) y π_comb el precio del combustible (EUR/L).

**Cambio de ruta con h.** Para una ruta fija, el costo es lineal en h: C(h) = h·T + M, con T el tiempo total y M = peajes + combustible. El mínimo de varias rectas es una función cóncava lineal por tramos, y dos rutas a y b se cruzan en:

$$
h^{*} = \frac{M_b - M_a}{T_a - T_b}
$$

Por eso el barrido calcula la envolvente inferior de todas las rutas encontradas: sus vértices son los valores de h donde cambia la mejor ruta conocida. Como los heurísticos no garantizan optimalidad, esos valores son una cota superior de los cambios reales.

### Colonia de hormigas (ACO)

Cada hormiga, partiendo de la ciudad inicial, elige la siguiente ciudad j no visitada con probabilidad proporcional a la feromona τ y la visibilidad η = 1/c:

$$
P_{ij} = \frac{\tau_{ij}^{\alpha}\, \eta_{ij}^{\beta}}{\sum_{k \in \text{no visitadas}} \tau_{ik}^{\alpha}\, \eta_{ik}^{\beta}}, \qquad \eta_{ij} = \frac{1}{c_{ij}}
$$

Tras cada iteración la feromona se evapora y todas las hormigas depositan en las aristas de su ruta, en proporción inversa al costo L_k de esa ruta:

$$
\tau_{ij} \leftarrow (1 - \rho)\,\tau_{ij} + \sum_{k} \frac{Q}{L_k}\,[\,(i,j) \in \text{ruta}_k\,]
$$

Se usan α = 1, β = 3, ρ = 0.35 y Q = 1. Como opción, `min_pheromone_fraction` fija una cota inferior a la feromona (idea del MAX-MIN Ant System) para evitar el estancamiento descrito en la sección de la cacería de la alucinación.

### Algoritmo genético para el TSP

Cada individuo es una permutación con la ciudad inicial fija. Se usan selección por torneo, cruce por orden (OX), mutación por intercambio de dos ciudades y elitismo. Con 200 individuos, 400 generaciones, cruce 0.9 y mutación 0.15 en la configuración de ejemplo; esos valores no están ajustados.

## Parte 1: diseño experimental

Se comparan cuatro métodos sobre dos funciones en 2 y 3 dimensiones, es decir, 16 combinaciones con 30 corridas independientes cada una (480 corridas).

- **Funciones.** Rosenbrock (valle estrecho, mal condicionada) y Rastrigin (muchos mínimos locales). Son complementarias: la primera pone a prueba la velocidad en un valle casi plano, la segunda la capacidad de escapar de mínimos locales.
- **Presupuesto.** 5000·d evaluaciones equivalentes: 10 000 en 2D y 15 000 en 3D, con la equivalencia C = n_f + 2·d·n_∇f de la fundamentación.
- **Condición inicial y semillas.** Punto o población inicial uniforme en el dominio. La corrida i usa la semilla 12345 + i, igual para todos los métodos, de modo que cualquier resultado se puede reproducir.
- **Éxito.** Una corrida tiene éxito si termina con f < 10⁻³. Se reportan media, desviación estándar, mejor, peor, tasa de éxito y evaluaciones consumidas.
- **Hiperparámetros.** Son valores estándar de la literatura y no se ajustaron para estas funciones; se listan abajo para que la comparación se pueda repetir.

| Método | Hiperparámetros |
| --- | --- |
| Descenso por gradiente | paso inicial 1, Armijo c = 10⁻⁴, β = 0.5, hasta 30 reducciones, ‖∇f‖ < 10⁻⁸ |
| Algoritmo genético | población 50, torneo 3, BLX-α con α = 0.5, cruce 0.9, mutación gaussiana 0.1 del dominio con prob. 1/d, elitismo 2 |
| PSO | 30 partículas, w = 0.729, c₁ = c₂ = 1.49445, velocidad máxima 0.2 del dominio |
| Evolución diferencial | DE/rand/1/bin, población 40, F = 0.5, CR = 0.9 |

Los métodos poblacionales dejan de evaluar cuando una generación completa ya no cabe en el presupuesto, por eso PSO usa 9990 y no 10 000 evaluaciones en 2D.

## Parte 1: resultados

El descenso por gradiente tuvo la peor media en las cuatro combinaciones y 0 % de éxito en Rosenbrock 3D con el presupuesto común. La Tabla 1 resume las 30 corridas de cada caso (umbral de éxito f < 10⁻³; costo medio en evaluaciones equivalentes).

**Tabla 1.** Valor final de f en 30 corridas, por función, dimensión y método.

| Función | d | Método | Media | Desv. est. | Mejor | Peor | Éxito (%) | Costo medio |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Rosenbrock | 2 | Gradiente | 5.8×10⁻² | 5.9×10⁻² | 4.3×10⁻⁵ | 1.3×10⁻¹ | 23 | 10008 |
| Rosenbrock | 2 | AG | 5.2×10⁻⁵ | 5.5×10⁻⁵ | 5.7×10⁻⁷ | 2.2×10⁻⁴ | 100 | 10000 |
| Rosenbrock | 2 | PSO | 2.2×10⁻¹¹ | 1.0×10⁻¹⁰ | 9.0×10⁻²⁰ | 5.6×10⁻¹⁰ | 100 | 9990 |
| Rosenbrock | 2 | DE | 0 | 0 | 0 | 0 | 100 | 10000 |
| Rosenbrock | 3 | Gradiente | 3.1×10⁻¹ | 8.9×10⁻¹ | 6.6×10⁻³ | 4.0×10⁰ | 0 | 15008 |
| Rosenbrock | 3 | AG | 1.9×10⁻² | 2.6×10⁻² | 1.2×10⁻⁴ | 1.2×10⁻¹ | 13 | 15000 |
| Rosenbrock | 3 | PSO | 8.0×10⁻⁴ | 6.0×10⁻⁴ | 3.2×10⁻⁵ | 2.2×10⁻³ | 70 | 15000 |
| Rosenbrock | 3 | DE | 2.6×10⁻² | 6.5×10⁻² | 0 | 2.8×10⁻¹ | 70 | 15000 |
| Rastrigin | 2 | Gradiente | 9.2×10⁰ | 8.5×10⁰ | 0 | 2.9×10¹ | 20 | 3099 |
| Rastrigin | 2 | AG | 1.0×10⁻³ | 1.1×10⁻³ | 1.8×10⁻⁶ | 3.9×10⁻³ | 67 | 10000 |
| Rastrigin | 2 | PSO | 3.3×10⁻² | 1.8×10⁻¹ | 0 | 9.9×10⁻¹ | 97 | 9990 |
| Rastrigin | 2 | DE | 0 | 0 | 0 | 0 | 100 | 10000 |
| Rastrigin | 3 | Gradiente | 1.7×10¹ | 1.1×10¹ | 0 | 4.2×10¹ | 13 | 4699 |
| Rastrigin | 3 | AG | 4.4×10⁻³ | 6.3×10⁻³ | 1.5×10⁻⁴ | 3.0×10⁻² | 27 | 15000 |
| Rastrigin | 3 | PSO | 9.9×10⁻² | 3.0×10⁻¹ | 0 | 9.9×10⁻¹ | 90 | 15000 |
| Rastrigin | 3 | DE | 0 | 0 | 0 | 0 | 100 | 15000 |

La Figura 1 y la Figura 2 muestran la mediana del mejor f hallado a lo largo del presupuesto. Donde la curva llega a 10⁻¹⁶ es porque f = 0 exacto, que la escala logarítmica no puede dibujar.

![Convergencia en Rosenbrock 2D]({{ '/assets/img/convergencia_rosenbrock_2d.png' | relative_url }})

**Figura 1a.** Rosenbrock 2D: mediana de 30 corridas.

![Convergencia en Rosenbrock 3D]({{ '/assets/img/convergencia_rosenbrock_3d.png' | relative_url }})

**Figura 1b.** Rosenbrock 3D: mediana de 30 corridas.

![Convergencia en Rastrigin 2D]({{ '/assets/img/convergencia_rastrigin_2d.png' | relative_url }})

**Figura 2a.** Rastrigin 2D: mediana de 30 corridas.

![Convergencia en Rastrigin 3D]({{ '/assets/img/convergencia_rastrigin_3d.png' | relative_url }})

**Figura 2b.** Rastrigin 3D: mediana de 30 corridas.

**Sensibilidad al presupuesto del gradiente.** En Rosenbrock el gradiente no se quedó atascado, solo no alcanzó a converger: con 100 000·d evaluaciones (20 veces más) llegó al umbral en las 30 corridas, con f media de 3.1×10⁻¹² en 2D y 1.1×10⁻¹⁵ en 3D. En Rastrigin, en cambio, terminó por sí mismo con 3099 (2D) y 4699 (3D) evaluaciones: llegó a un mínimo local donde ‖∇f‖ < 10⁻⁸ y más presupuesto no lo habría cambiado.

### Animaciones

Tres GIF de una corrida en 2D con semilla 3. Los GIF solo existen en 2D porque con tres variables no se puede dibujar la superficie. Se regeneran con `python main.py animate`.

![Descenso por gradiente en Rosenbrock]({{ '/assets/gif/rosenbrock_gd_s3.gif' | relative_url }})

**Animación 1.** Descenso por gradiente en Rosenbrock: terminó en f = 0.125 sin converger.

![PSO en Rastrigin]({{ '/assets/gif/rastrigin_pso_s3.gif' | relative_url }})

**Animación 2.** PSO en Rastrigin: terminó en f = 0.

![Evolución diferencial en Rosenbrock]({{ '/assets/gif/rosenbrock_de_s3.gif' | relative_url }})

**Animación 3.** Evolución diferencial en Rosenbrock: terminó en f = 0.

## Parte 1: discusión

Las dos funciones fallan al gradiente por razones distintas, y esa diferencia es la que explica el orden de los métodos. Lo que sigue son interpretaciones consistentes con los datos de la Tabla 1, no hipótesis comprobadas con experimentos adicionales, salvo la del presupuesto, que sí se probó.

**Rosenbrock: un problema de velocidad.** Su valle es curvo y estrecho, así que el gradiente apunta casi perpendicular al valle y la búsqueda de Armijo acepta pasos muy cortos a lo largo de él. Con 10 000 evaluaciones el gradiente seguía lejos del mínimo (mediana cerca de 10⁻² en la Figura 1a), pero con 20 veces más presupuesto convergió siempre: no hay mínimos locales que lo atrapen. DE y PSO bajaron varios órdenes de magnitud más rápido. Una explicación habitual para DE es que sus vectores de diferencia entre individuos se alinean con la dirección del valle y adaptan solos la escala del paso; este trabajo no lo midió.

**Rosenbrock 3D es más difícil con solo 1.5 veces más presupuesto.** El éxito bajó de 100 % a 13 % en el AG y de 100 % a 70 % en PSO y DE. La DE tiene un resultado bimodal: llega a f = 0 exacto en 19 de 30 corridas y en 9 se estanca entre 0.014 y 0.28, por eso su media (2.6×10⁻²) es peor que la de PSO (8.0×10⁻⁴) pese a tener la misma tasa de éxito. Con 30 corridas no se hicieron pruebas de significancia, así que no se afirma que PSO supere a DE en este caso.

**Rastrigin: un problema de mínimos locales.** Tiene cerca de 11ᵈ mínimos locales en el dominio (uno por entero en cada eje, de -5 a 5). El gradiente terminó por sí solo, con 3099 y 4699 evaluaciones, al llegar a uno de ellos; su éxito (20 % en 2D, 13 % en 3D) es la fracción de corridas que cayó en la cuenca del mínimo global. Es mayor que la fracción 1/11ᵈ que daría un descenso puramente local (1/121 y 1/1331), lo que sugiere que los primeros pasos, de longitud 1 y recortados al dominio, saltan entre cuencas; no se verificó. Los métodos poblacionales exploran muchas cuencas a la vez: DE no falló en ninguna corrida, PSO falló en 1 de 30 (2D) y 3 de 30 (3D) con f ≈ 0.995, que es el mínimo local vecino al origen, es decir, convergencia prematura del enjambre.

**El AG quedaba corto en precisión.** Sus curvas medianas se aplanan entre 10⁻³ y 10⁻⁵, y su desviación de mutación fija (0.1 del dominio) es una causa plausible, porque no se reduce al acercarse al óptimo. Ajustar esa desviación o hacerla decrecer es el primer cambio a probar.

**Alcance de las conclusiones.** Los resultados valen para estos dos problemas, este presupuesto, estos hiperparámetros sin ajustar y este umbral de éxito, que es arbitrario. No hay una comparación estadística formal. Dentro de ese alcance, DE fue el método más robusto, PSO el segundo y el gradiente el más dependiente de la forma de la función: bueno cuando no hay mínimos locales y presupuesto suficiente, malo en caso contrario.

## Parte 2: datos y metodología

El código de la parte 2 está completo, pero ninguno de sus datos de entrada está todavía verificado, así que esta sección describe el método y deja marcado, dato por dato, qué falta. Cada dato debe quedar con su fuente y su fecha de consulta (`data/sources.md`).

**Instancia.** 47 capitales de provincia de la España peninsular: las 50 provincias menos Palma, Las Palmas de Gran Canaria y Santa Cruz de Tenerife. Ceuta y Melilla no son capitales de provincia.

**Costo por tramo.** Para ir de i a j se suman tres componentes, todos en euros:

- **Tiempo:** valor de la hora × horas de viaje.
- **Peajes:** importe del trayecto para un turismo de clase 1.
- **Combustible:** kilómetros × consumo (L/100 km) / 100 × precio del litro.

Las matrices de distancia y tiempo se obtienen una sola vez de la API Table de OSRM, que devuelve la ruta más rápida según el perfil, no necesariamente la más corta ni la de menor costo; por eso la matriz puede ser asimétrica. Una vez guardadas en `data/`, la ejecución no depende de Internet.

**Estado de cada dato.**

| Dato | Fuente prevista | Estado |
| --- | --- | --- |
| Coordenadas de las 47 capitales | Fuente primaria (IGN, INE o ayuntamientos) | Las escribió la IA de memoria; solo pasan un control de cordura (rangos y 4 distancias desde Madrid con ±5 %) |
| Distancias y tiempos | OSRM, API Table, perfil `driving` | Obtenido a partir de OSRM |
| Peajes (2162 pares dirigidos) | Tarifas oficiales de cada concesionaria, clase 1 | **Pendiente:**  |
| Vehículo y consumo | Ficha técnica del fabricante u homologación | Completo, vehiculo elegido Dacian Sanndero |
| Precio del combustible | Fuente oficial con fecha | Fuente en experimet.json |

**Método para los peajes: decisión pendiente del equipo.** Identificar los tramos de peaje de cada itinerario y sumar las tarifas oficiales exige decidir cuánto del trabajo se hace a mano y cuánto se aproxima. Se exploró detectar los tramos automáticamente con OSRM y OpenStreetMap, pero esa vía se descartó y su código se retiró del repositorio (ver la cacería de la alucinación). Cualquier método que se adopte debe declarar si el importe es oficial o una estimación.

**Algoritmos y parámetros.** ACO y AG descritos en la fundamentación. Con 3 corridas, ACO de 150 iteraciones y AG de 200 individuos × 400 generaciones, la configuración de ejemplo dura cerca de un minuto; son valores de demostración, no ajustados, y hay que justificar los definitivos. La semilla base es 42 y la corrida i usa 42 + i.

**Barrido del valor de la hora.** Para h en una malla (por defecto 0, 10, 20, 40, 80, 160 EUR/h) se ejecutan los algoritmos, se reúnen todas las rutas halladas y se calcula la envolvente inferior de sus rectas C(h) = h·T + M. Los vértices son los valores de h donde cambia la mejor ruta conocida.

## Parte 2: resultados

**[PENDIENTE: no hay resultados citables hasta cargar los datos reales.]** El código se probó solo con datos sintéticos inventados (`python main.py run --demo`), que no se pueden citar. Cuando existan los datos reales, esta sección debe contener lo siguiente, que `main.py run` y `main.py sweep` ya producen:

- **Comparación ACO y AG:** tabla con mejor, media, desviación, peor costo y segundos por algoritmo (`results/comparison.csv`), con el número de corridas y la semilla base 42.
- **Mejor ruta:** el orden de las 47 capitales y el desglose en tiempo, peajes y combustible (`best_route.json`), con el mapa (`best_route.png`) y el GIF de su evolución (`evolution.gif`).
- **Barrido del valor de la hora:** los valores de h en que cambia la mejor ruta conocida (`hourly_sweep_envelope.csv`) y la figura `hourly_sweep.png`. Esos cambios son una cota superior de los cambios reales, porque los heurísticos no garantizan optimalidad; la columna `gap_vs_best_known_eur` mide cuánto se alejó cada corrida de la mejor ruta conocida.
- **Análisis:** cuál algoritmo es mejor y con qué parámetros, qué parte del costo pesa más y qué cambia en la ruta cuando sube h (más autopistas de peaje, menos tiempo).

**Observación preliminar con datos sintéticos (no citable).** Con los parámetros de ejemplo, el ACO obtuvo costos menores que el AG (alrededor de 2314 frente a 2630 en la instancia sintética), lo que indica que el AG necesita ajuste de población, generaciones y operadores antes de la comparación definitiva.

## Reproducibilidad

Todo el trabajo se regenera desde un repositorio con un solo entorno para las dos partes. **[PENDIENTE: URL del repositorio y hash del commit de entrega; probar un clon limpio en otra máquina.]**

- **Entorno:** Python 3.11 o superior (probado con 3.13/3.14) y `requirements.txt` con versiones fijas: numpy 2.5.3, pandas 3.0.5, matplotlib 3.11.2, pillow 12.3.0 y requests 2.34.2. Las versiones instaladas coinciden con las fijadas; la instalación con `pip install -r requirements.txt` todavía no se probó en una máquina limpia.
- **Semillas:** parte 1, base 12345; parte 2, base 42; la corrida i usa base + i. Mismas semillas, mismos resultados (hay una prueba para la parte 2 y el resultado de la parte 1 no cambió entre versiones de las bibliotecas).
- **Parámetros:** se cambian por línea de comandos o por un JSON, sin editar el código (`--param método.nombre=valor`).
- **Datos:** una vez generados los CSV de `parte2_tsp/data/`, la ejecución no usa Internet.

Comandos, ejecutados desde la carpeta de cada parte:

```bash
# Parte 1
cd parte1_numerica
python main.py check                 # gradientes analíticos vs. diferencias finitas
python main.py compare               # 30 corridas, 4 métodos, 2 funciones, 2D y 3D (~17 s)
python main.py curves                # PNG de convergencia
python main.py animate --method pso --function rastrigin --seed 3   # GIF (~25 s)

# Parte 2
cd ../parte2_tsp
python build_data.py                 # matrices de OSRM (una vez, con Internet)
python main.py validate
python main.py run
python main.py sweep --hourly-values 0 10 20 40 80 160
python -m unittest discover -s tests # 35 pruebas (~4 s)
```

## Uso de inteligencia artificial

| Tarea | Qué produjo la IA | Cómo se verificó |
| --- | --- | --- |
| Construir README.md y main.py a partir de los archivos pasados | Archivo README.md de la raiz y main.py de optimizacio heuristica | Se verifico que fuera funcional y legible ejecutandolo en un repo clonado nuevo y se verificaron cada uno de los comandos |
| Implementar los tests de los algoritmos y corregir test de la matriz | test_aco.py, test_genetic_algorithm y test_cost__matrix.py corregido | Se usaron los tests con datos sinteticos |
| Completar y corregir comentarios | La gran parte de comentarios | Se verificaron la mayoria de comentarios |
| Generar archivos complementarios de la parte 2 | build_data.py (a partir de OSRM), main.py, tsp_data.py, sources.md, requirements.txt y README.md | Se verificaron los datos extraidos |
| Generar reporte en markdown a partir de documento y complementos | Produjo la gran mayoria del texto de este documento | Se valido en la pagina del blog |


## Cacería de la alucinación

Se registran los errores y suposiciones falsas del asistente que se detectaron al ejecutar y probar el código. 

| # | Qué afirmó o hizo la IA | Cómo se detectó | Corrección |
| --- | --- | --- | --- |
| 1 | El ACO con los parámetros por defecto encuentra buenas rutas | Una prueba con 7 ciudades y óptimo conocido por fuerza bruta: 0 de 10 semillas lo alcanzaron, y el resultado era idéntico con 80, 500 o 2000 iteraciones. Con 47 ciudades, 150 y 450 iteraciones dieron los mismos costos | Estancamiento de la feromona: sin cota inferior, las aristas no usadas bajan a ~10⁻¹⁷, por debajo del piso de 10⁻¹² del código, y quedan unas 10⁹ veces menos probables. Se añadió `min_pheromone_fraction` (cota estilo MAX-MIN); con 0.1 alcanza el óptimo en 8 de 10 semillas en 7 ciudades, pero con 47 ciudades empeoró con 150 iteraciones y mejoró solo 0.3 % con 0.01 y 450 iteraciones. Hay que ajustarlo con datos reales |
| 2 | Para ver si cambia la ruta con el valor de la hora, bastaba comparar la ruta final de cada h | Con datos sintéticos, el AG dio rutas más lentas al subir h, algo imposible para un óptimo: el ruido del heurístico se confundía con cambios reales | Se reemplazó por la envolvente inferior de las rectas C(h) = h·T + M de todas las rutas halladas |
| 3 | Las columnas `ciudad/lon/lat` y `ruta/costo` del script de visualización original eran compatibles con el resto | El script de datos usaba `city/longitude/latitude` y los algoritmos devuelven `route/cost/generation` | Se unificaron los nombres en la versión en inglés |
| 4 | OSRM público expone la clase `toll` en sus rutas, así que detectar peajes era leer ese campo | El equipo ejecutó la detección y el servidor no devolvió ninguna clase; la salvaguarda del código se negó a seguir en vez de marcar toda ruta como gratuita | Se probó una segunda versión (cruzar la geometría de la ruta con las vías de OpenStreetMap); tampoco se pudo descargar la geometría (504 de Overpass). Se retiró todo el codigo |
| 5 | Un cambio de nombres de módulos y variables en la parte 1 no afectaba al resultado | Colisiones de nombres de módulos (`functions`) y claves de diccionario que también se habían renombrado | Se corrigieron las importaciones y se comprobó que los resultados eran idénticos|

Los puntos 1 y 2 son errores de diseño que solo aparecieron al ejecutar; los puntos 4 y 7 son datos que el asistente produjo sin fuente, que es la forma más directa de alucinación en este trabajo.

## Referencias

- Armijo, L. (1966). Minimization of functions having Lipschitz continuous first partial derivatives. *Pacific Journal of Mathematics, 16*(1), 1–3.
- Clerc, M., & Kennedy, J. (2002). The particle swarm: Explosion, stability, and convergence in a multidimensional complex space. *IEEE Transactions on Evolutionary Computation, 6*(1), 58–73.
- Davis, L. (1985). Applying adaptive algorithms to epistatic domains. En *Proceedings of the 9th International Joint Conference on Artificial Intelligence* (Vol. 1, pp. 162–164).
- Dorigo, M., Maniezzo, V., & Colorni, A. (1996). Ant system: Optimization by a colony of cooperating agents. *IEEE Transactions on Systems, Man, and Cybernetics, Part B, 26*(1), 29–41.
- Eshelman, L. J., & Schaffer, J. D. (1993). Real-coded genetic algorithms and interval-schemata. En L. D. Whitley (Ed.), *Foundations of genetic algorithms 2* (pp. 187–202). Morgan Kaufmann.
- Holland, J. H. (1975). *Adaptation in natural and artificial systems*. University of Michigan Press.
- Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. En *Proceedings of ICNN'95: International Conference on Neural Networks* (Vol. 4, pp. 1942–1948). IEEE.
- Luxen, D., & Vetter, C. (2011). Real-time routing with OpenStreetMap data. En *Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems* (pp. 513–516). ACM.
- Nocedal, J., & Wright, S. J. (2006). *Numerical optimization* (2.ª ed.). Springer.
- Project OSRM. (s. f.). *OSRM API documentation*. https://project-osrm.org/docs/v5.24.0/api/.
- Rosenbrock, H. H. (1960). An automatic method for finding the greatest or least value of a function. *The Computer Journal, 3*(3).
- Storn, R., & Price, K. (1997). Differential evolution: A simple and efficient heuristic for global optimization over continuous spaces. *Journal of Global Optimization, 11*(4).
- Stützle, T., & Hoos, H. H. (2000). MAX–MIN ant system. *Future Generation Computer Systems, 16*(8).
- Törn, A., & Žilinskas, A. (1989). *Global optimization* (Lecture Notes in Computer Science, Vol. 350).
