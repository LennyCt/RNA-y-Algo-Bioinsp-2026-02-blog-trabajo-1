"""Visualización de la evolución del TSP para las 47 capitales peninsulares.

Estructuras esperadas
---------------------
cities:
    pandas.DataFrame con columnas (las mismas de data/cities.csv):
        - city: nombre de la capital
        - longitude: longitud en grados
        - latitude: latitud en grados

history:
    lista de diccionarios, uno por iteración/generación, tal como los devuelven
    `ant_colony_optimization` y `genetic_algorithm`:
    [
        {"generation": 0, "cost": 12500.0, "route": ["Madrid", "Ávila", ..., "Madrid"]},
        {"generation": 1, "cost": 11900.0, "route": ["Madrid", "Segovia", ..., "Madrid"]},
    ]

La ruta puede contener nombres de ciudades o índices enteros que correspondan al
orden de filas de `cities`. Si la ruta no repite la ciudad inicial al final, la
función cierra el circuito automáticamente.

Para dibujar la silueta de España peninsular se puede pasar un GeoJSON local
(por ejemplo data/spain_peninsular.geojson). Así la animación se regenera sin
Internet. Si no se proporciona, la ruta se dibuja sobre el plano longitud/latitud
y se emite una advertencia: NO se muestra la silueta del país.
"""
from __future__ import annotations

import json
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # solo guardamos archivos; no se abren ventanas
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.animation import FuncAnimation, PillowWriter  # noqa: E402


_WARNED = {"no_geojson": False}


def _validate_cities(cities: pd.DataFrame) -> pd.DataFrame:
    """Comprueba y normaliza las columnas necesarias."""
    required_columns = {"city", "longitude", "latitude"}
    missing_columns = required_columns - set(cities.columns)
    if missing_columns:
        raise ValueError(
            "El DataFrame de ciudades debe contener las columnas "
            f"{sorted(required_columns)}. Faltan: {sorted(missing_columns)}"
        )
    cities = cities.copy().reset_index(drop=True)
    if cities["city"].duplicated().any():
        raise ValueError("Hay nombres de ciudades duplicados.")
    if cities[["longitude", "latitude"]].isnull().any().any():
        raise ValueError("Hay coordenadas vacías.")
    return cities


def _draw_boundary(ax, geojson_path) -> None:
    """Dibuja geometrías Polygon/MultiPolygon desde un GeoJSON local."""
    path = Path(geojson_path)
    if not path.exists():
        raise FileNotFoundError(f"No existe el GeoJSON: {path}")
    with path.open("r", encoding="utf-8") as file:
        geojson = json.load(file)

    def draw_geometry(geometry: dict) -> None:
        geometry_type = geometry.get("type")
        coordinates = geometry.get("coordinates", [])
        if geometry_type == "Polygon":
            polygons = [coordinates]
        elif geometry_type == "MultiPolygon":
            polygons = coordinates
        else:
            return
        for polygon in polygons:
            if polygon:
                exterior = np.asarray(polygon[0], dtype=float)  # primer anillo = contorno
                ax.plot(exterior[:, 0], exterior[:, 1], linewidth=1.0, color="0.45")

    kind = geojson.get("type")
    if kind == "FeatureCollection":
        for feature in geojson.get("features", []):
            draw_geometry(feature.get("geometry", {}))
    elif kind == "Feature":
        draw_geometry(geojson.get("geometry", {}))
    else:
        draw_geometry(geojson)


