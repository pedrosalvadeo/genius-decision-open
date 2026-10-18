"""Harvest water-year unregulated inflow to Lake Powell from Reclamation's RISE (item 4301).

RISE item 4301 is the daily total unregulated inflow to Lake Powell in acre-feet, from
June 1963. This script pages through the RISE results API, sums each complete water year
(October to September) and writes one row per year. Deterministic: no gap filling; a
water year missing any day is left out and reported.

Run (needs network):
  python twin/history/rise_inflow.py --out twin/history/lake_mead/powell_unregulated_wy.csv
"""
import argparse
import csv
from datetime import date, timedelta
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.parse
import urllib.request

API = 'https://data.usbr.gov/rise/api/result'
ITEM = 4301


def get(params):
    url = API + '?' + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            request = urllib.request.Request(url, headers={'Accept': 'application/vnd.api+json', 'User-Agent': 'genius-history-node'})
            with urllib.request.urlopen(request, timeout=120) as response:
                raw = response.read()
            return url, raw, json.loads(raw)
        except Exception as exc:  # network errors are retried, then reported
            if attempt == 3:
                raise SystemExit(f'{url}: {exc}')
            time.sleep(2 ** (attempt + 1))


def daily(first, last):
    values, digest, page = {}, hashlib.sha256(), 1
    while True:
        url, raw, body = get({'itemId': ITEM, 'dateTime[after]': first.isoformat(), 'dateTime[before]': last.isoformat(),
                              'order[dateTime]': 'ASC', 'itemsPerPage': 10000, 'page': page})
        digest.update(raw)
        rows = body.get('data', [])
        if page == 1 and not rows:
            raise SystemExit(f'no data from {url}: {raw[:500]!r}')
        for row in rows:
            attributes = row.get('attributes', {})
            if attributes.get('result') is not None:
                values[date.fromisoformat(str(attributes['dateTime'])[:10])] = Fraction(str(attributes['result']))
        if len(rows) < 10000:
            return values, digest.hexdigest(), url
        page += 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--first-wy', type=int, default=1964)
    parser.add_argument('--last-wy', type=int, default=2025)
    parser.add_argument('--out', required=True)
    args = parser.parse_args(argv)
    # RISE treats dateTime[before] as exclusive, so ask for one day past the last water year.
    values, digest, url = daily(date(args.first_wy - 1, 10, 1), date(args.last_wy, 10, 1))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    missing = {}
    with out.open('w', newline='') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['water_year', 'days', 'unregulated_inflow_af'])
        for wy in range(args.first_wy, args.last_wy + 1):
            days = [date(wy - 1, 10, 1) + timedelta(n) for n in range((date(wy, 9, 30) - date(wy - 1, 10, 1)).days + 1)]
            absent = [d for d in days if d not in values]
            if absent:
                missing[wy] = len(absent)
                continue
            writer.writerow([wy, len(days), round(sum(values[d] for d in days))])
    meta = dict(source='Reclamation RISE item 4301, Lake Powell daily unregulated inflow (acre-feet)', last_url=url,
                responses_sha256=digest, method='Sum of daily values over each complete water year (Oct-Sep)', incomplete_years=missing)
    out.with_suffix('.json').write_text(json.dumps(meta, indent=1) + '\n')
    print(out.read_text())
    print(json.dumps(meta), file=sys.stderr)


if __name__ == '__main__':
    main()
