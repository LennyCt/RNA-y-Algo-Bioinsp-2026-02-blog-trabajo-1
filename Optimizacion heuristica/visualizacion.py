from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from matplotlib.animation import FuncAnimation, PillowWriter

# Obtener la carpeta donde se encuentra este archivo Python.
CARPETA_ACTUAL = Path(__file__).parent

# Carpetas donde se guardarán los resultados.
CARPETA_RESULTADOS = CARPETA_ACTUAL / "resultados"
CARPETA_GRAFICAS = CARPETA_RESULTADOS / "graficas"
CARPETA_ANIMACIONES = CARPETA_RESULTADOS / "animaciones"

# Crear las carpetas si todavía no existen.
CARPETA_GRAFICAS.mkdir(parents=True, exist_ok=True)
CARPETA_ANIMACIONES.mkdir(parents=True, exist_ok=True)

def plot_function(
    f,
    x1_range,
    x2_range,
    title="Function Plot",
    minima=None,
    x1_point=None,
    x2_point=None,
    elev=30,
    azim=45,
    output_filename="funcion.png"
):
    """
    Dibuja la superficie 3D y las curvas de nivel de una función
    de dos variables.

    Parámetros:
        f: función que recibe un array [X1, X2].
        x1_range: límites de la primera variable.
        x2_range: límites de la segunda variable.
        title: título de la gráfica.
        minima: lista de tuplas (x1, x2) con mínimos conocidos.
        x1_point, x2_point: mínimo individual, por compatibilidad.
        elev, azim: ángulos de observación de la superficie.
    """

    # Generar las coordenadas de ambas variables.
    x1 = np.linspace(x1_range[0], x1_range[1], 200)
    x2 = np.linspace(x2_range[0], x2_range[1], 200)

    # Crear la cuadrícula de puntos.
    X1, X2 = np.meshgrid(x1, x2)

    # Evaluar la función en toda la cuadrícula.
    Z = np.asarray(f(np.array([X1, X2])))

    # Comprobar que la salida tenga la forma esperada.
    if Z.shape != X1.shape:
        raise ValueError(
            "La función debe aceptar arrays de coordenadas "
            "y devolver una matriz del mismo tamaño que X1 y X2."
        )

    # Unificar las formas de especificar los mínimos.
    if minima is None:
        minima = []

    if x1_point is not None and x2_point is not None:
        minima = list(minima) + [(x1_point, x2_point)]

    fig = plt.figure(figsize=(14, 6))

    # -------------------------------
    # Gráfica 3D
    # -------------------------------
    ax1 = fig.add_subplot(121, projection="3d")

    surface = ax1.plot_surface(
        X1, X2, Z,
        cmap="viridis",
        edgecolor="none",
        alpha=0.85
    )

    ax1.set_title(f"Superficie 3D: {title}")
    ax1.set_xlabel("x1")
    ax1.set_ylabel("x2")
    ax1.set_zlabel("f(x1, x2)")
    ax1.view_init(elev=elev, azim=azim)

    fig.colorbar(surface, ax=ax1, shrink=0.6, pad=0.1)

    # Marcar los mínimos conocidos.
    for i, (xm, ym) in enumerate(minima):
        zm = float(np.asarray(f(np.array([xm, ym]))))

        ax1.scatter(
            [xm], [ym], [zm],
            color="red",
            marker="o",
            s=60,
            label=f"Mínimo {i + 1}"
        )

    if minima:
        ax1.legend()

    # -------------------------------
    # Mapa de contorno
    # -------------------------------
    ax2 = fig.add_subplot(122)

    contour = ax2.contourf(
        X1, X2, Z,
        levels=30,
        cmap="viridis"
    )

    ax2.contour(
        X1, X2, Z,
        levels=15,
        colors="black",
        linewidths=0.35,
        alpha=0.5
    )

    ax2.set_title(f"Curvas de nivel: {title}")
    ax2.set_xlabel("x1")
    ax2.set_ylabel("x2")

    fig.colorbar(contour, ax=ax2, label="f(x1, x2)")

    # Marcar los mínimos también en el mapa.
    for i, (xm, ym) in enumerate(minima):
        ax2.scatter(
            xm, ym,
            color="red",
            marker="*",
            s=100,
            label=f"Mínimo {i + 1}",
            zorder=5
        )

    if minima:
        ax2.legend()

    plt.tight_layout()

    # Guardar la gráfica en la carpeta correspondiente.
    ruta_salida = CARPETA_GRAFICAS / output_filename
    fig.savefig(ruta_salida, dpi=300, bbox_inches="tight")

    print(f"Gráfica guardada en: {ruta_salida}")

    plt.show()
    plt.close(fig)


