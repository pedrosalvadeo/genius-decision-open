"""Read two official reports and prepare a system-linked investigation mission.

This is a deterministic, domain-specific scout. It neither searches the whole
web nor derives a causal model from prose. Remote text is data, never a command.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
import unicodedata
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from genius_twin import systems

BASE = 'https://www.irrigacion.gov.ar/web/2026/10/02/'
SOURCES = {
    'forecast': BASE + 'informe-de-la-situacion-hidrica-a-partir-del-pronostico-de-escurrimientos-temporada-2026-2027/',
    'context': BASE + 'pronostico/',
}
PUBLICATION_DATE = '2026-10-02'
BODY_LIMIT = 524288
MAX_AGE_DAYS = 45


def now():
    return datetime.now(timezone.utc).isoformat(timespec='microseconds')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def stamp(value):
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Timestamp needs a timezone')
    return result


def contract():
    return dict(format='genius-public-source-contract/1', adapter='mendoza_water_v1',
        urls=SOURCES, publication_date=PUBLICATION_DATE, season='2026-2027',
        geography='Río Mendoza, sección Guido; broader boundaries are hypotheses',
        method='GET', redirects='REJECT', retries=0, requests_per_run=2,
        body_limit_bytes=BODY_LIMIT, socket_timeout_seconds=15,
        read_budget_seconds=30, review_after_publication_days=MAX_AGE_DAYS,
        extraction='VERSIONED_RULES_REJECT_AMBIGUOUS_OR_UNSUPPORTED_CONTENT',
        credentials='NONE', external_effects='NONE', schedule='ON_DEMAND')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


class Article(HTMLParser):
    """Only visible paragraphs and dates in one article, excluding executable tags."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.inside = False
        self.blocked = 0
        self.paragraph = None
        self.paragraphs = []
        self.dates = []
        self.articles = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'article':
            self.articles += 1
            self.inside = True
        if not self.inside:
            return
        if tag in ('script', 'style', 'template', 'noscript'):
            self.blocked += 1
        if self.blocked:
            return
        if tag == 'p':
            if self.paragraph is not None:
                raise ValueError('Nested paragraph')
            self.paragraph = []
        if tag == 'time':
            self.dates.append(dict(attrs).get('datetime', ''))

    def handle_endtag(self, tag):
        if self.blocked:
            if tag in ('script', 'style', 'template', 'noscript'):
                self.blocked -= 1
            return
        if tag == 'p' and self.paragraph is not None:
            self.paragraphs.append(' '.join(''.join(self.paragraph).split()))
            self.paragraph = None
        if tag == 'article':
            self.inside = False

    def handle_data(self, data):
        if self.inside and not self.blocked and self.paragraph is not None:
            self.paragraph.append(data)


def normalize(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', text.casefold())
                   if not unicodedata.combining(c))


def unique(rows, predicate):
    found = [row for row in rows if predicate(row)]
    if len(found) != 1:
        raise ValueError('Missing or ambiguous source assertion')
    return found[0]


def extract(key, raw):
    parser = Article()
    parser.feed(raw.decode('utf-8', errors='strict'))
    parser.close()
    if parser.articles != 1 or parser.inside or parser.blocked or parser.paragraph is not None:
        raise ValueError('Unrecognized article structure')
    if len(parser.dates) != 1 or stamp(parser.dates[0]).date().isoformat() != PUBLICATION_DATE:
        raise ValueError('Unexpected publication date')
    rows = [normalize(p) for p in parser.paragraphs]
    if key == 'forecast':
        row = unique(rows, lambda p: p.startswith('rio mendoza:'))
        match = re.fullmatch(
            r'rio mendoza:.*?humedo\..*?25/26\s+escurrieron\s+(\d{1,5})\s+hm\s*3\..*?'
            r'2026-2027.*?derrame de\s+(\d{1,5})\s+hm3,.*?'
            r'(\d{1,3})%.*?guido\.', row)
        if not match:
            raise ValueError('Unsupported forecast statement')
        previous, forecast, percent = map(int, match.groups())
        if not 0 < previous <= 10000 or not 0 < forecast <= 10000 or not 100 < percent <= 300:
            raise ValueError('Values outside reviewed wet-season contract')
        return dict(basin='Mendoza', station='Guido', unit='hm3',
            previous_season='2025-2026', previous_reported_runoff=previous,
            forecast_season='2026-2027', forecast_runoff=forecast,
            forecast_percent_of_historical_mean=percent, classification='wet',
            basis='REPORTED_NOT_INDEPENDENTLY_MEASURED')
    if key == 'context':
        low = unique(rows, lambda p: 'reservas bajas' in p)
        timing = unique(rows, lambda p: 'cada dia' in p and 'ese dato no lo tenemos' in p)
        if 'empezar la temporada' not in low or 'estadisticas' not in timing:
            raise ValueError('Unsupported seasonal context')
        return dict(starting_reserves='reported_low',
            daily_availability='NOT_ESTABLISHED_BY_ANNUAL_FORECAST',
            basis='REPORTED_NOT_INDEPENDENTLY_MEASURED')
    raise ValueError('Unknown source')


