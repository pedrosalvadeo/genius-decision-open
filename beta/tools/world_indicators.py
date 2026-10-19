"""Download the world indicators the home page charts, with their sources.

Each series is the World row of an Our World in Data chart; OWID republishes the
primary source named in each entry (World Bank, UN IGME, Ember, UNEP). Run on a
machine with open internet (the "World indicators" GitHub workflow does) and commit
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

# slug candidates are tried in order; the first that answers with a World series wins.
INDICATORS = [
    dict(id="poverty", slugs=["share-of-population-in-extreme-poverty"], better="down", years=(1990, 2024),
         note_en="Below $3 a day (2021 prices). The latest years are World Bank nowcasts.",
         note_es="Menos de 3 dólares por día (precios de 2021). Los últimos años son estimaciones del Banco Mundial.",
         en="People living in extreme poverty", es="Personas en pobreza extrema", unit="%"),
    dict(id="child_mortality", slugs=["child-mortality"], better="down", years=(1950, 2100),
         en="Children who die before age five", es="Niños que mueren antes de los cinco años", unit="%"),
    dict(id="solar_wind", slugs=["share-electricity-solar-wind", "share-of-electricity-production-from-solar-and-wind"], better="up", years=(2000, 2100),
         en="Electricity from solar and wind", es="Electricidad solar y eólica", unit="%"),
    dict(id="ozone", slugs=["ozone-depleting-substance-consumption", "consumption-of-ozone-depleting-substances"], better="down", total=True, years=(1989, 2100),
         note_en="All controlled substances, weighted by their ozone-depleting potential.",
         note_es="Todas las sustancias controladas, ponderadas por su potencial de agotar el ozono.",
         en="Consumption of ozone-depleting substances", es="Consumo de sustancias que agotan el ozono", unit="t ODP"),
    dict(id="electricity_access", slugs=["share-of-the-population-with-access-to-electricity"], better="up",
         en="People with access to electricity", es="Personas con acceso a electricidad", unit="%"),
]


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "genius-decision-open world indicators"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def series(slug, total=False, years=(0, 9999)):
    text = get(f"{GRAPHER}{slug}.csv?v=1&csvType=full&useColumnShortNames=false")
    rows = list(csv.reader(io.StringIO(text)))
    header, body = rows[0], rows[1:]
    world = [r for r in body if r[0] == "World"]
    if not world:
        raise ValueError(f"no World row; entities like {sorted({r[0] for r in body})[:5]}")
    # Entity, Code, Year, value columns...: one column, or a stacked chart whose total is the sum.
    points = []
    for r in world:
        cells = [c.strip() for c in (r[3:] if total else r[3:4])]
        if any(cells) and years[0] <= int(r[2]) <= years[1]:
            points.append([int(r[2]), round(sum(float(c) for c in cells if c), 3)])
    meta = json.loads(get(f"{GRAPHER}{slug}.metadata.json"))
    column = next(iter(meta.get("columns", {}).values()), {})
    return dict(column="total of " + ", ".join(header[3:]) if total else header[3], points=sorted(points), chart=f"{GRAPHER}{slug}",
                title=meta.get("chart", {}).get("title"),
                citation=column.get("citationShort") or column.get("citationLong"),
                unit=column.get("unit"), description=column.get("descriptionShort"),
                updated=column.get("lastUpdated"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    result, failures = [], []
    for item in INDICATORS:
        for slug in item["slugs"]:
            try:
                data = series(slug, item.get("total", False), item.get("years", (0, 9999)))
            except Exception as error:  # report and try the next candidate
                failures.append(f"{slug}: {error}")
                continue
            entry = {k: v for k, v in item.items() if k not in ("slugs", "total", "years")}
            entry.update(data)
            result.append(entry)
            break
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(dict(source="Our World in Data (ourworldindata.org)", indicators=result), handle, ensure_ascii=False, indent=1)
    print(json.dumps(dict(source="Our World in Data (ourworldindata.org)", indicators=result), ensure_ascii=False))
    for failure in failures:
        print("FAILED", failure, file=sys.stderr)


if __name__ == "__main__":
    main()
