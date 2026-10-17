"""Harvest Lake Mead and Lake Powell tables from Reclamation's Lower Colorado 24-Month Studies.

Downloads each study PDF, converts it with `pdftotext -layout` and parses the end-of-month
elevation and storage rows of the Hoover Dam - Lake Mead and Glen Canyon Dam - Lake Powell
tables. Deterministic: no estimation, no language model. PDFs are not kept; their SHA-256 is.

Run (needs network and poppler-utils):
  python twin/history/reclamation_24mo.py --from 2009-01 --to 2026-10 --out twin/history/lake_mead/studies.csv
"""
import argparse
import csv
from datetime import date
import hashlib
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

BASE = 'https://www.usbr.gov/lc/region/g4000/'
MONTHS = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
# Suffix -> scenario name used by twin/history/hindcast.py; 6/7 maf variants are kept apart.
VARIANTS = {'': 'most_probable', '_MIN': 'min', '_MAX': 'max', '_6': 'most_probable_6', '_7': 'most_probable_7'}
CURRENT = {'': '24mo.pdf', '_MIN': '24mo_MIN.pdf', '_MAX': '24mo_MAX.pdf', '_6': '24mo_6.pdf', '_7': '24mo_7.pdf'}
LAKES = {'mead': (re.compile(r'hoover\s+dam|lake\s+mead', re.I), (800, 1250)),
         'powell': (re.compile(r'glen\s+canyon|lake\s+powell', re.I), (3300, 3720))}
# Rows may carry a margin letter (the vertical "HISTORY" label) or a "*" before the month.
ROW = re.compile(r'^\s*(?:[A-Z*]\s+)?(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\-/]*\'?(\d{4}|\d{2})\b(.*)$', re.I)
NUMBER = re.compile(r'-?\d[\d,]*(?:\.\d+)?')
FIELDS = ['study_date', 'scenario', 'source_url', 'pdf_sha256', 'row_month', 'lake', 'elevation_ft', 'storage_kaf', 'kind']


def month_key(year, month):
    return f'{year:04d}-{month:02d}'


def urls(year, month, current=None):
    """Archive URLs for a study; the current month's study lives at the root."""
    stem = f'{MONTHS[month - 1]}{year % 100:02d}'
    for suffix, scenario in VARIANTS.items():
        if current == (year, month):
            yield scenario, BASE + CURRENT[suffix]
        yield scenario, f'{BASE}24mo/{year}/{stem}{suffix}.pdf'


def _heading(lines, index):
    """A table heading: a short line without digits followed within six lines by a units line."""
    text = lines[index].strip()
    if not text or len(text) > 60 or re.search(r'\d', text):
        return False
    return any('Ac-Ft' in lines[j] for j in range(index + 1, min(index + 7, len(lines))))


def _positions(headers, phrases):
    """Character centres of every occurrence of the header phrases."""
    out = []
    for line in headers:
        for phrase in phrases:
            out += [m.start() + len(phrase) / 2 for m in re.finditer(re.escape(phrase), line)]
    return sorted(out)


def _columns(headers):
    """(elevation, storage) centres. Elevation sits under its unit, "(Ft)" or "Feet". End-of-month
    storage is the first "EOM" or "End Of Month" header to the right of the elevation that is not
    the elevation's own label, so bank storage and Lees Ferry columns are skipped in every layout."""
    elevations = _positions(headers, ['(Ft)', 'Feet'])
    if not elevations:
        return None, None
    elevation = elevations[0]
    storage = next((p for p in _positions(headers, ['EOM', 'End Of Month']) if p > elevation + 6), None)
    return elevation, storage