def _normalize_route(route, cities: pd.DataFrame) -> list[str]:
    """Convierte una ruta de nombres o índices en una lista cerrada de nombres."""
    city_names = cities["city"].tolist()
    normalized = []
    for item in route:
        if isinstance(item, (int, np.integer)):
            if not 0 <= int(item) < len(city_names):
                raise ValueError(f"Índice de ciudad fuera de rango: {item}")
            normalized.append(city_names[int(item)])
        else:
            if str(item) not in city_names:
                raise ValueError(f"Ciudad no encontrada en el DataFrame: {item}")
            normalized.append(str(item))
    if not normalized:
        raise ValueError("La ruta está vacía.")
    if normalized[-1] != normalized[0]:  # cierra el circuito si el algoritmo no lo hizo
        normalized.append(normalized[0])
    if len(normalized) - 1 != len(city_names) or len(set(normalized[:-1])) != len(city_names):
        raise ValueError("Cada ruta debe visitar cada ciudad exactamente una vez "
                         "(sin contar la repetición final de la ciudad de salida).")
    return normalized


def _prepare_history(history: list[dict], cities: pd.DataFrame) -> list[dict]:
    """Valida el historial y lo normaliza a claves generation/cost/route."""
    if not history:
        raise ValueError("El historial está vacío.")
    prepared = []
    for position, entry in enumerate(history):
        if "route" not in entry:
            raise ValueError(f"La entrada {position} no contiene la clave 'route'.")
        if entry.get("cost") is None:
            raise ValueError(f"La entrada {position} debe incluir 'cost'.")
        prepared.append({
            "generation": int(entry.get("generation", entry.get("iteration", position))),
            "cost": float(entry["cost"]),
            "route": _normalize_route(entry["route"], cities),
        })
    return prepared


def compress_history(history: list[dict], max_frames: int = 60) -> list[dict]:
    """Reduce el historial a los fotogramas que muestran mejoras (más el primero y el último).

    El historial guarda la mejor solución hasta cada iteración, así que casi todas
    las entradas repiten la misma ruta; dibujar solo los cambios hace el GIF corto.
    Si aun así hay más de `max_frames`, se submuestrea conservando los extremos.
    """
    if not history:
        return []
    kept = [history[0]]
    for entry in history[1:-1]:
        if entry["cost"] < kept[-1]["cost"]:
            kept.append(entry)
    if len(history) > 1:
        kept.append(history[-1])
    if len(kept) > max_frames:
        positions = np.linspace(0, len(kept) - 1, max_frames).round().astype(int)
        kept = [kept[i] for i in sorted(set(positions))]
    return kept


def _draw_map(ax, cities: pd.DataFrame, geojson_path=None) -> None:
    """Dibuja el límite opcional y las capitales."""
    if geojson_path is not None:
        _draw_boundary(ax, geojson_path)
    elif not _WARNED["no_geojson"]:
        _WARNED["no_geojson"] = True  # una sola advertencia por ejecución
        warnings.warn("Sin GeoJSON: se dibuja el plano longitud/latitud, sin la silueta de España. "
                      "Guarde un GeoJSON en data/spain_peninsular.geojson para dibujarla.",
                      stacklevel=3)
    ax.scatter(cities["longitude"], cities["latitude"], s=20, zorder=4)
    for row in cities.itertuples(index=False):
        ax.annotate(row.city, (row.longitude, row.latitude), xytext=(3, 3),
                    textcoords="offset points", fontsize=6, alpha=0.8)
    lon_margin, lat_margin = 0.45, 0.35
    ax.set_xlim(cities["longitude"].min() - lon_margin, cities["longitude"].max() + lon_margin)
    ax.set_ylim(cities["latitude"].min() - lat_margin, cities["latitude"].max() + lat_margin)
    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")
    # a esta latitud 1 grado de longitud mide ~cos(40°) de uno de latitud
    ax.set_aspect(1.0 / np.cos(np.radians(cities["latitude"].mean())), adjustable="box")
    ax.grid(True, alpha=0.2)


def _route_coordinates(route: list[str], cities: pd.DataFrame):
    """Coordenadas ordenadas para dibujar el circuito cerrado."""
    by_name = cities.set_index("city")
    lon = np.array([float(by_name.loc[name, "longitude"]) for name in route])
    lat = np.array([float(by_name.loc[name, "latitude"]) for name in route])
    return lon, lat


