"""Builds world.json for a first digital twin of the Earth, 2025-2105, from cited excerpts.

Run: python twin/cases/earth_2105/build.py
Same eight modules and kernel as the water and blood cases, at planetary scale. The
quotes come from public pages and are checked against the live pages by the history
node (twin/history/source_quotes.py with twin/history/earth_2026/quotes.json).
Every number that is not quoted is a hypothesis or decision claim, listed in README.md.
"""
from fractions import Fraction
import json
from pathlib import Path

SOURCES = [
    dict(id='phc', origin='Potsdam Institute for Climate Impact Research, "Seven of nine planetary boundaries now breached – ocean acidification joins the danger zone", 24/09/2025, https://www.pik-potsdam.de/en/news/latest-news/seven-of-nine-planetary-boundaries-now-breached-2013-ocean-acidification-joins-the-danger-zone',
         observed_at='2025-09-24T12:00:00+02:00', content='seven out of nine Planetary Boundaries have been breached'),
    dict(id='igcc', origin='University of Leeds, "Scientists find three years left of remaining carbon budget for 1.5C" (Forster et al. 2025, Indicators of Global Climate Change 2024), 19/06/2025, https://www.leeds.ac.uk/news/article/5801/scientists-find-three-years-left-of-remaining-carbon-budget-for-15-c ; and the paper, Earth System Science Data 17, 2641, 2025, https://essd.copernicus.org/articles/17/2641/2025/',
         observed_at='2025-06-19T12:00:00+01:00', content=' […] '.join([
             'central estimate of the remaining carbon budget for 1.5°C to be 130 billion tonnes of CO2 (from the beginning of 2025)',
             '1.52°C, of which 1.36°C can be attributed to human activity',
             'AR6 budgets were expressed from 2020 onwards, and approximately 200 Gt CO2 was emitted between 2020 and 2024'])),
    dict(id='ar6_budget', origin='IPCC AR6 WGI SPM Table SPM.2 (remaining carbon budgets from 1/1/2020), as tabulated by openclimatedata, https://openclimatedata.net/climate-spirals/carbon-budget/',
         observed_at='2021-08-09T12:00:00+00:00', content='2.0 °C: 1350 GtCO₂ (Median), 33%-67% range: 1150 - 1700 GtCO₂'),
    dict(id='ar6_scenarios', origin='IPCC AR6 WGI Chapter 1, p. 1-102, as quoted in https://scholar.colorado.edu/downloads/000001537',
         observed_at='2021-08-09T12:00:00+00:00', content='No likelihood is attached to the scenarios assessed in this Report'),
    dict(id='gcb', origin='Friedlingstein et al., "Global Carbon Budget 2025", Earth System Science Data 18, 3211, 2026, https://essd.copernicus.org/articles/18/3211/2026/',
         observed_at='2025-11-13T12:00:00+00:00', content='about 11.5 GtC (42.2 GtCO2), marginally below the 2024 level due to lower net land-use emissions'),
    dict(id='unep', origin='UNEP, Emissions Gap Report 2025, 04/11/2025, https://www.unep.org/en/publications/report/emissions-gap-report-2025',
         observed_at='2025-11-04T12:00:00+00:00', content='2.3-2.5°C based on full implementation of Nationally Determined Contributions (NDCs), while those based on current policies are 2.8°C'),
    dict(id='paris', origin='Paris Agreement, Article 2.1(a), as quoted by the Grantham Research Institute (LSE), https://www.lse.ac.uk/granthaminstitute/?p=53369',
         observed_at='2015-12-12T12:00:00+01:00', content='holding the increase in the global average temperature to well below 2°C above pre-industrial levels and pursuing efforts to limit the temperature increase to 1.5°C'),
    dict(id='fra', origin='FAO, Global Forest Resources Assessment 2025: Key findings, https://openknowledge.fao.org/server/api/core/bitstreams/2dee6e93-1988-4659-aa89-30dd20b43b15/content/FRA-2025/key-findings.html ; and FAO newsroom, "Global deforestation slows, but forests remain under pressure, FAO report shows", https://www.fao.org/newsroom/detail/global-deforestation-slows--but-forests-remain-under-pressure--fao-report-shows/en',
         observed_at='2025-10-21T12:00:00+02:00', content=' […] '.join([
             'The world has a total forest area of 4.14 billion hectares',
             'current rate of deforestation at 10.9 million hectares per year remains too high'])),
]
BY_ID = {s['id']: s for s in SOURCES}


