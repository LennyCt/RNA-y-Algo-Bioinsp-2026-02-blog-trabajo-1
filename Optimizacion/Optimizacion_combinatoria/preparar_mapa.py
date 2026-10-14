"""Genera data/spain_peninsular.geojson (47 provincias peninsulares) para las figuras y el GIF."""
import json
from pathlib import Path

ORIGEN = Path("data/valhalla/spain-provinces.geojson")
DESTINO = Path("data/spain_peninsular.geojson")
EXCLUIR = {"Illes Balears", "Las Palmas", "Santa Cruz De Tenerife", "Ceuta", "Melilla"}

geo = json.loads(ORIGEN.read_text(encoding="utf-8"))
nombres = {f["properties"]["name"] for f in geo["features"]}
faltan = EXCLUIR - nombres
if faltan:
    raise SystemExit(f"No se encontraron en el GeoJSON: {sorted(faltan)}")

geo["features"] = [f for f in geo["features"] if f["properties"]["name"] not in EXCLUIR]
if len(geo["features"]) != 47:
    raise SystemExit(f"Se esperaban 47 provincias y quedaron {len(geo['features'])}")
DESTINO.write_text(json.dumps(geo, ensure_ascii=False), encoding="utf-8")
print(f"{DESTINO}: {len(geo['features'])} provincias peninsulares")