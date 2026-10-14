---
layout: default
title: "Trabajo 1: Optimización numérica, metaheurística y combinatoria"
subtitle: "Reporte técnico · Redes neuronales y algoritmos bioinspirados · Universidad Nacional de Colombia · 2026-02"
---

**Autores:** Lenny Alejandro Carvajal Taborda, Diego Fernando Juajibioy Chavez · **Fecha:** 2026-10-13 · **Código:** https://github.com/LennyCt/RNA-y-Algo-Bioinsp_Trabajo1.git

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

Se busca la permutación π de las 47 ciudades que minimiza el costo del circuito cerrado. En general el costo del tramo i → j puede depender del sentido; con los datos usados (promedio de las rutas de ida y de vuelta) la matriz resulta simétrica:

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

Todos los datos se consultaron el 13 de octubre de 2026 y están guardados en el repositorio (`data/`), así que la ejecución no usa Internet. Las fuentes, fechas y limitaciones de cada dato están en `sources.md` y en `data/valhalla/FUENTES.md`.

**Instancia.** 47 capitales de provincia de la España peninsular: las 50 provincias menos Palma, Las Palmas de Gran Canaria y Santa Cruz de Tenerife. Ceuta y Melilla no son capitales de provincia. Las coordenadas se tomaron de Wikidata (propiedad P625), y el identificador de cada ciudad queda en `data/cities.csv` para que se pueda verificar.

**Costo por tramo.** Para ir de i a j se suman tres componentes, todos en euros:

- **Tiempo:** valor de la hora × horas de viaje.
- **Peajes:** importe del trayecto para un vehículo ligero, sin descuentos.
- **Combustible:** kilómetros × consumo (L/100 km) / 100 × precio del litro.

**Distancias y tiempos.** Se calcularon con Valhalla 3.9.1, un motor de rutas de código abierto sobre OpenStreetMap, en el servidor público de FOSSGIS. Para cada par se usa la ruta más rápida con peajes permitidos, calculada en los dos sentidos y promediada; por eso la matriz es simétrica. La mediana de los tramos es de 536 km y 5.2 h, y el más largo mide 1247 km. La misma ruta se usa para el tiempo, la distancia y los peajes, de modo que el costo de cada tramo corresponde a un único viaje real.

La primera versión del código usaba OSRM (API Table). Al comparar ambas fuentes, la diferencia relativa de distancia tiene mediana 1.7 %, percentil 95 de 16.5 % y máximo de 50 %. Medir los peajes sobre una ruta y tomar el tiempo de otra habría dado costos que no corresponden a ningún viaje, así que se descartó mezclarlas. Los datos de OSRM se conservan en `data/osrm/` solo para comparar.

**Peajes.** Se identificaron las autopistas de peaje que recorre cada ruta midiendo, arista por arista, los kilómetros sobre vías marcadas `toll=yes` en OpenStreetMap. Cada vía se asignó a su grupo tarifario y se calculó una tarifa por kilómetro a partir del peaje oficial de 2026 de un recorrido de referencia, medido con el mismo motor de rutas:

$$
\text{tarifa}_a = \frac{\text{peaje oficial del recorrido de referencia}}{\text{km de ese recorrido}}, \qquad p_{ij} = \sum_{a} \text{km}_{ij,a}\,\text{tarifa}_a + \text{cuotas fijas}
$$

La Tabla 2 muestra las tarifas resultantes. Los túneles de Artxanda tienen cuota fija: 1.55 EUR por paso.

**Tabla 2.** Tarifas por kilómetro de las autopistas de peaje que usan las rutas, vehículo ligero, 2026. Fuente: PDF de tarifas del Ministerio de Transportes y Movilidad Sostenible, SEITT, Bidegi, Interbiak y Audenasa (URL por fila en `data/valhalla/peajes_2026.csv`).