def span(source_id, quote):
    content = BY_ID[source_id]['content']
    start = content.index(quote)
    return dict(source_id=source_id, start=start, end=start + len(quote), quote=quote)


def claim(id, basis, statement, uncertainty, spans=(), premises=()):
    return dict(id=id, basis=basis, statement=statement, uncertainty=uncertainty, spans=list(spans), premises=list(premises))


def q(x):
    x = Fraction(x)
    return f'{x.numerator}/{x.denominator}'


H = 8                                   # decades, 1 January 2025 to 1 January 2105
YEARS = 10
E0 = Fraction(422, 10)                  # GtCO2 per year in 2025, fossil plus land use
SPENT = 200                             # GtCO2 emitted 2020-2024
BUDGET_2020 = dict(low=1150, central=1350, high=1700)      # 2°C at 67 %, 50 % and 33 %
BUDGET = {k: v - SPENT for k, v in BUDGET_2020.items()}     # 950, 1150, 1500 from 2025
FOREST = 4140                           # Mha in 2025
DEFOREST = Fraction(109, 10)            # Mha per year, gross
NET_LOSS = Fraction(412, 100)           # Mha per year, net (FRA 2025)
EXPANSION = DEFOREST - NET_LOSS         # 6.78 Mha per year of forest gain, kept in every route
LEVELS = [Fraction(1), Fraction(3, 4), Fraction(1, 2), Fraction(1, 4), Fraction(0)]
ROUTES = [('fast', 'Bajar a cero en 2045', [Fraction(3, 4), Fraction(1, 4)]),
          ('medium', 'Bajar a cero en 2065', [Fraction(1), Fraction(3, 4), Fraction(1, 2), Fraction(1, 4)]),
          ('slow', 'Bajar a cero en 2085', [Fraction(1), Fraction(3, 4), Fraction(1, 2), Fraction(1, 2), Fraction(1, 4), Fraction(1, 4)]),
          ('current_policies', 'Seguir con las políticas actuales', [Fraction(1)] * 8)]
LABELS = dict(low='Clima más sensible (presupuesto del 67 %)', central='Clima central (presupuesto del 50 %)', high='Clima menos sensible (presupuesto del 33 %)')


def level_id(f):
    return 'level_' + str(int(f * 100))


def schedule(levels):
    return levels + [Fraction(0)] * (H - len(levels))


ACTIONS = [dict(id=level_id(f), label=f'Emitir y deforestar al {int(f * 100)} % del ritmo de 2025 durante una década', requires=['emit'],
                withdrawals={k: q(v) for k, v in (('budget', f * E0 * YEARS), ('forest', f * DEFOREST * YEARS)) if v},
                deposits={'emitted': q(f * E0 * YEARS)} if f else {}, add_capabilities=[], remove_capabilities=[]) for f in LEVELS]
POLICIES = [dict(id=route, label=label, default_action=level_id(Fraction(0)),
                 rules=[dict(steps=[step], when=[], action=level_id(f)) for step, f in enumerate(schedule(levels), start=1) if f])
            for route, label, levels in ROUTES]

TOTALS = {route: sum(levels) * E0 * YEARS for route, _, levels in ROUTES}

