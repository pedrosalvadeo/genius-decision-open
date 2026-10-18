"""Probe the national hydrological system's monthly series workbook (SNIH, 1931-2020).

Prints each sheet's name, size and first rows, and every row naming a station or river
of interest, so a harvester can be written against the real layout.
Run (needs network and openpyxl): python twin/history/snih_probe.py out/snih_mensuales.xlsx Guido Mendoza
"""
import sys
import urllib.request

import openpyxl

URL = 'https://snih.hidricosargentina.gob.ar/Info/SeriesMensuales_1931_2020.xlsx'


def main(path, *needles):
    request = urllib.request.Request(URL, headers={'User-Agent': 'genius-history-node'})
    with urllib.request.urlopen(request, timeout=300) as response, open(path, 'wb') as out:
        out.write(response.read())
    book = openpyxl.load_workbook(path, read_only=True, data_only=True)
    for sheet in book.worksheets:
        print(f'== sheet {sheet.title!r} rows={sheet.max_row} cols={sheet.max_column}')
        hits = 0
        for i, row in enumerate(sheet.iter_rows(values_only=True)):
            cells = ['' if c is None else str(c) for c in row]
            line = ' | '.join(cells)[:400]
            if i < 6:
                print(f'{i}: {line}')
            elif hits < 40 and any(n.lower() in line.lower() for n in needles):
                hits += 1
                print(f'{i}: {line}')


if __name__ == '__main__':
    main(*sys.argv[1:])