| Autopista | Peaje de referencia (EUR) | km de referencia | EUR/km |
| --- | --- | --- | --- |
| AP-6 Villalba – Adanero | 15.70 | 57.46 | 0.273 |
| AP-51 Villacastín – Ávila | 1.75 | 23.46 | 0.075 |
| AP-61 San Rafael – Segovia | 3.05 | 25.59 | 0.119 |
| AP-9 A Coruña – Pontevedra | 16.35 | 111.60 | 0.147 |
| AP-53 Santiago – Alto de Santo Domingo | 7.25 | 40.36 | 0.180 |
| AP-66 Campomanes – León | 16.20 | 77.20 | 0.210 |
| AP-71 León – Astorga | 6.20 | 35.03 | 0.177 |
| AP-68 Bilbao – Zaragoza | 39.90 | 291.10 | 0.137 |
| AP-15 Pamplona – Tudela | 11.40 | 69.52 | 0.164 |
| AP-8/AP-1 Bilbao – Donostia | 13.81 | 75.96 | 0.182 |
| R-2 | 5.20 | 57.09 | 0.091 |
| R-3 | 3.40 | 25.35 | 0.134 |
| R-4 | 6.15 | 51.01 | 0.121 |
| R-5 | 3.65 | 20.53 | 0.178 |
| AP-36 Corral de Almaguer – San Clemente | 14.15 | 118.69 | 0.119 |
| AP-7 Málaga – Guadiaro | 12.00 | 71.45 | 0.168 |
| C-32 Garraf y Cubelles | 13.45 | 32.73 | 0.411 |

De los 1081 pares de ciudades, 607 (1214 pares dirigidos) pasan por al menos una autopista de peaje. El peaje medio de esos tramos es de 17.09 EUR, y el máximo es de 52.20 EUR (Albacete – Oviedo).

Por ejemplo, de A Coruña a Albacete la ruta recorre 118.69 km de AP-36, 56.41 km de AP-6 y 50.69 km de R-4, y el peaje suma 14.15 + 15.41 + 6.11 = 35.67 EUR.

**Vehículo y combustible.** Dacia Sandero TCe 90 de gasolina (67 kW), con consumo WLTP combinado de 5.3 L/100 km (ADAC Autokatalog). El precio de la gasolina 95 E5 es de 1.7961 EUR/L: la media simple de 10 238 estaciones de la España peninsular, según el Geoportal de Gasolineras del MITECO, con dato del 13/10/2026 a las 22:02.

**Estado de cada dato.**

| Dato | Fuente | Estado |
| --- | --- | --- |
| Coordenadas de las 47 capitales | Wikidata (P625) | Verificado; la versión anterior, escrita de memoria por la IA, difería como máximo 1.6 km |
| Distancias y tiempos | Valhalla 3.9.1 sobre OpenStreetMap (FOSSGIS) | Completo, 1081 pares |
| Peajes | Tarifas oficiales 2026 prorrateadas por km sobre la ruta de Valhalla | Completo, 2162 pares dirigidos; es una estimación, ver limitaciones |
| Vehículo y consumo | ADAC Autokatalog | Completo |
| Precio del combustible | Geoportal de Gasolineras (MITECO), 13/10/2026 | Completo |

**Limitaciones de los peajes.**

- Prorratear por kilómetro es una aproximación: en la realidad se paga por tramo o por caseta.
- Se supone el mismo peaje en los dos sentidos.
- No se modelan descuentos por recurrencia ni tarifas nocturnas.
- La concesión de la AP-68 termina el 10/11/2026; después de esa fecha su peaje es 0.
- Hay tres tarifas con reservas:
  - AP-15: la columna de la tabla de Audenasa se interpretó como vehículos ligeros.
  - C-32: tarifa de una fuente secundaria.
  - R-4 y AP-36: el PDF se titula 2026 pero dice "en vigor desde el 1 de enero de 2025".

**Algoritmos y parámetros.** ACO y AG como se describen en la fundamentación, con la configuración de `config/experiment.json`:

- ACO: 47 hormigas, 150 iteraciones, α = 1, β = 3, ρ = 0.35.
- AG: 200 individuos, 400 generaciones, cruce 0.9, mutación 0.15.

Se hicieron 10 corridas por algoritmo con valor de la hora h = 20 EUR/h. La semilla base es 42 y la corrida i usa 42 + i.

**Barrido del valor de la hora.** Para h = 0, 10, 20, 40, 80 y 160 EUR/h se ejecutaron 3 corridas de ACO, se reunieron todas las rutas halladas y se calculó la envolvente inferior de sus rectas C(h) = h·T + M.

## Parte 2: resultados

El ACO encontró la ruta más barata y fue mucho más estable que el AG. La Tabla 3 resume las 10 corridas de cada algoritmo con h = 20 EUR/h.

**Tabla 3.** Costo total del recorrido (EUR) en 10 corridas por algoritmo, h = 20 EUR/h, semillas 42 a 51.