CLAIMS = [
    claim('boundaries', 'reported', 'En 2025 la Tierra ya cruzó siete de los nueve límites planetarios.',
          'Evaluación del Planetary Health Check 2025; varios valores de control son estimaciones con incertidumbre propia.', [span('phc', 'seven out of nine Planetary Boundaries have been breached')]),
    claim('warming', 'reported', 'En 2024 el calentamiento observado fue 1,52 °C, de los cuales 1,36 °C se atribuyen a la actividad humana; el presupuesto restante para 1,5 °C al 50 % era de 130 GtCO2 desde el inicio de 2025.',
          'Estimación central de Forster et al. 2025.', [span('igcc', '1.52°C, of which 1.36°C can be attributed to human activity'),
                                                      span('igcc', 'central estimate of the remaining carbon budget for 1.5°C to be 130 billion tonnes of CO2 (from the beginning of 2025)')]),
    claim('budget_2c', 'reported', 'Presupuesto de CO2 para 2 °C desde 2020 (IPCC AR6): 1350 GtCO2 al 50 %, 1150 al 67 % y 1700 al 33 %; entre 2020 y 2024 se emitieron cerca de 200 GtCO2.',
          'Tabla SPM.2 citada por una fuente secundaria; incluye el efecto de gases distintos del CO2 bajo trayectorias típicas.',
          [span('ar6_budget', '2.0 °C: 1350 GtCO₂ (Median), 33%-67% range: 1150 - 1700 GtCO₂'),
           span('igcc', 'approximately 200 Gt CO2 was emitted between 2020 and 2024')]),
    claim('emissions', 'reported', 'Emisiones mundiales de CO2 en 2025 (fósiles y uso del suelo): 42,2 GtCO2.',
          'Proyección del Global Carbon Budget 2025 para el año completo.', [span('gcb', 'about 11.5 GtC (42.2 GtCO2), marginally below the 2024 level due to lower net land-use emissions')]),
    claim('current_policies', 'reported', 'Con las políticas actuales el mundo va a 2,8 °C en este siglo; con las NDC cumplidas, a 2,3-2,5 °C.',
          'Proyección del PNUMA; depende de supuestos posteriores a 2030.', [span('unep', '2.3-2.5°C based on full implementation of Nationally Determined Contributions (NDCs), while those based on current policies are 2.8°C')]),
    claim('no_likelihood', 'reported', 'El IPCC no asigna probabilidades a sus escenarios socioeconómicos.',
          'Cita del capítulo 1 del AR6 a través de una fuente secundaria.', [span('ar6_scenarios', 'No likelihood is attached to the scenarios assessed in this Report')]),
    claim('paris', 'reported', 'El Acuerdo de París fija mantener el calentamiento muy por debajo de 2 °C y procurar limitarlo a 1,5 °C.',
          'Texto citado por una fuente secundaria.', [span('paris', 'holding the increase in the global average temperature to well below 2°C above pre-industrial levels and pursuing efforts to limit the temperature increase to 1.5°C')]),
    claim('forests', 'reported', 'Bosques del mundo en 2025: 4140 millones de hectáreas; deforestación de 10,9 millones de hectáreas por año en 2015-2025, con una pérdida neta de 4,12 millones por año.',
          'FRA 2025; la pérdida neta de 4,12 Mha por año está en el informe completo y no se cita textual aquí.', [span('fra', 'The world has a total forest area of 4.14 billion hectares'),
                                                                                                              span('fra', 'current rate of deforestation at 10.9 million hectares per year remains too high')]),
    claim('h_budget', 'hypothesis', 'El presupuesto de CO2 para 2 °C desde 2025 es 950, 1150 o 1500 GtCO2 (el de 2020 menos 200 GtCO2 emitidos).',
          'Resta simple; Forster et al. 2025 y el Global Carbon Budget 2025 dan cifras cercanas (cerca de 1050-1110 GtCO2 al 50 %).', premises=['budget_2c']),
    claim('h_routes', 'hypothesis', 'Cada ruta fija, década por década, qué fracción del ritmo de 2025 (42,2 GtCO2 y 10,9 Mha deforestadas por año) se mantiene: 100, 75, 50, 25 o 0 %. Bajar a cero en 2045: 75 y 25 %. En 2065: 100, 75, 50 y 25 %. En 2085: 100, 75, 50, 50, 25 y 25 %. Políticas actuales: 100 % siempre. Emisiones acumuladas 2025-2105: ' +
          ', '.join(f'{r} {float(v):g}' for r, v in TOTALS.items()) + ' GtCO2.',
          'Simplificación en escalones de una década; la deforestación baja al mismo ritmo que las emisiones. El PNUMA proyecta que las políticas actuales no mantienen las emisiones exactamente constantes; no se modelan emisiones negativas.', premises=['emissions', 'current_policies', 'forests']),
    claim('h_forest', 'hypothesis', 'La expansión de bosque de 6,78 Mha por año (10,9 de deforestación menos 4,12 de pérdida neta) sigue igual en todas las rutas y escenarios.',
          'La expansión incluye plantaciones, que no equivalen a bosque nativo para la biodiversidad.', premises=['forests']),
    claim('d_scenarios', 'decision', 'Escenarios: la respuesta del clima a cada tonelada de CO2 es incierta. Clima más sensible usa el presupuesto con 67 % de probabilidad de no pasar 2 °C; central, el del 50 %; menos sensible, el del 33 %.',
          'Los tres escenarios representan los tercios de la distribución de forma optimista: un tercio inferior bien representado usaría el presupuesto del 83 % (900 GtCO2 desde 2020), que no se pudo verificar textual. Las rutas frágiles pueden estar sobrestimadas.',
          premises=['budget_2c', 'h_budget']),
    claim('d_law', 'decision', 'Ley declarada: un tercio para cada escenario, como tercios de la distribución de probabilidad que el IPCC da para el presupuesto.',
          'No es una ley empírica AM-02: el clima del siglo no se repite 30 veces. La PVS es condicional a esta ley y se informa su rango bajo toda ley.',
          premises=['d_scenarios', 'no_likelihood']),
    claim('d_routes', 'decision', 'Rutas: bajar emisiones y deforestación a cero en 2045, 2065 o 2085, o seguir con las políticas actuales. Las trayectorias socioeconómicas del IPCC se tratan como decisiones de la humanidad, no como escenarios, por eso no necesitan probabilidad.',
          'Opciones planteadas por el modelizador; no son propuestas oficiales.', premises=['no_likelihood', 'current_policies', 'h_routes']),
    claim('d_life_task', 'decision', 'Condición de vida: no superar el presupuesto de CO2 para 2 °C, la línea superior del Acuerdo de París, en ninguna década. Gastar más de lo que queda en una década cuenta como incumplimiento.',
          'Umbral elegido por el modelizador. Con 1,5 °C (130 GtCO2 desde 2025) todas las rutas lo incumplirían en todos los escenarios antes de 2030. Los límites planetarios de CO2 (350 ppm) ya están cruzados.',
          premises=['paris', 'warming', 'h_budget', 'boundaries']),
    claim('d_welfare', 'decision', 'Bienestar: las generaciones futuras y las personas de hoy por el presupuesto que queda (más es mejor); las otras especies por la superficie de bosque; las economías que dependen de combustibles fósiles por el CO2 que pueden seguir emitiendo.',
          'Representación del modelizador; ninguna parte la declaró. No modela costos de mitigación ni daños económicos del calentamiento.', premises=['h_routes', 'h_forest']),
    claim('d_functions', 'decision', 'Funciones (módulo I), en décadas cumplidas: protección frente al calentamiento peligroso (presupuesto de 2 °C sin agotar) y ecosistemas (bosque no menor que el de 2025).',
          'Más décadas cumplidas es mejor.', premises=['d_life_task', 'forests']),
    claim('d_subsystems', 'decision', 'Subsistemas (módulo II): atmósfera y energía (presupuesto y CO2 emitido) y biosfera (bosques). Los une el uso del suelo, que emite CO2 al deforestar.',
          'No se modelan otros límites planetarios (agua, nitrógeno, fósforo, acidificación).', premises=['boundaries']),
    claim('modelling', 'definition', 'Unidades: GtCO2 para presupuesto y emisiones, millones de hectáreas (Mha) para bosques. Ocho pasos de una década, de 2025 a 2105. Las emisiones de cada ruta salen del presupuesto; el escenario ajusta el presupuesto en la primera década; la expansión de bosque entra cada década.',
          'Modelo de un solo número para el clima: no modela gases distintos del CO2 por separado, puntos de inflexión ni emisiones negativas.', premises=['h_budget', 'h_routes', 'h_forest']),
]


