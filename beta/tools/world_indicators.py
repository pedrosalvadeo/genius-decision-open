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
    dict(id="poverty", slugs=["share-of-population-in-extreme-poverty"], better="down",
         en="People living in extreme poverty", es="Personas en pobreza extrema", unit="%"),
    dict(id="child_mortality", slugs=["child-mortality"], better="down",
         en="Children who die before age five", es="Niños que mueren antes de los cinco años", unit="%"),
    dict(id="solar_wind", slugs=["share-electricity-solar-wind", "share-of-electricity-production-from-solar-and-wind"], better="up",
         en="Electricity from solar and wind", es="Electricidad solar y eólica", unit="%"),
    dict(id="ozone", slugs=["ozone-depleting-substance-consumption", "consumption-of-ozone-depleting-substances"], better="down",
         en="Consumption of ozone-depleting substances", es="Consumo de sustancias que agotan el ozono", unit="t ODP"),
    dict(id="electricity_access", slugs=["share-of-the-population-with-access-to-electricity"], better="up",
         en="People with access to electricity", es="Personas con acceso a electricidad", unit="%"),
]


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "genius-decision-open world indicators"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def series(slug):
    text = get(f"{GRAPHER}{slug}.csv?v=1&csvType=full&useColumnShortNames=false")
    rows = list(csv.reader(io.StringIO(text)))
    header, body = rows[0], rows[1:]
    world = [r for r in body if r[0] == "World"]
    if not world:
        raise ValueError(f"no World row; entities like {sorted({r[0] for r in body})[:5]}")
    # Entity, Code, Year, value columns...; sum is wrong for multi-column charts, so take the first value column.
    points = []
    for r in world:
        value = r[3].strip() if len(r) > 3 else ""
        if value:
            points.append([int(r[2]), float(value)])
    meta = json.loads(get(f"{GRAPHER}{slug}.metadata.json"))
    column = next(iter(meta.get("columns", {}).values()), {})
    return dict(column=header[3], points=sorted(points), chart=f"{GRAPHER}{slug}",
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
                data = series(slug)
            except Exception as error:  # report and try the next candidate
                failures.append(f"{slug}: {error}")
                continue
            entry = {k: v for k, v in item.items() if k != "slugs"}
            entry.update(data)
            result.append(entry)
            break
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(dict(source="Our World in Data (ourworldindata.org)", indicators=result), handle, ensure_ascii=False, indent=1)
    print(json.dumps(result, ensure_ascii=False))
    for failure in failures:
        print("FAILED", failure, file=sys.stderr)


if __name__ == "__main__":
    main()