def plot_best_route(cities: pd.DataFrame, best_solution: dict, output_path,
                    geojson_path=None, title: str = "Mejor recorrido encontrado") -> Path:
    """Guarda una imagen estática de la mejor ruta.

    `best_solution` debe tener las claves 'route' y 'cost'.
    """
    cities = _validate_cities(cities)
    solution = _prepare_history([best_solution], cities)[0]
    fig, ax = plt.subplots(figsize=(10, 8))
    _draw_map(ax, cities, geojson_path)
    lon, lat = _route_coordinates(solution["route"], cities)
    ax.plot(lon, lat, linewidth=1.4, marker="o", markersize=3, zorder=3, color="tab:red")
    ax.scatter([lon[0]], [lat[0]], marker="*", s=130, zorder=5, color="gold",
               edgecolors="black", label=f"Salida: {solution['route'][0]}")
    ax.set_title(f"{title}\nCosto total: {solution['cost']:.2f} EUR")
    ax.legend()
    fig.tight_layout()
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"Gráfica guardada en: {output_path}")
    return output_path


def animate_tsp_evolution(cities: pd.DataFrame, history: list[dict], output_path,
                          geojson_path=None,
                          title: str = "Evolución de la mejor ruta del TSP",
                          fps: int = 2, max_frames: int = 60) -> Path:
    """Genera un GIF con la evolución de la mejor ruta sobre el mapa.

    `history` debe guardar la mejor solución encontrada hasta cada iteración (como
    lo hacen ACO y el AG de este repositorio), no una solución cualquiera de la población.
    """
    cities = _validate_cities(cities)
    frames = compress_history(_prepare_history(history, cities), max_frames)

    fig, ax = plt.subplots(figsize=(10, 8))
    _draw_map(ax, cities, geojson_path)
    line, = ax.plot([], [], linewidth=1.6, marker="o", markersize=3, zorder=3, color="tab:red")
    start_marker = ax.scatter([], [], marker="*", s=130, zorder=5, color="gold",
                              edgecolors="black")
    text_box = ax.text(0.02, 0.98, "", transform=ax.transAxes, va="top", ha="left",
                       bbox={"boxstyle": "round", "alpha": 0.85, "facecolor": "white"})
    ax.set_title(title)

    def initialize():
        line.set_data([], [])
        start_marker.set_offsets(np.empty((0, 2)))
        text_box.set_text("")
        return line, start_marker, text_box

    def update(index: int):
        frame = frames[index]
        lon, lat = _route_coordinates(frame["route"], cities)
        line.set_data(lon, lat)
        start_marker.set_offsets(np.array([[lon[0], lat[0]]]))
        text_box.set_text(f"Iteración/generación: {frame['generation']}\n"
                          f"Costo de la mejor ruta: {frame['cost']:.2f} EUR")
        return line, start_marker, text_box

    animation = FuncAnimation(fig, update, frames=len(frames), init_func=initialize,
                              interval=1000 / max(1, fps), blit=False, repeat=True)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    animation.save(output_path, writer=PillowWriter(fps=fps))
    plt.close(fig)
    print(f"Animación guardada en: {output_path} ({len(frames)} fotogramas)")
    return output_path


def save_best_solution_history(history: list[dict], output_path) -> Path:
    """Guarda el historial en CSV (reproducibilidad). La ruta va separada por ' -> '."""
    rows = []
    best_cost = float("inf")
    best_route = None
    for position, entry in enumerate(history):
        cost = float(entry["cost"])
        if cost < best_cost:  # TSP de minimización: se conserva la mejor histórica
            best_cost, best_route = cost, list(entry["route"])
        rows.append({
            "generation": entry.get("generation", position),
            "current_cost": cost,
            "best_cost_so_far": best_cost,
            "best_route": " -> ".join(map(str, best_route)),
        })
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False, encoding="utf-8")
    print(f"Historial guardado en: {output_path}")
    return output_path