def events(scenario):
    out = []
    for step in range(1, H + 1):
        drains = {'budget': q(BUDGET['high'] - BUDGET[scenario])} if step == 1 and scenario != 'high' else {}
        out.append(dict(inflows={'forest': q(EXPANSION * YEARS)}, renewables={}, drains=drains, remove_capabilities=[]))
    return out


FRAGMENTS = [
    ('/profile', 'STOCK_FLOW_FINITE_V1', ['modelling']),
    ('/name', 'La Tierra: clima y bosques, 2025-2105', ['modelling']),
    ('/horizon', H, ['modelling']),
    ('/step_unit', 'step', ['modelling']),
    ('/stocks/0', dict(id='budget', label='Presupuesto de CO2 que queda para 2 °C', unit='GtCO2', kind='persistent', initial=q(BUDGET['high']), capacity=q(BUDGET['high'])), ['h_budget', 'modelling']),
    ('/stocks/1', dict(id='emitted', label='CO2 emitido desde 2025 (acumulado)', unit='GtCO2', kind='persistent', initial='0/1', capacity='5000/1'), ['h_routes']),
    ('/stocks/2', dict(id='forest', label='Bosques del mundo', unit='Mha', kind='persistent', initial=q(FOREST), capacity='6000/1'), ['forests']),
    ('/carriers/0', dict(id='future_generations', label='Generaciones futuras', kind='person'), ['d_life_task']),
    ('/carriers/1', dict(id='other_species', label='Otras especies', kind='living'), ['boundaries']),
    ('/carriers/2', dict(id='people_today', label='Personas de hoy', kind='person'), ['warming']),
    ('/carriers/3', dict(id='fossil_economies', label='Economías que dependen de combustibles fósiles', kind='organization'), ['emissions']),
    ('/capabilities/0', dict(id='emit', label='Economía en marcha'), ['modelling']),
    ('/initial_capabilities/0', 'emit', ['modelling']),
]
FRAGMENTS += [(f'/actions/{i}', a, ['h_routes', 'h_forest']) for i, a in enumerate(ACTIONS)]
FRAGMENTS += [(f'/policies/{i}', p, ['d_routes', 'h_routes']) for i, p in enumerate(POLICIES)]
for i, s in enumerate(['low', 'central', 'high']):
    FRAGMENTS.append((f'/scenarios/{i}', dict(id=s, label=LABELS[s], events=events(s)), ['d_scenarios', 'h_budget', 'h_forest']))