| Algoritmo | Mejor | Media | Desv. est. | Peor | Segundos por corrida |
| --- | --- | --- | --- | --- | --- |
| ACO | 2308.61 | 2401.35 | 35.26 | 2433.26 | 17.3 |
| AG | 2465.36 | 2845.44 | 172.54 | 3092.52 | 10.4 |

La mejor ruta del ACO (semilla 44) recorre 6941 km en 79.3 h. Su costo se reparte así:

- tiempo: 1586.12 EUR (68.7 %);
- combustible: 660.74 EUR (28.6 %);
- peajes: 61.74 EUR (2.7 %).

La mejor del AG (semilla 43) es 157 EUR más cara: recorre 587 km más y tarda 5.2 h más.

**Mejor recorrido (ACO):** A Coruña → Lugo → Ourense → Pontevedra → Oviedo → Santander → Bilbao → Vitoria-Gasteiz → San Sebastián → Pamplona → Logroño → Soria → Guadalajara → Madrid → Toledo → Ciudad Real → Albacete → Cuenca → Teruel → Zaragoza → Huesca → Lleida → Tarragona → Barcelona → Girona → Castellón de la Plana → Valencia → Alicante → Murcia → Almería → Málaga → Granada → Jaén → Córdoba → Sevilla → Huelva → Cádiz → Badajoz → Cáceres → Salamanca → Ávila → Segovia → Zamora → Valladolid → Palencia → Burgos → León → A Coruña.

![Mejor ruta ACO]({{ '/assets/img/tsp_mejor_ruta_aco.png' | relative_url }})

**Figura 3.** Mejor recorrido del ACO sobre las provincias peninsulares (h = 20 EUR/h, semilla 44). Fuente: elaboración propia; polígonos de provincias de click_that_hood (Code for America).

![Mejor ruta AG]({{ '/assets/img/tsp_mejor_ruta_ag.png' | relative_url }})

**Figura 4.** Mejor recorrido del AG (h = 20 EUR/h, semilla 43). Fuente: elaboración propia.

![Evolución del ACO]({{ '/assets/gif/tsp_aco_evolucion.gif' | relative_url }})

**Animación 4.** Evolución de la mejor ruta del ACO a lo largo de las iteraciones. Se regenera con `python main.py run`.

**Barrido del valor de la hora.** Las 18 rutas distintas que se encontraron en el barrido forman una envolvente inferior de solo dos tramos (Tabla 4 y Figura 5). La mejor ruta conocida cambia una sola vez, en h ≈ 8.56 EUR/h:

- **Por debajo de ese valor** conviene una ruta 1.3 h más lenta pero 71 km más corta y con 17.76 EUR menos de peajes.
- **Por encima** conviene la ruta más rápida, que es la de la Figura 3.

**Tabla 4.** Envolvente inferior del barrido del valor de la hora (ACO, 3 corridas por valor). Fuente: `results/hourly_sweep_envelope.csv`.

| Intervalo de h (EUR/h) | Horas | km | Peajes (EUR) | Hallada en |
| --- | --- | --- | --- | --- |
| [0, 8.56) | 80.59 | 7012 | 43.98 | h = 160 |
| [8.56, ∞) | 79.31 | 6941 | 61.74 | h = 20 |

![Barrido del valor de la hora]({{ '/assets/img/tsp_barrido_valor_hora.png' | relative_url }})

**Figura 5.** Horas totales y gasto en peajes más combustible de la mejor corrida para cada valor de la hora, y de la mejor ruta conocida (línea negra). Fuente: elaboración propia.

## Parte 2: discusión

**El ACO superó al AG en costo y en estabilidad.** Su desviación estándar fue 5 veces menor. La visibilidad η = 1/c guía a cada hormiga hacia los tramos baratos desde la primera iteración. El AG, en cambio, parte de permutaciones aleatorias, y su mutación por intercambio de dos ciudades cambia cuatro aristas a la vez, casi siempre empeorando la ruta. Aun así, la mejor ruta del ACO tiene cruces visibles en la Figura 3 (por ejemplo, Girona – Castellón). Un recorrido con cruces no es óptimo: deshacer el cruce con un movimiento 2-opt lo acorta. Por eso ninguno de los dos resultados es el óptimo.

**El ruido de los heurísticos pesa más que el efecto del valor de la hora.** 8 de las 10 corridas del ACO terminaron entre 2381 y 2433 EUR, lo que es consistente con el estancamiento de la feromona descrito en la cacería de la alucinación. En el barrido, la mejor corrida se alejó hasta 194.73 EUR de la mejor ruta conocida para el mismo h, y la ruta que resultó mejor para h < 8.56 se encontró corriendo con h = 160. Por eso el umbral de 8.56 EUR/h es una cota de lo que encontraron los heurísticos, no el umbral exacto del óptimo.