def collect(key, *, opener=None, clock=now, monotonic=time.monotonic):
    url = SOURCES[key]  # no caller-supplied URL or remote instructions
    receipt = dict(source_id=key, url=url, started_at=clock(),
        source_contract_sha256=digest(contract()), http_status=None,
        response_sha256=None, response_bytes=0, facts=None, failure=None)
    raw = b''
    started = monotonic()
    try:
        req = Request(url, headers={'Accept':'text/html', 'Accept-Encoding':'identity',
            'User-Agent':'Genius-Public-Explorer/1 (+https://github.com/pedrosalvadeo/genius-decision-open)'})
        with (opener or build_opener(NoRedirect())).open(req, timeout=15) as response:
            receipt['http_status'] = response.status
            if response.status != 200 or response.geturl() != url:
                raise ValueError('Unexpected HTTP response')
            if response.headers.get_content_type() != 'text/html' or response.headers.get('Content-Encoding', 'identity') != 'identity':
                raise ValueError('Unsupported content type or encoding')
            while len(raw) <= BODY_LIMIT:
                chunk = response.read(min(8192, BODY_LIMIT + 1 - len(raw)))
                raw += chunk
                if monotonic() - started > 30:
                    raise ValueError('Read budget exceeded')
                if not chunk:
                    break
            if len(raw) > BODY_LIMIT:
                raise ValueError('Body limit exceeded')
        receipt['facts'] = extract(key, raw)
    except HTTPError as exc:
        receipt['http_status'], receipt['failure'] = exc.code, 'HTTP_ERROR'
        exc.close()
    except (URLError, OSError, TimeoutError):
        receipt['failure'] = 'TRANSPORT_FAILURE'
    except (ValueError, UnicodeError):
        receipt['failure'] = 'SOURCE_CONTRACT_MISMATCH'
    receipt.update(completed_at=clock(), response_bytes=len(raw),
        response_sha256=hashlib.sha256(raw).hexdigest() if raw else None)
    if stamp(receipt['completed_at']) < stamp(receipt['started_at']):
        receipt['failure'] = 'CLOCK_REVERSED'
    if receipt['failure']:
        receipt['facts'] = None
    receipt['outcome'] = 'REJECTED' if receipt['failure'] else 'OBSERVED'
    return receipt


UNKNOWNS = [
    'Reservas actuales, capacidad útil, caudales y demandas por intervalo; fecha y unidad de cada medición.',
    'Pérdidas, retornos, calidad del agua y demoras; relaciones causales contrastadas para cada alternativa.',
    'Identidad y límites de los sistemas; personas y seres vivos afectados, sin duplicarlos entre grupos.',
    'Condiciones de vida, bienestar y restricciones de cada portador, incluidos efectos aguas abajo.',
    'Escenarios, probabilidades justificadas, horizonte y criterios del cálculo Genius.',
    'Responsable operativo, permisos, costos, capacidad de ejecución y reversión de cada intervención.',
]


def observation(receipts):
    first = min(r['started_at'] for r in receipts)
    last = max(r['completed_at'] for r in receipts)
    by_id = {r['source_id']: r for r in receipts}
    f = by_id['forecast']['facts']
    evidence = [dict(id='forecast', observed_at=by_id['forecast']['completed_at'],
        source=SOURCES['forecast'], basis='reported',
        statement=f"Guido: {f['previous_reported_runoff']} hm³ informados para 2025–2026; "
            f"{f['forecast_runoff']} hm³ pronosticados para 2026–2027 ({f['forecast_percent_of_historical_mean']}% de la media).",
        uncertainty='Informe de tercero, publicado 2026-10-02; el pronóstico no es volumen disponible hoy ni probabilidad.'),
        dict(id='context', observed_at=by_id['context']['completed_at'], source=SOURCES['context'],
            basis='reported', statement='La temporada inicia con reservas bajas; el volumen anual previsto no determina el suministro diario.',
            uncertainty='Declaración regional fechada, sin serie diaria ni medición actual de un embalse concreto.'),
        dict(id='scope_hypothesis', observed_at=last, source='Genius mendoza_water_v1: hipótesis explícita del adaptador',
            basis='inference', statement='Se propone estudiar almacenamiento y distribución junto a comunidades, agroecosistemas y vida aguas abajo.',
            uncertainty='Topología y agrupaciones por verificar; no representan un inventario de personas o especies ni acreditan jurisdicción.')]
    rows = [
        ('river', 'Agua del río Mendoza en Guido', 'resource', 'forecast'),
        ('storage', 'Agua almacenada: inventario por relevar', 'resource', 'scope_hypothesis'),
        ('distribution', 'Red de distribución: límites por relevar', 'physical', 'scope_hypothesis'),
        ('dgi', 'Departamento General de Irrigación: fuente del informe', 'organization', 'context'),
        ('communities', 'Personas dependientes: identidades por relevar', 'living', 'scope_hypothesis'),
        ('agroecosystem', 'Vida en agroecosistemas: inventario por relevar', 'living', 'scope_hypothesis'),
        ('downstream', 'Vida aguas abajo: inventario por relevar', 'living', 'scope_hypothesis'),
    ]
    links = [('river','storage','supplies'), ('storage','distribution','supplies'),
        ('distribution','communities','supplies'), ('distribution','agroecosystem','supplies'),
        ('distribution','downstream','affects'), ('dgi','distribution','organizes')]
    return dict(format=systems.FORMAT, label='Exploración hídrica Mendoza 2026–2027',
        window=dict(start=first, end=last), evidence=evidence,
        entities=[dict(id=i,label=label,kind=kind,evidence_ids=[e]) for i,label,kind,e in rows],
        relations=[dict(id=f'link.{i}',source=a,target=b,kind=k,evidence_ids=['scope_hypothesis'])
                   for i,(a,b,k) in enumerate(links)], unknowns=UNKNOWNS.copy())


