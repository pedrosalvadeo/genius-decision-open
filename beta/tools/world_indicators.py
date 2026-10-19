"""Download the world indicators the home page charts, one for each planetary boundary.

Most series are the World row of an Our World in Data chart, which republishes the
primary source named in each entry; atmospheric CO2 comes straight from NOAA. Run on
a machine with open internet (the "World indicators" GitHub workflow does) and commit
the output:
    python beta/tools/world_indicators.py --out beta/genius_beta/static/world-indicators.json
"""
import argparse
import csv
import io
import json
import sys
import urllib.request

GRAPHER = "https://ourworldindata.org/grapher/"
NOAA_CO2 = "https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_gl.csv"

# One entry per boundary in static/boundaries.json. Slug candidates are tried in order;
# entities too (the first one with data wins). "better" is the direction that helps life.
INDICATORS = [
    dict(id="ozone", boundary="ozone", slugs=["ozone-depleting-substance-consumption"], better="down", total=True, years=(1989, 2100),
         en="Consumption of ozone-depleting substances", es="Consumo de sustancias que agotan el ozono", unit="t",
         note_en="Tonnes weighted by ozone-depleting potential. After the Montreal Protocol (1987) it fell 99 %.",
         note_es="Toneladas ponderadas por su potencial de agotar el ozono. Tras el Protocolo de Montreal (1987) cayó 99 %."),
    dict(id="co2", boundary="climate", source="noaa", better="down", years=(1979, 2100),
         en="CO₂ in the atmosphere", es="CO₂ en la atmósfera", unit="ppm", limit=350,
         note_en="Global annual mean. The planetary boundary is 350 ppm.",
         note_es="Promedio global anual. El límite planetario es de 350 ppm."),
    dict(id="living_planet", boundary="biosphere", slugs=["global-living-planet-index", "living-planet-index"], better="up", years=(1970, 2100), scale=100,
         en="Monitored wildlife populations", es="Poblaciones de fauna silvestre monitoreadas", unit="index",
         note_en="Living Planet Index, 1970 = 100: on average, monitored vertebrate populations shrank 73 %.",
         note_es="Índice Planeta Vivo, 1970 = 100: en promedio, las poblaciones de vertebrados monitoreadas se redujeron 73 %."),
    dict(id="forest", boundary="land", slugs=["forest-area-km"], better="up", years=(1990, 2100), scale=1e-6,
         en="Forest area", es="Superficie de bosques", unit="Mha",
         note_en="The vertical axis does not start at zero. 203 million hectares lost since 1990.",
         note_es="El eje vertical no empieza en cero. Se perdieron 203 millones de hectáreas desde 1990."),
    dict(id="freshwater", boundary="freshwater", slugs=["annual-freshwater-withdrawals"], better="down", years=(1960, 2100), scale=1e-9,
         en="Freshwater withdrawn each year", es="Agua dulce extraída por año", unit="km3",
         note_en="Cubic kilometres a year from rivers, lakes and aquifers, for farming, industry and cities.",
         note_es="Kilómetros cúbicos por año de ríos, lagos y acuíferos, para agricultura, industria y ciudades."),
    dict(id="nitrogen", boundary="nutrients", slugs=["nitrogen-fertilizer-application-per-hectare-of-cropland"], better="down", years=(1961, 2100),
         en="Nitrogen fertilizer per hectare of cropland", es="Fertilizante nitrogenado por hectárea cultivada", unit="kg/ha"),
    dict(id="plastics", boundary="novel_entities", slugs=["global-plastics-production"], better="down", years=(1950, 2100),
         en="Plastic produced each year", es="Plástico producido por año", unit="t"),
    dict(id="ocean_ph", boundary="ocean_acidification", slugs=["seawater-ph"], better="up", entities=["World", "Hawaii"], years=(1988, 2100),
         en="Ocean surface pH", es="pH de la superficie del océano", unit="pH",
         note_en="Station ALOHA, Hawaii, the longest open-ocean record. The vertical axis does not start at zero; lower pH is a more acidic ocean.",
         note_es="Estación ALOHA, Hawái, el registro más largo en mar abierto. El eje vertical no empieza en cero; un pH más bajo es un océano más ácido."),
    dict(id="so2", boundary="aerosols", slugs=["so-emissions-by-world-region-in-million-tonnes"], better="down", years=(1950, 2100),
         en="Sulphur dioxide emitted", es="Dióxido de azufre emitido", unit="t",
         note_en="The main source of the aerosols that pollute the air. Global aerosol loading is in the safe zone, though regions such as South Asia exceed it.",
         note_es="La principal fuente de los aerosoles que contaminan el aire. La carga global está en zona segura, aunque regiones como el sur de Asia la superan."),
]


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "genius-decision-open world indicators"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def noaa(years):
    rows = [r for r in csv.reader(io.StringIO(get(NOAA_CO2))) if r and not r[0].startswith("#")]
    points = [[int(r[0]), round(float(r[1]), 2)] for r in rows[1:] if years[0] <= int(r[0]) <= years[1]]
    return dict(column="mean (ppm)", points=points, chart="https://gml.noaa.gov/ccgg/trends/global.html",
                citation="NOAA Global Monitoring Laboratory, global annual mean CO₂", updated=None, entity="World")