**El tiempo domina el costo.** Con h = 20 EUR/h el tiempo representa el 69 % del total y los peajes menos del 3 %. Esto explica por qué la ruta cambia tan poco al subir h: las rutas buenas ya son casi las más rápidas.

**Limitación del modelo: una sola ruta por par.** Cada tramo usa siempre la ruta más rápida, pague o no peaje, así que el valor de la hora solo puede cambiar el orden de las ciudades, no la decisión de pagar el peaje. Los datos de Valhalla incluyen también la ruta que evita peajes (`data/valhalla/rutas_valhalla.csv`). Por ejemplo, para A Coruña → Albacete con h = 20 EUR/h:

- ruta con peaje (7.92 h, 855.6 km): 275.55 EUR;
- ruta libre (8.33 h, 863.1 km): 248.78 EUR.

El peaje solo compensa a partir de h ≈ 85 EUR/h. Un modelo con costo mín(ruta con peaje, ruta libre) por tramo respondería mejor a la pregunta del valor de la hora; queda como trabajo futuro.

## Reproducibilidad

Todo el trabajo se regenera desde un repositorio con un solo entorno para las dos partes. **[PENDIENTE: URL del repositorio y hash del commit de entrega; probar un clon limpio en otra máquina.]**

- **Entorno:** Python 3.11 o superior (probado con 3.13/3.14) y `requirements.txt` con versiones fijas: numpy 2.5.3, pandas 3.0.5, matplotlib 3.11.2, pillow 12.3.0 y requests 2.34.2. Las versiones instaladas coinciden con las fijadas; la instalación con `pip install -r requirements.txt` todavía no se probó en una máquina limpia.
- **Semillas:** parte 1, base 12345; parte 2, base 42; la corrida i usa base + i. Mismas semillas, mismos resultados (hay una prueba para la parte 2 y el resultado de la parte 1 no cambió entre versiones de las bibliotecas).
- **Parámetros:** se cambian por línea de comandos o por un JSON, sin editar el código (`--param método.nombre=valor`).
- **Datos:** los CSV de `Optimizacion/Optimizacion_combinatoria/data/` ya están en el repositorio; la ejecución no usa Internet. Se regeneran desde los datos originales con `python importar_valhalla.py` y `python build_data.py --skip-osrm ...`.

Comandos, ejecutados desde la carpeta de cada parte:

```bash
# Parte 1
cd Optimizacion/Optimizacion_heuristica
python main.py check                 # gradientes analíticos vs. diferencias finitas
python main.py compare               # 30 corridas, 4 métodos, 2 funciones, 2D y 3D (~17 s)
python main.py curves                # PNG de convergencia
python main.py animate --method pso --function rastrigin --seed 3   # GIF (~25 s)

# Parte 2
cd ../Optimizacion_combinatoria
python main.py validate                     # revisa datos y matriz de costos
python main.py run --runs 10                # Tabla 3, Figuras 3 y 4, Animación 4 (~6 min)
python main.py run --runs 1 --param aco.iterations=80 --param genetic_algorithm.generations=200   # demostración (< 2 min)
python main.py sweep --runs 3               # Tabla 4 y Figura 5 (~4 min)
python -m unittest discover -s tests        # 35 pruebas
```

## Uso de inteligencia artificial