def create_3d_animation(
    func,
    dataframe,
    x1_range,
    x2_range,
    output_filename="trayectoria.gif",
    title="Trayectoria de optimización",
    elev=30,
    azim=45,
    interval=300
):
    """
    Genera un GIF que muestra la trayectoria de una solución
    sobre la superficie de una función.

    Columnas requeridas:
        x1, x2, f(x1,x2)

    Cada fila representa una iteración del algoritmo.
    """

    required_columns = ["x1", "x2", "f(x1,x2)"]

    if not all(col in dataframe.columns for col in required_columns):
        raise ValueError(
            f"El DataFrame debe contener: {required_columns}"
        )

    if dataframe.empty:
        raise ValueError("El DataFrame no puede estar vacío.")

    # Extraer las coordenadas de la trayectoria.
    x1_vals = dataframe["x1"].to_numpy(dtype=float)
    x2_vals = dataframe["x2"].to_numpy(dtype=float)
    z_vals = dataframe["f(x1,x2)"].to_numpy(dtype=float)

    # Crear la superficie de la función.
    x1 = np.linspace(*x1_range, 150)
    x2 = np.linspace(*x2_range, 150)
    X1, X2 = np.meshgrid(x1, x2)

    Z = np.asarray(func(np.array([X1, X2])))

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_surface(
        X1, X2, Z,
        cmap="viridis",
        alpha=0.65,
        edgecolor="none"
    )

    # Preparar la línea y el marcador de la solución.
    line, = ax.plot(
        [], [], [],
        color="red",
        marker="o",
        markersize=4,
        linewidth=2,
        label="Trayectoria"
    )

    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_zlabel("f(x1, x2)")
    ax.set_title(title)
    ax.view_init(elev=elev, azim=azim)
    ax.legend()

    # Texto que indica la iteración actual.
    iteration_text = ax.text2D(
        0.03, 0.95, "",
        transform=ax.transAxes
    )

    def update(frame):
        # Mostrar todas las posiciones hasta esta iteración.
        line.set_data(
            x1_vals[:frame + 1],
            x2_vals[:frame + 1]
        )

        line.set_3d_properties(z_vals[:frame + 1])

        iteration_text.set_text(
            f"Iteración: {frame + 1}/{len(dataframe)}\n"
            f"f(x) = {z_vals[frame]:.6f}"
        )

        return line, iteration_text

    animation = FuncAnimation(
        fig,
        update,
        frames=len(dataframe),
        interval=interval,
        blit=False
    )

    # Guardar el GIF en la carpeta de animaciones.
    ruta_salida = CARPETA_ANIMACIONES / output_filename

    animation.save( 
        ruta_salida,
        writer=PillowWriter(fps=4)
    )

    plt.show()
    plt.close(fig)
    print(f"Animación guardada en: {ruta_salida}")

    return animation




