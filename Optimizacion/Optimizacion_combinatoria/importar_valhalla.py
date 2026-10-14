"""convertimos los datos de Valhalla (data/valhalla/) al formato que usa main.py (data/)."""
import json
from pathlib import Path

import pandas as pd

SRC = Path("data/valhalla")
OUT = Path("data")
FECHA = "2026-10-13"
VALHALLA_URL = "https://valhalla.github.io/valhalla/api/turn-by-turn/api-reference/"


def cargar_tarifas():
    t = pd.read_csv(SRC / "peajes_2026.csv", comment="#")
    tarifas = {}
    for r in t.itertuples():
        valor = r.peaje_eur / r.km_referencia if r.tipo == "km" else r.peaje_eur
        tarifas[r.grupo] = (r.tipo, valor, r.url)
    return tarifas


def peaje_de(refs, tarifas):
    """'AP-6:56.41;R-4:50.69' -> (euros, [urls], notas)."""
    if not isinstance(refs, str) or not refs:
        return 0.0, [], "sin autopistas de peaje"
    total, urls = 0.0, []
    for parte in refs.split(";"):
        grupo, km = parte.rsplit(":", 1)
        tipo, valor, url = tarifas[grupo]
        total += float(km) * valor if tipo == "km" else valor
        urls.append(url)
    return total, urls, refs.replace(";", "; ")


def main():
    capitales = pd.read_csv(SRC / "capitales.csv")
    nombre = dict(zip(capitales.id, capitales.ciudad))
    nombres = capitales.ciudad.tolist()
    tarifas = cargar_tarifas()
    rutas = pd.read_csv(SRC / "rutas_valhalla.csv")

    km = pd.DataFrame(0.0, index=nombres, columns=nombres)
    horas = km.copy()
    filas = []
    for r in rutas.itertuples():
        a, b = nombre[r.i], nombre[r.j]
        euros, urls, notas = peaje_de(r.peaje_refs_km, tarifas)
        for o, d in ((a, b), (b, a)):   
            km.loc[o, d] = r.d_peaje_km
            horas.loc[o, d] = r.t_peaje_s / 3600
            filas.append({
                "origin": o, "destination": d, "toll_eur": round(euros, 4),
                "toll_status": "verified", "vehicle_class": "ligeros",
                "source_url": "; ".join(urls) if urls else VALHALLA_URL,
                "consultation_date": FECHA,
                "notes": f"{notas} (tarifa prorrateada por km; ver data/valhalla/FUENTES.md)",
            })
    for c in nombres:                            
        filas.append({"origin": c, "destination": c, "toll_eur": 0.0,
                      "toll_status": "not_applicable", "vehicle_class": "ligeros",
                      "source_url": "", "consultation_date": "", "notes": ""})

    for frame in (km, horas):
        frame.index.name = "city"
    km.to_csv(OUT / "distances.csv", encoding="utf-8")
    horas.to_csv(OUT / "travel_times.csv", encoding="utf-8")
    pd.DataFrame(filas).to_csv(OUT / "toll_costs.csv", index=False, encoding="utf-8")
    capitales.rename(columns={"ciudad": "city", "lon": "longitude", "lat": "latitude"})[
        ["city", "longitude", "latitude", "wikidata"]].to_csv(OUT / "cities.csv", index=False, encoding="utf-8")
    (OUT / "valhalla_metadata.json").write_text(json.dumps({
        "source": "Valhalla /route sobre OpenStreetMap", "retrieved_on": FECHA,
        "units": {"distances.csv": "km", "travel_times.csv": "h"},
        "note": "Ruta más rápida con peajes permitidos; promedio de ida y vuelta.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(filas) - len(nombres)} pares dirigidos escritos; "
          f"{sum(f['toll_eur'] > 0 for f in filas)} con peaje.")


if __name__ == "__main__":
    main()