| Tarea | Qué produjo la IA | Cómo se verificó |
| --- | --- | --- |
| Construir README.md y main.py a partir de los archivos pasados | Archivo README.md de la raiz y main.py de optimizacio heuristica | Se verifico que fuera funcional y legible ejecutandolo en un repo clonado nuevo y se verificaron cada uno de los comandos |
| Implementar los tests de los algoritmos y corregir test de la matriz | test_aco.py, test_genetic_algorithm y test_cost__matrix.py corregido | Se usaron los tests con datos sinteticos |
| Completar y corregir comentarios | La gran parte de comentarios | Se verificaron la mayoria de comentarios |
| Generar archivos complementarios de la parte 2 | build_data.py (a partir de OSRM), main.py, tsp_data.py, sources.md, requirements.txt y README.md | Se verificaron los datos extraidos |
| Generar reporte en markdown a partir de documento y complementos | Produjo la gran mayoria del texto de este documento y los otros archivos en docs | Se valido en la pagina del blog |
| Construir los datos reales de la parte 2 (rutas, peajes, combustible) | Consultas a Valhalla y a la API del MITECO, tabla de tarifas `peajes_2026.csv` con URL oficial por fila, `build_rutas.py` y `FUENTES.md` | Se abrieron los PDF oficiales de cada tarifa; se calculó a mano el peaje de A Coruña – Albacete (35.67 EUR) y coincidió con el CSV |
| Revisar el código de la parte 2 e integrar los datos | Diagnóstico de lo que faltaba, `importar_valhalla.py`, `preparar_mapa.py`, `sources.md` y README actualizados | `python main.py validate`, las 35 pruebas y una corrida completa; se compararon las distancias de OSRM y Valhalla |
| Redactar las secciones de datos, resultados y discusión de la parte 2 | Texto de este reporte a partir de los CSV de `results/` | Cada cifra se comprobó contra `comparison.csv`, `best_route.json` y `hourly_sweep_envelope.csv` |


## Cacería de la alucinación

Se registran los errores y suposiciones falsas del asistente que se detectaron al ejecutar y probar el código. 

| # | Qué afirmó o hizo la IA | Cómo se detectó | Corrección |
| --- | --- | --- | --- |
| 1 | El ACO con los parámetros por defecto encuentra buenas rutas | Una prueba con 7 ciudades y óptimo conocido por fuerza bruta: 0 de 10 semillas lo alcanzaron, y el resultado era idéntico con 80, 500 o 2000 iteraciones. Con 47 ciudades, 150 y 450 iteraciones dieron los mismos costos | Estancamiento de la feromona: sin cota inferior, las aristas no usadas bajan a ~10⁻¹⁷, por debajo del piso de 10⁻¹² del código, y quedan unas 10⁹ veces menos probables. Se añadió `min_pheromone_fraction` (cota estilo MAX-MIN); con 0.1 alcanza el óptimo en 8 de 10 semillas en 7 ciudades, pero con 47 ciudades empeoró con 150 iteraciones y mejoró solo 0.3 % con 0.01 y 450 iteraciones. Hay que ajustarlo con datos reales |
| 2 | Para ver si cambia la ruta con el valor de la hora, bastaba comparar la ruta final de cada h | Con datos sintéticos, el AG dio rutas más lentas al subir h, algo imposible para un óptimo: el ruido del heurístico se confundía con cambios reales | Se reemplazó por la envolvente inferior de las rectas C(h) = h·T + M de todas las rutas halladas |
| 3 | Las columnas `ciudad/lon/lat` y `ruta/costo` del script de visualización original eran compatibles con el resto | El script de datos usaba `city/longitude/latitude` y los algoritmos devuelven `route/cost/generation` | Se unificaron los nombres en la versión en inglés |
| 4 | OSRM público expone la clase `toll` en sus rutas, así que detectar peajes era leer ese campo | El equipo ejecutó la detección y el servidor no devolvió ninguna clase; la salvaguarda del código se negó a seguir en vez de marcar toda ruta como gratuita | Se probó una segunda versión (cruzar la geometría de la ruta con las vías de OpenStreetMap); tampoco se pudo descargar la geometría (504 de Overpass). Se retiró todo el codigo |
| 5 | Un cambio de nombres de módulos y variables en la parte 1 no afectaba al resultado | Colisiones de nombres de módulos (`functions`) y claves de diccionario que también se habían renombrado | Se corrigieron las importaciones y se comprobó que los resultados eran idénticos|
| 6 | `build_data.py` (generado por IA) usaba por defecto 6.0 L/100 km y 1.60 EUR/L, mientras que el vehículo de `config/experiment.json` consume 5.3 L/100 km a 1.7961 EUR/L | Al comparar `data/cost_matrix.csv` con la matriz que construye `main.py`: los valores por defecto del script no son los del vehículo, así que la matriz guardada no coincidía con la usada | Se pasan los valores de forma explícita (`--consumption 5.3 --fuel-price 1.7961`) y el comando quedó documentado en el README |
| 7 | El README y `sources.md` generados por IA citaban archivos y carpetas que no existen: `genetic_algorithm.py`, `tsp_visualization.py`, `toll_tools.py` y `parte2_tsp/` | Al seguir las instrucciones del README en el repositorio clonado, los comandos y referencias no encontraban los archivos (los reales son `algoritmo_genetico.py` y `tsp_visualizacion.py`) | Se corrigieron los nombres en el README y se retiró la descripción de `toll_tools.py` de `sources.md` |
| 8 | Las coordenadas de las 47 capitales en `cities.csv` las escribió la IA de memoria, sin fuente | `sources.md` lo declaraba; un dato sin fuente no se puede citar | Se reemplazaron por las de Wikidata (P625). La diferencia máxima fue de 1.6 km (A Coruña): eran aproximadas, no inventadas, pero no eran verificables |