def grapher(slug, total=False, years=(0, 9999), entities=("World",), scale=1):
    text = get(f"{GRAPHER}{slug}.csv?v=1&csvType=full&useColumnShortNames=false")
    rows = list(csv.reader(io.StringIO(text)))
    header, body = rows[0], rows[1:]
    entity = next((e for e in entities if any(r[0] == e for r in body)), None)
    if entity is None:
        raise ValueError(f"no {entities} row; entities like {sorted({r[0] for r in body})[:8]}")
    # Entity, Code, Year (or Day), value columns...: one column, or a stacked chart whose total is the sum.
    # Daily series are averaged per year.
    when = next(i for i, h in enumerate(header) if h in ("Year", "Day", "Date"))
    first = when + 1
    by_year = {}
    for r in body:
        if r[0] != entity or not r[when]:
            continue
        cells = [c.strip() for c in (r[first:] if total else r[first:first + 1])]
        year = int(r[when][:4])
        if any(cells) and years[0] <= year <= years[1]:
            by_year.setdefault(year, []).append(sum(float(c) for c in cells if c))
    points = [[y, round(sum(v) / len(v) * scale, 4)] for y, v in by_year.items()]
    if len(points) < 2:
        raise ValueError(f"only {len(points)} points for {entity}")
    meta = json.loads(get(f"{GRAPHER}{slug}.metadata.json"))
    column = next(iter(meta.get("columns", {}).values()), {})
    return dict(column="total of " + ", ".join(header[first:]) if total else header[first], points=sorted(points), chart=f"{GRAPHER}{slug}",
                citation=column.get("citationShort") or column.get("citationLong"), source_unit=column.get("unit"),
                updated=column.get("lastUpdated"), entity=entity)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result, failures = [], []
    keep = lambda item: {k: v for k, v in item.items() if k not in ("slugs", "total", "years", "entities", "source", "scale")}
    for item in INDICATORS:
        years = item.get("years", (0, 9999))
        if item.get("source") == "noaa":
            try:
                result.append({**keep(item), **noaa(years)})
            except Exception as error:
                failures.append(f"noaa: {error}")
            continue
        for slug in item["slugs"]:
            try:
                data = grapher(slug, item.get("total", False), years, item.get("entities", ("World",)), item.get("scale", 1))
            except Exception as error:  # report and try the next candidate
                failures.append(f"{slug}: {error}")
                continue
            result.append({**keep(item), **data})
            break
    out = dict(source="Our World in Data (ourworldindata.org) and NOAA", indicators=result)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(out, handle, ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False))
    for failure in failures:
        print("FAILED", failure, file=sys.stderr)


if __name__ == "__main__":
    main()
