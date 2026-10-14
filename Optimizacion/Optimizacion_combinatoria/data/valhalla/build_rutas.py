"""Construye data/tsp/rutas_valhalla.csv y completa km_referencia en peajes_2026.csv.

Entradas:
  raw/rutas_base.csv      tiempo y distancia (promedio ida y vuelta), con y sin peajes (Valhalla /route)
  raw/peajes_aristas.txt  km de peaje por vía, arista por arista (Valhalla /trace_attributes), ruta i->j
  mapa_refs_peaje.csv     nombre de la vía en OSM -> grupo tarifario
  peajes_2026.csv         tarifas oficiales y par de referencia de cada grupo

Salida:
  rutas_valhalla.csv      i, j, t_peaje_s, d_peaje_km, t_libre_s, d_libre_km, peaje_refs_km (grupo:km;...)

Se ejecuta una sola vez:  python data/tsp/build_rutas.py   (los resultados se versionan en Git)
"""
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
A_CORUNA = 0
EXENTO_AP9_KM = 10.5   # A Coruña - A Barcala está exento (RD 633/2006); salir de A Coruña al este no paga


def main():
    cities = pd.read_csv(HERE / "capitales.csv")
    name2id = dict(zip(cities.ciudad, cities.id))
    base = pd.read_csv(HERE / "raw" / "rutas_base.csv")
    gmap = pd.read_csv(HERE / "mapa_refs_peaje.csv", comment="#")
    ref2g = dict(zip(gmap.ref_osm, gmap.grupo))

    tolls, method, unknown = {}, {}, set()
    for line in (HERE / "raw" / "peajes_aristas.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        key, refs, how = line.split("|")[:3]
        groups = {}
        for part in filter(None, refs.split(";")):
            ref, km = part.rsplit(":", 1)
            g = ref2g.get(ref)
            if g is None:
                unknown.add(ref); continue
            groups[g] = groups.get(g, 0.0) + float(km)
        dom = groups.pop("DOMINANTE", 0.0)
        groups.pop("LIBRE", None)
        if dom and groups:
            gmax = max(groups, key=groups.get); groups[gmax] += dom
        tolls[key], method[key] = groups, how
    if unknown:
        raise SystemExit(f"Referencias sin mapear en mapa_refs_peaje.csv: {sorted(unknown)}")

    # Respaldo "maniobras" (solo rutas > 1000 km): una maniobra puede incluir tramos libres contiguos,
    # así que los km de cada autopista se limitan al máximo medido arista por arista para esa autopista.
    exact_max = {}
    for key, g in tolls.items():
        if method[key] != "maniobras":
            for k, km in g.items():
                exact_max[k] = max(exact_max.get(k, 0), km)
    for key, g in tolls.items():
        if method[key] == "maniobras":
            for k in g:
                g[k] = min(g[k], exact_max.get(k, g[k]))
        i, j = map(int, key.split("-"))
        lim = EXENTO_AP9_KM if method[key] != "maniobras" else 16.0
        if A_CORUNA in (i, j) and 0 < g.get("AP-9", 0) <= lim:
            g.pop("AP-9")
        tolls[key] = {k: km for k, km in g.items() if km > 0.05}

    rows = []
    for r in base.itertuples():
        key = f"{r.i}-{r.j}"
        if r.usa_peaje and key not in tolls:
            raise SystemExit(f"Falta el detalle de peajes del par {key}")
        g = dict(tolls.get(key, {})) if r.usa_peaje else {}
        tA, dA = r.t_peaje_s, r.d_peaje_km
        if "PORTUGAL" in g:            # ruta por Portugal: se usa la ruta sin peajes por España
            tA, dA, g = r.t_libre_s, r.d_libre_km, {}
        free_ok = bool(r.usa_peaje) and r.libre_usa_peaje == 0 and bool(g)
        rows.append({
            "i": r.i, "j": r.j, "t_peaje_s": tA, "d_peaje_km": dA,
            # si la ruta "sin peajes" también usó uno, o la ruta rápida no paga nada, no hay alternativa
            "t_libre_s": r.t_libre_s if free_ok else float("nan"),
            "d_libre_km": r.d_libre_km if free_ok else float("nan"),
            "peaje_refs_km": ";".join(f"{k}:{v:.3f}" for k, v in sorted(g.items())),
            "metodo_peaje": method.get(key, "") if g else "",
            "asim_t_rel": r.asim_t_rel,
        })
    out = pd.DataFrame(rows)
    out.to_csv(HERE / "rutas_valhalla.csv", index=False)

    # km de referencia de cada tarifa
    lines = (HERE / "peajes_2026.csv").read_text(encoding="utf-8").splitlines()
    header = [l for l in lines if l.startswith("#")]
    t = pd.read_csv(HERE / "peajes_2026.csv", comment="#")
    for idx, row in t.iterrows():
        if row.tipo != "km":
            continue
        if row.par_referencia == "max":
            km = max((v.get(row.grupo, 0) for k, v in tolls.items() if method[k] != "maniobras"), default=0)
        else:
            a, b = (name2id[x] for x in row.par_referencia.split("-"))
            km = tolls.get(f"{min(a, b)}-{max(a, b)}", {}).get(row.grupo, 0)
        if km <= 0:
            raise SystemExit(f"{row.grupo}: el par de referencia {row.par_referencia} no recorre esa autopista")
        t.loc[idx, "km_referencia"] = round(km, 3)
    with open(HERE / "peajes_2026.csv", "w", encoding="utf-8") as fh:
        fh.write("\n".join(header) + "\n")
        t.to_csv(fh, index=False)
    t["eur_km"] = t.peaje_eur / t.km_referencia
    print(t[["grupo", "tipo", "peaje_eur", "par_referencia", "km_referencia", "eur_km"]].to_string(index=False))
    print(f"\n{len(out)} pares; {sum(1 for x in out.peaje_refs_km if x)} con peaje efectivo.")


if __name__ == "__main__":
    main()