## Referencias

- ADAC. (s. f.). *Dacia Sandero (3. Generation) TCe 90* [Ficha técnica, ADAC Autokatalog]. Recuperado el 13 de octubre de 2026 de https://www.adac.de/rund-ums-fahrzeug/autokatalog/marken-modelle/dacia/sandero/3generation/334757
- Armijo, L. (1966). Minimization of functions having Lipschitz continuous first partial derivatives. *Pacific Journal of Mathematics, 16*(1), 1–3.
- Clerc, M., & Kennedy, J. (2002). The particle swarm: Explosion, stability, and convergence in a multidimensional complex space. *IEEE Transactions on Evolutionary Computation, 6*(1), 58–73.
- Code for America. (s. f.). *click_that_hood* [Repositorio de GitHub]. Recuperado el 13 de octubre de 2026 de https://github.com/codeforamerica/click_that_hood
- Davis, L. (1985). Applying adaptive algorithms to epistatic domains. En *Proceedings of the 9th International Joint Conference on Artificial Intelligence* (Vol. 1, pp. 162–164).
- Dorigo, M., Maniezzo, V., & Colorni, A. (1996). Ant system: Optimization by a colony of cooperating agents. *IEEE Transactions on Systems, Man, and Cybernetics, Part B, 26*(1), 29–41.
- Eshelman, L. J., & Schaffer, J. D. (1993). Real-coded genetic algorithms and interval-schemata. En L. D. Whitley (Ed.), *Foundations of genetic algorithms 2* (pp. 187–202). Morgan Kaufmann.
- Holland, J. H. (1975). *Adaptation in natural and artificial systems*. University of Michigan Press.
- Kennedy, J., & Eberhart, R. (1995). Particle swarm optimization. En *Proceedings of ICNN'95: International Conference on Neural Networks* (Vol. 4, pp. 1942–1948). IEEE.
- Luxen, D., & Vetter, C. (2011). Real-time routing with OpenStreetMap data. En *Proceedings of the 19th ACM SIGSPATIAL International Conference on Advances in Geographic Information Systems* (pp. 513–516). ACM.
- Ministerio de Transportes y Movilidad Sostenible. (2026). *Peajes vigentes desde el 01/01/2026* [Tarifas por autopista]. Recuperado el 13 de octubre de 2026 de https://www.transportes.gob.es
- Ministerio para la Transición Ecológica y el Reto Demográfico. (2026). *Precios de carburantes en estaciones de servicio terrestres* [API REST, Geoportal de Gasolineras]. Recuperado el 13 de octubre de 2026 de https://sedeaplicaciones.minetur.gob.es/ServiciosRESTCarburantes/PreciosCarburantes/EstacionesTerrestres/
- Nocedal, J., & Wright, S. J. (2006). *Numerical optimization* (2.ª ed.). Springer.
- OpenStreetMap contributors. (2026). *OpenStreetMap* [Base de datos geográfica]. https://www.openstreetmap.org
- Project OSRM. (s. f.). *OSRM API documentation*. https://project-osrm.org/docs/v5.24.0/api/.
- Rosenbrock, H. H. (1960). An automatic method for finding the greatest or least value of a function. *The Computer Journal, 3*(3).
- Storn, R., & Price, K. (1997). Differential evolution: A simple and efficient heuristic for global optimization over continuous spaces. *Journal of Global Optimization, 11*(4).
- Stützle, T., & Hoos, H. H. (2000). MAX–MIN ant system. *Future Generation Computer Systems, 16*(8).
- Törn, A., & Žilinskas, A. (1989). *Global optimization* (Lecture Notes in Computer Science, Vol. 350).
- Valhalla contributors. (2025). *Valhalla* (Versión 3.9.1) [Software]. https://github.com/valhalla/valhalla
- Wikidata. (2026). *Wikidata Query Service*. Recuperado el 13 de octubre de 2026 de https://query.wikidata.org