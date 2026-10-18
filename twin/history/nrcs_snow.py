"""Harvest April 1 snow water equivalent for the basins that supply Denver Water from NRCS SNOTEL.

Denver Water collects snowmelt on both sides of the Divide: the Colorado headwaters and
the Blue River (West Slope) and the South Platte headwaters. This script asks the NRCS
Air and Water Database (AWDB) REST API for every Colorado SNOTEL station in those
watersheds that reported since 1991, reads each station's April 1 snow water equivalent
(WTEQ, inches) for every year, and computes the basin index the way NRCS does: the sum
of the stations' values over the sum of their 1991-2020 medians, only in years where
every kept station reported. Deterministic: no estimation, no gap filling.

Run (needs network):
  python twin/history/nrcs_snow.py --out twin/history/denver_snow/april1.csv
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
from statistics import median
import sys
import time
import urllib.parse
import urllib.request

API = 'https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/'
# Colorado headwaters (Fraser, Williams Fork), Blue River, South Platte headwaters, Upper South Platte.
HUCS = ('14010001', '14010002', '10190001', '10190002')
FIRST, NORMAL = 1991, (1991, 2020)


def get(path, params):
    url = API + path + '?' + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'genius-history-node'}), timeout=120) as response:
                raw = response.read()
            return url, raw, json.loads(raw)
        except Exception as exc:  # network errors are retried, then reported
            if attempt == 3:
                raise SystemExit(f'{url}: {exc}')
            time.sleep(2 ** (attempt + 1))


def stations(last_year):
    url, raw, rows = get('stations', dict(stationTriplets='*:CO:SNTL', returnForecastPointMetadata='false',
                                          returnReservoirMetadata='false', returnStationElements='false', activeOnly='true'))
    kept = [r for r in rows if str(r.get('huc') or '').startswith(HUCS) and str(r.get('beginDate', '9999'))[:10] <= f'{FIRST}-04-01']
    return url, hashlib.sha256(raw).hexdigest(), sorted(kept, key=lambda r: r['stationTriplet'])


def april_first(triplets, last_year):
    url, raw, rows = get('data', dict(stationTriplets=','.join(triplets), elements='WTEQ', duration='DAILY',
                                      beginDate=f'{FIRST}-04-01', endDate=f'{last_year}-04-01', periodRef='END'))
    values = {}
    for row in rows:
        for series in row.get('data', []):
            for v in series.get('values', []):
                if str(v.get('date', ''))[5:10] == '04-01' and v.get('value') is not None:
                    values[(row['stationTriplet'], int(v['date'][:4]))] = Fraction(str(v['value']))
    return url, hashlib.sha256(raw).hexdigest(), values


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--last-year', type=int, default=2026)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    station_url, station_sha, kept = stations(args.last_year)
    if not kept:
        raise SystemExit('no SNOTEL station found in the Denver Water watersheds')
    triplets = [r['stationTriplet'] for r in kept]
    data_url, data_sha, values = april_first(triplets, args.last_year)
    complete = [t for t in triplets if all((t, y) in values for y in range(NORMAL[0], NORMAL[1] + 1))]
    medians = {t: Fraction(median(values[(t, y)] for y in range(NORMAL[0], NORMAL[1] + 1))) for t in complete}
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['year', 'stations', 'swe_sum_in', 'median_sum_in', 'index_pct'])
        for year in range(FIRST, args.last_year + 1):
            if all((t, year) in values for t in complete):
                total, normal = sum(values[(t, year)] for t in complete), sum(medians.values())
                writer.writerow([year, len(complete), f'{float(total):.1f}', f'{float(normal):.1f}', f'{float(100 * total / normal):.1f}'])
    meta = dict(stations=[dict(triplet=r['stationTriplet'], name=r.get('name'), huc=r.get('huc'), begin=r.get('beginDate'),
                               used=r['stationTriplet'] in complete) for r in kept],
                normal_period=list(NORMAL), method='Sum of April 1 SWE over sum of 1991-2020 station medians, complete years only',
                sources=[dict(url=station_url, sha256=station_sha), dict(url=data_url, sha256=data_sha)])
    out.with_suffix('.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1) + '\n')
    print(out.read_text())
    print(json.dumps(meta['stations'], ensure_ascii=False), file=sys.stderr)


if __name__ == '__main__':
    main()