SAFE = [dict(kind='stock', stock='budget', op='ge', value='0/1')]
FRAGMENTS += [
    ('/law', {'low': '1/3', 'central': '1/3', 'high': '1/3'}, ['d_law']),
    ('/welfare/0', dict(carrier='future_generations', dimension='climate_margin', label='Presupuesto de 2 °C que queda', stock='budget', direction='higher'), ['d_welfare']),
    ('/welfare/1', dict(carrier='people_today', dimension='climate_margin', label='Presupuesto de 2 °C que queda', stock='budget', direction='higher'), ['d_welfare']),
    ('/welfare/2', dict(carrier='other_species', dimension='forest', label='Superficie de bosque', stock='forest', direction='higher'), ['d_welfare']),
    ('/welfare/3', dict(carrier='fossil_economies', dimension='emissions_allowed', label='CO2 que pueden seguir emitiendo', stock='emitted', direction='higher'), ['d_welfare']),
    ('/task', dict(kind='life_conditions', label='No superar el presupuesto de CO2 para 2 °C en ninguna década', living_carriers=['future_generations', 'other_species'],
                   conditions=[dict(stock='budget', op='ge', threshold='0/1')], require_action_success=True), ['d_life_task']),
    ('/functions/0', dict(id='climate_safety', kind='safety', label='Calentamiento por debajo de 2 °C (décadas cumplidas)', serves=['future_generations', 'people_today', 'other_species'],
                          measure='cumulative', when=SAFE), ['d_functions']),
    ('/functions/1', dict(id='forest_cover', kind='ecosystems', label='Bosque no menor que el de 2025 (décadas cumplidas)', serves=['other_species'],
                          measure='cumulative', when=[dict(kind='stock', stock='forest', op='ge', value=q(FOREST))]), ['d_functions']),
    ('/subsystems/0', dict(id='atmosphere', label='Atmósfera y energía', stocks=['budget', 'emitted'], carriers=['future_generations', 'people_today', 'fossil_economies']), ['d_subsystems']),
    ('/subsystems/1', dict(id='biosphere', label='Biosfera', stocks=['forest'], carriers=['other_species']), ['d_subsystems']),
    ('/interfaces/0', dict(id='land_use', label='Deforestación que emite CO2 (Mha)', source='biosphere', target='atmosphere'), ['d_subsystems']),
    ('/require_all_scenarios', True, ['modelling']),
    ('/selection', 'none', ['modelling']),
    ('/assumptions/0', dict(id='Calibration', kind='CALIBRATION', statement='Presupuesto desde 2025, rutas en escalones por década y expansión de bosque son hipótesis propias sobre cifras publicadas.', provenance='Claims h_budget, h_routes, h_forest'), ['h_budget', 'h_routes', 'h_forest']),
    ('/assumptions/1', dict(id='LifeTwoDegrees', kind='NORMATIVE', statement='La condición de vida es no superar el presupuesto de 2 °C; margen climático, bosques y emisiones permitidas se comparan como bienestar, sin sumarlos.', provenance='Claims d_life_task, d_welfare'), ['d_life_task', 'd_welfare']),
    ('/assumptions/2', dict(id='ClimateLaw', kind='PROBABILITY', statement='Un tercio para cada respuesta del clima, declarado a partir de las probabilidades del IPCC para el presupuesto; no es una ley empírica AM-02. La PVS se informa también bajo toda ley.', provenance='Claim d_law'), ['d_law']),
]