def create_population_animation(
    func,
    dataframe,
    x1_range,
    x2_range,
    output_filename="poblacion.gif",
    title="Evolución de la población",
    elev=30,
    azim=45,
    interval=500
):
    """
    Genera un GIF de la evolución de una población sobre
    la superficie de una función.

    Columnas requeridas:
        generation, x1, x2, f(x1,x2)

    Cada fila representa un individuo de una generación.
    """

    required_columns = [
        "generation", "x1", "x2", "f(x1,x2)"
    ]

    if not all(col in dataframe.columns for col in required_columns):
        raise ValueError(
            f"El DataFrame debe contener: {required_columns}"
        )

    if dataframe.empty:
        raise ValueError("El DataFrame no puede estar vacío.")

    # Ordenar las generaciones cronológicamente.
    dataframe = dataframe.sort_values("generation").copy()
    generations = sorted(dataframe["generation"].unique())

    # Preparar la superficie.
    x1 = np.linspace(*x1_range, 150)
    x2 = np.linspace(*x2_range, 150)
    X1, X2 = np.meshgrid(x1, x2)

    Z = np.asarray(func(np.array([X1, X2])))

    fig = plt.figure(figsize=(10, 7))
    ax = fig.add_subplot(111, projection="3d")

    ax.plot_surface(
        X1, X2, Z,
        cmap="viridis",
        alpha=0.65,
        edgecolor="none"
    )

    # Puntos de la población de la generación actual.
    points = ax.scatter(
        [], [], [],
        color="red",
        s=35,
        label="Población"
    )

    ax.set_xlabel("x1")
    ax.set_ylabel("x2")
    ax.set_zlabel("f(x1, x2)")
    ax.set_title(title)
    ax.view_init(elev=elev, azim=azim)
    ax.legend()

    generation_text = ax.text2D(
        0.03, 0.95, "",
        transform=ax.transAxes
    )

    def update(frame):
        generation = generations[frame]

        current = dataframe[
            dataframe["generation"] == generation
        ]

        # Actualizar las coordenadas de todos los individuos.
        points._offsets3d = (
            current["x1"].to_numpy(),
            current["x2"].to_numpy(),
            current["f(x1,x2)"].to_numpy()
        )

        best_value = current["f(x1,x2)"].min()

        generation_text.set_text(
            f"Generación: {generation}\n"
            f"Mejor valor de la generación: {best_value:.6f}"
        )

        return points, generation_text

    animation = FuncAnimation(
        fig,
        update,
        frames=len(generations),
        interval=interval,
        blit=False
    )
    
    # Guardar el GIF en la carpeta de animaciones.
    ruta_salida = CARPETA_ANIMACIONES / output_filename

    animation.save(
        ruta_salida,
        writer=PillowWriter(fps=4)
    )

    plt.show()
    plt.close(fig)
    print(f"Animación guardada en: {ruta_salida}")

    return animation


# Función temporal para probar las gráficas.
def funcion_prueba(X):
    x, y = X
    return x**2 + y**2


# Probar la superficie 3D y el mapa de contorno.
plot_function(
    f=funcion_prueba,
    x1_range=(-3, 3),
    x2_range=(-3, 3),
    title="Función de prueba",
    minima=[(0, 0)]
)


# Crear datos ficticios de una trayectoria.
valores = np.linspace(2.5, 0, 30)

trayectoria = pd.DataFrame({
    "x1": valores,
    "x2": valores,
    "f(x1,x2)": valores**2 + valores**2
})

# Probar la animación de trayectoria.
create_3d_animation(
    func=funcion_prueba,
    dataframe=trayectoria,
    x1_range=(-3, 3),
    x2_range=(-3, 3),
    output_filename="prueba_trayectoria.gif",
    title="Prueba de trayectoria"
)


# Crear datos ficticios de una población.
filas = []

for generacion in range(5):
    for individuo in range(8):
        x = np.random.uniform(-3, 3) / (generacion + 1)
        y = np.random.uniform(-3, 3) / (generacion + 1)

        filas.append({
            "generation": generacion,
            "x1": x,
            "x2": y,
            "f(x1,x2)": x**2 + y**2
        })

poblacion = pd.DataFrame(filas)

# Probar la animación de población.
create_population_animation(
    func=funcion_prueba,
    dataframe=poblacion,
    x1_range=(-3, 3),
    x2_range=(-3, 3),
    output_filename="prueba_poblacion.gif",
    title="Prueba de población"
)