def prepare(receipts, *, created_at=None):
    created_at = created_at or now()
    result = dict(format='genius-public-exploration/1', created_at=created_at,
        source_contract=contract(), receipts=receipts,
        adapter_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        calculation_status='NOT_READY', life_sustaining_probability=None,
        selected_intervention=None, external_actions_executed=[],
        schedule='ON_DEMAND', status='SOURCE_REVIEW_REQUIRED')
    if len(receipts) != 2 or {r['source_id'] for r in receipts} != set(SOURCES):
        raise ValueError('Exactly one receipt per source required')
    for r in receipts:
        if r['url'] != SOURCES[r['source_id']] or r['source_contract_sha256'] != digest(contract()):
            raise ValueError('Receipt contract mismatch')
    if any(r['outcome'] != 'OBSERVED' or not r['facts'] for r in receipts):
        return result
    observed = observation(receipts)
    recognition = systems.recognize(observed)
    age = (stamp(created_at).date() - datetime.fromisoformat(PUBLICATION_DATE).date()).days
    fresh = 0 <= age <= MAX_AGE_DAYS
    f = next(r['facts'] for r in receipts if r['source_id'] == 'forecast')
    delta = f['forecast_runoff'] - f['previous_reported_runoff']
    result.update(status='INVESTIGATION_PREPARED' if fresh else 'SOURCE_REFRESH_REQUIRED',
        source_age_days=age, observation=observed, recognition=recognition,
        boundary_hypothesis=systems.boundary(observed, ['river','storage','distribution','dgi']),
        authorized_intervention_entities=[],
        arithmetic=dict(kind='DESCRIPTIVE_ONLY', forecast_minus_prior_reported_hm3=delta,
            forecast_over_prior_reported=str(Fraction(f['forecast_runoff'], f['previous_reported_runoff'])),
            meaning='Compara una previsión anual con un volumen anual informado; no mide mejora, agua libre ni PVS.'),
        mission=dict(id='mendoza.water.2026-2027',
            objective='Investigar cómo sostener abastecimiento y condiciones de vida durante la transición entre reservas bajas y un año previsto húmedo.',
            trigger='LOW_STARTING_RESERVES_AND_WET_ANNUAL_FORECAST',
            trigger_basis='DECLARED_DOMAIN_RULE_NOT_AN_OPTIMAL_PRIORITY_RANKING',
            candidate_routes=[
                dict(id='baseline', description='Reconstruir la operación vigente como referencia.',
                    requires=['Series actuales y reglas de operación verificadas.']),
                dict(id='loss_reduction', description='Evaluar reparación localizada de pérdidas, si se confirma su existencia.',
                    requires=['Pérdida medida, retornos afectados, costo, plazo y responsable.']),
                dict(id='timing', description='Comparar secuencias de almacenamiento y distribución con las condiciones de todos los afectados.',
                    requires=['Caudales por intervalo, capacidades, demandas, restricciones y efectos aguas abajo.']),
            ], missing_data=UNKNOWNS.copy(),
            next_action='Delimitar con un responsable un tramo o instalación y obtener series observadas; construir y revisar el modelo antes de ordenar rutas.',
            measurement_plan=dict(baseline='Mismos puntos, unidades e intervalos antes y después; registrar clima y demanda.',
                outcomes=['Disponibilidad y calidad del agua.', 'Cumplimiento de condiciones por portador, incluidos los de aguas abajo.',
                    'Pérdidas y retornos medidos, costos y efectos no deseados.'],
                attribution='Contrastar predicciones y alternativas; una variación temporal aislada no prueba causalidad.',
                stop='Detener y revisar ante datos inválidos, incumplimiento de condiciones acordadas o pérdida de autorización.')))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='New directory; existing evidence is never overwritten')
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    receipts = [collect(key) for key in SOURCES]
    result = prepare(receipts)
    (args.out / 'exploration.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    if 'observation' in result:
        (args.out / 'observation.json').write_text(json.dumps(result['observation'], ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(status=result['status'], calculation_status=result['calculation_status'],
        receipt_sha256=digest(result), external_actions_executed=0)))
    return 0 if result['status'] == 'INVESTIGATION_PREPARED' else 2


if __name__ == '__main__':
    raise SystemExit(main())