ENTITIES = [
    dict(id='budget', label='Presupuesto de CO2 para 2 °C', kind='resource', evidence_ids=['e_budget']),
    dict(id='emitted', label='CO2 emitido', kind='resource', evidence_ids=['e_emissions']),
    dict(id='forest', label='Bosques del mundo', kind='resource', evidence_ids=['e_forest']),
    dict(id='future_generations', label='Generaciones futuras', kind='person', evidence_ids=['e_budget']),
    dict(id='other_species', label='Otras especies', kind='living', evidence_ids=['e_boundaries']),
    dict(id='people_today', label='Personas de hoy', kind='person', evidence_ids=['e_warming']),
    dict(id='fossil_economies', label='Economías fósiles', kind='organization', evidence_ids=['e_emissions']),
]
EVIDENCE = [
    dict(id='e_boundaries', observed_at=BY_ID['phc']['observed_at'], source=BY_ID['phc']['origin'], basis='reported', statement='Siete de nueve límites planetarios cruzados.', uncertainty='Evaluación científica.'),
    dict(id='e_warming', observed_at=BY_ID['igcc']['observed_at'], source=BY_ID['igcc']['origin'], basis='reported', statement='1,36 °C de calentamiento humano en 2024.', uncertainty='Estimación central.'),
    dict(id='e_budget', observed_at=BY_ID['ar6_budget']['observed_at'], source=BY_ID['ar6_budget']['origin'], basis='reported', statement='Presupuesto para 2 °C de 1150-1700 GtCO2 desde 2020.', uncertainty='Rango 33-67 %.'),
    dict(id='e_emissions', observed_at=BY_ID['gcb']['observed_at'], source=BY_ID['gcb']['origin'], basis='reported', statement='42,2 GtCO2 emitidas en 2025.', uncertainty='Proyección anual.'),
    dict(id='e_forest', observed_at=BY_ID['fra']['observed_at'], source=BY_ID['fra']['origin'], basis='reported', statement='4140 Mha de bosque; 10,9 Mha deforestadas por año.', uncertainty='Datos nacionales agregados.'),
]
RELATIONS = [
    dict(id='econ_emit', source='fossil_economies', target='emitted', kind='organizes', evidence_ids=['e_emissions']),
    dict(id='budget_future', source='budget', target='future_generations', kind='supplies', evidence_ids=['e_budget']),
    dict(id='budget_today', source='budget', target='people_today', kind='supplies', evidence_ids=['e_warming']),
    dict(id='forest_species', source='forest', target='other_species', kind='supplies', evidence_ids=['e_forest']),
]
OBSERVATION = dict(format='genius-system-observation/1', label='La Tierra: clima y bosques, 2025',
                   window=dict(start='2015-12-12T00:00:00+00:00', end='2026-10-19T00:00:00+00:00'),
                   entities=ENTITIES, evidence=EVIDENCE, relations=RELATIONS,
                   unknowns=['Respuesta exacta del clima a cada tonelada de CO2 (por eso hay tres escenarios).', 'Puntos de inflexión del sistema climático.',
                             'Cinco límites planetarios cruzados que este gemelo todavía no modela (agua, nitrógeno, fósforo, acidificación, entidades nuevas).',
                             'Costos de mitigación y daños económicos del calentamiento.'])
