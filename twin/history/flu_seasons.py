"""Harvest the peak of each US influenza season (CDC ILINet, via the Delphi Epidata API).

The driver for winter health-supply twins: the national weighted percentage of
outpatient visits for influenza-like illness (wILI), one value per week. A season runs
from epidemiological week 40 to week 20 of the next year (October to May, the window
ILINet reported every year since 1997); its value is the weekly peak in that window.
Seasons missing weeks are left out and reported. Deterministic, no gap filling.

Run (needs network):
  python twin/history/flu_seasons.py --out twin/history/blood_2026/flu_peak_wili.csv
"""
import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.parse
import urllib.request

API = 'https://api.delphi.cmu.edu/epidata/fluview/'


def weeks(first_season, last_season):
    url = API + '?' + urllib.parse.urlencode({'regions': 'nat', 'epiweeks': f'{first_season}40-{last_season + 1}39'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'genius-history-node'}), timeout=120) as response:
                raw = response.read()
            body = json.loads(raw)
            if body.get('result') != 1:
                raise SystemExit(f'{url}: {body.get("message")}')
            return url, hashlib.sha256(raw).hexdigest(), body['epidata']
        except SystemExit:
            raise
        except Exception as exc:  # network errors are retried, then reported
            if attempt == 3:
                raise SystemExit(f'{url}: {exc}')
            time.sleep(2 ** (attempt + 1))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--first-season', type=int, default=1997)
    parser.add_argument('--last-season', type=int, default=2025)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    url, digest, rows = weeks(args.first_season, args.last_season)
    by_season = {}
    for row in rows:
        year, week = divmod(int(row['epiweek']), 100)
        season = year if week >= 40 else year - 1
        if 20 < week < 40:
            continue
        if row.get('wili') is not None:
            by_season.setdefault(season, []).append((int(row['epiweek']), Fraction(str(row['wili']))))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    short = {}
    with out.open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['season', 'weeks', 'peak_wili', 'peak_epiweek'])
        for season in range(args.first_season, args.last_season + 1):
            found = by_season.get(season, [])
            if len(found) < 33:
                short[season] = len(found)
                continue
            week, peak = max(found, key=lambda pair: (pair[1], -pair[0]))
            writer.writerow([f'{season}/{season + 1}', len(found), f'{float(peak):.5f}'.rstrip('0').rstrip('.'), week])
    meta = dict(source='CDC ILINet national weighted ILI (%), via Delphi Epidata fluview', url=url, response_sha256=digest,
                method='Weekly peak of wILI over each season (epiweek 40 to 20)', incomplete_seasons=short)
    out.with_suffix('.json').write_text(json.dumps(meta, indent=1) + '\n')
    print(out.read_text())
    print(json.dumps(meta), file=sys.stderr)


if __name__ == '__main__':
    main()