def parse(text, study):
    """Rows (lake, row_month, elevation, storage) from pdftotext -layout output of one study.

    Columns are located by their headers (see `_columns`), so extra columns such as bank
    storage or Lees Ferry do not shift the values. Layouts from 2009 to 2026 differ in labels,
    units lines and margin letters; tests cover one excerpt of each.
    """
    lines = text.splitlines()
    out, seen = [], set()
    lake, headers, columns = None, [], None
    for index, line in enumerate(lines):
        match = ROW.match(line)
        if not match:
            if _heading(lines, index):
                lake = next((name for name, (pattern, _) in LAKES.items() if pattern.search(line)), None)
                headers, columns = [], None
            elif lake is not None and columns is None and line.strip():
                headers.append(line)
            continue
        if lake is None:
            continue
        if columns is None:
            columns = _columns(headers)
        elevation_at, storage_at = columns
        if elevation_at is None or storage_at is None:
            continue
        tokens = [(m.group().replace(',', ''), (m.start() + m.end()) / 2) for m in NUMBER.finditer(line, match.start(3))]
        if len(tokens) < 2:
            continue
        elevation = min(tokens, key=lambda t: abs(t[1] - elevation_at))[0]
        storage = min(tokens, key=lambda t: abs(t[1] - storage_at))[0]
        low, high = LAKES[lake][1]
        if '.' not in elevation or '.' in storage or not low <= float(elevation) <= high:
            continue  # not an end-of-month row of this table
        year = int(match.group(2))
        year = year + 2000 if year < 100 else year
        month = [m.lower() for m in MONTHS].index(match.group(1)[:3].lower()) + 1
        key = (lake, month_key(year, month))
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(lake=lake, row_month=key[1], elevation_ft=elevation, storage_kaf=str(int(storage)),
                        kind='historical' if key[1] < study else 'projected'))
    return out


MONTH_NAMES = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']


def issued(text, year, month):
    """The study names its own month near the top; a stale or misfiled PDF does not."""
    return f'{MONTH_NAMES[month - 1]} {year}'.lower() in ' '.join(text[:3000].split()).lower()


def fetch(url, attempts=3):
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'genius-decision-open history node'})
            with urllib.request.urlopen(request, timeout=60) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return None
            time.sleep(2 ** attempt)
        except urllib.error.URLError:
            time.sleep(2 ** attempt)
    return None


def to_text(data):
    with tempfile.NamedTemporaryFile(suffix='.pdf') as pdf:
        pdf.write(data)
        pdf.flush()
        return subprocess.run(['pdftotext', '-layout', pdf.name, '-'], check=True, capture_output=True, text=True).stdout


def harvest(start, end, out, failures, pause=0.3, today=None, samples=None):
    """`samples`: a folder that receives the text of the first unparsed study per year and scenario."""
    today = today or date.today()
    current = (today.year, today.month)
    rows, missing, sampled = [], [], set()
    year, month = start
    while (year, month) <= end:
        study = month_key(year, month)
        done = set()
        for scenario, url in urls(year, month, current):
            if scenario in done:
                continue
            data = fetch(url)
            time.sleep(pause)
            if data is None:
                missing.append(f'{url} not found')
                continue
            text = to_text(data)
            if not issued(text, year, month):
                missing.append(f'{url} does not name {study} at the top')
                continue
            parsed = parse(text, study)
            if not any(r['lake'] == 'mead' for r in parsed):
                missing.append(f'{url} no Lake Mead rows parsed')
                if samples and (year, scenario) not in sampled:
                    sampled.add((year, scenario))
                    Path(samples).mkdir(parents=True, exist_ok=True)
                    Path(samples, f'{study}_{scenario}.txt').write_text(text)
                continue
            done.add(scenario)
            digest = hashlib.sha256(data).hexdigest()
            rows += [dict(study_date=study, scenario=scenario, source_url=url, pdf_sha256=digest, **r) for r in parsed]
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    with open(out, 'w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    Path(failures).write_text(''.join(line + '\n' for line in missing))
    return rows, missing


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--from', dest='start', required=True, help='YYYY-MM')
    parser.add_argument('--to', dest='end', required=True, help='YYYY-MM')
    parser.add_argument('--out', required=True)
    parser.add_argument('--failures', default=None)
    parser.add_argument('--samples', default=None, help='folder for the text of unparsed studies')
    args = parser.parse_args(argv)
    start = tuple(int(x) for x in args.start.split('-'))
    end = tuple(int(x) for x in args.end.split('-'))
    rows, missing = harvest(start, end, args.out, args.failures or args.out + '.failures.txt', samples=args.samples)
    studies = len({(r['study_date'], r['scenario']) for r in rows})
    print(f'{studies} study files, {len(rows)} rows, {len(missing)} missing or unparsed', file=sys.stderr)


if __name__ == '__main__':
    main()