SCOPE = dict(format='genius-system-scope/1', observation_revision=1, label='Presupuesto de CO2 para 2 °C, emisiones y bosques',
             members=[e['id'] for e in ENTITIES], intervention_entities=['fossil_economies'], evaluation_entities=[e['id'] for e in ENTITIES],
             bindings=[dict(collection='stocks', model_id=s, entity_id=s) for s in ('budget', 'emitted', 'forest')] +
                      [dict(collection='carriers', model_id=c, entity_id=c) for c in ('future_generations', 'other_species', 'people_today', 'fossil_economies')],
             rationale='La humanidad decide su ruta de emisiones y deforestación; se evalúan el margen climático, los bosques y las emisiones permitidas. Fuera de alcance: los otros límites planetarios.')

WORLD = dict(
    narrative='Primer gemelo de la Tierra con hipótesis declaradas: la humanidad emite 42,2 GtCO2 por año y le quedan entre 950 y 1500 GtCO2 para no pasar 2 °C, según cuán sensible sea el clima. Se comparan bajar emisiones y deforestación a cero en 2045, 2065 o 2085, y seguir con las políticas actuales.',
    observation=OBSERVATION,
    construction={'format': 'genius-world-construction/1', 'sources': SOURCES, 'claims': CLAIMS,
                  'fragments': [dict(path=p, value=v, claim_ids=c) for p, v, c in FRAGMENTS], 'scope': SCOPE, 'unresolved': []},
    provenance='Interpretación manual de extractos textuales citados; cifras no citadas declaradas como hipótesis.')

if __name__ == '__main__':
    out = Path(__file__).with_name('world.json')
    out.write_text(json.dumps(WORLD, ensure_ascii=False, indent=2) + '\n')
    print(out)
