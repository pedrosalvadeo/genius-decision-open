"""Builds world.json for the Denver Water 2026/27 drought case from cited excerpts.

Run: python twin/cases/denver_water_2026/build.py
Quotes are copied verbatim from the cited pages; every number that is not quoted
is a hypothesis claim and is listed in README.md for review.
"""
import json
from pathlib import Path

SOURCES = [
    dict(id='dw_tap_oct12', origin='Denver Water TAP, "Denver Water supply and water use update", https://www.denverwater.org/tap/denver-water-snowpack-and-water-supply-update',
         observed_at='2026-10-12T12:00:00-06:00', content=' […] '.join([
             'As of Oct. 12, 2026, reservoirs were 67% full, versus an average of 90% full for this time.',
             'Water use Oct. 1 through Oct. 11 was 34% below the five-year average,',
             'On Aug. 26, 2026, the board amended its Stage 1 drought resolution to prohibit lawn watering as of Oct. 1.',
             'Customers are reminded of the ban on lawn watering and spray irrigation as of Oct. 1.'])),
    dict(id='gazette_oct15', origin='Denver Gazette, 2026-10-15, https://www.denvergazette.com/2026/10/15/denvers-reservoirs-dwindle-to-two-thirds-capacity/',
         observed_at='2026-10-15T12:00:00-06:00', content=' […] '.join([
             "The system's reservoir storage dropped from 72% capacity to 67% in just five weeks.",
             'Officials warn levels could fall to 55% to 60% before next spring\'s runoff.',
             'Typically, levels would be at 85% capacity before the snowmelt begins.',
             "It would take a snowpack that's more than 150% of normal this winter.",
             'To put these numbers into perspective, Denver Water\'s reservoir storage "bottomed out" at 50% of the system\'s capacity in 2003',
             'Denver has never implemented Stage 2 drought restrictions, which ban outdoor watering.',
             'Peaking early at about 58% of normal, an unusually warm March accelerated the melt,',
             'Denver Water depends on snowpack for a water supply that serves 1.5 million people across the metro,'])),
    dict(id='denver7_aug', origin='Denver7, August 2026, https://www.denver7.com/news/drought/denver-water-orders-lawn-sprinklers-off-starting-oct-1-as-drought-pushes-reservoir-levels-to-record-lows',
         observed_at='2026-08-26T12:00:00-06:00', content=' […] '.join([
             "As of Aug. 24, storage in Denver Water's supply reservoirs sat at 72% full,",
             'just 95,000 acre-feet — 22% of normal,',
             'expected to remain off well into spring 2027.'])),
    dict(id='dw_resolution', origin='Denver Water Board Resolution #002-2026, https://www.denverwater.org/drought/board-resolution-drought-declaration',
         observed_at='2026-03-25T12:00:00-06:00', content=' […] '.join([
             "storage in Denver Water's supply reservoirs is currently at 80% of full.",
             'reduce total water demand by 20% from March 25, 2026 through April 30, 2027.'])),
    dict(id='dw_water_watch', origin='Denver Water, "Water Watch Report", 12/10/2026, https://www.denverwater.org/sites/default/files/water-watch-report.pdf',
         observed_at='2026-10-12T12:00:00-06:00', content=' […] '.join([
             'October 12, 2026 Water Watch Report',
             'Total system supply reservoir contents are shown in acre-feet (AF).',
             'TOTAL 378,895 480,506 567,906 67 85 90',
             'Day of Month Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec Sum of YTD-Avg',
             'Expected Daily Use 109 109 109 120 175 261 300 288 263 170 114 107 193',
             'Values are in million gallons (MG).'])),
]
BY_ID = {s['id']: s for s in SOURCES}


def span(source_id, quote):
    content = BY_ID[source_id]['content']
    start = content.index(quote)
    return dict(source_id=source_id, start=start, end=start + len(quote), quote=quote)


def claim(id, basis, statement, uncertainty, spans=(), premises=()):
    return dict(id=id, basis=basis, statement=statement, uncertainty=uncertainty, spans=list(spans), premises=list(premises))


CLAIMS = [
    claim('storage_now', 'reported', 'Almacenamiento de los embalses de suministro de Denver Water: 67 % de su capacidad el 12/10/2026.',
          'Cifra publicada por la empresa; no se conoce la capacidad exacta usada como denominador.',
          [span('dw_tap_oct12', 'As of Oct. 12, 2026, reservoirs were 67% full, versus an average of 90% full for this time.')]),
    claim('lawn_ban', 'reported', 'Desde el 1/10/2026 rige la prohibición de riego de césped y riego por aspersión (Etapa 1 enmendada).',
          'La fecha de reanudación la decide el directorio.',
          [span('dw_tap_oct12', 'On Aug. 26, 2026, the board amended its Stage 1 drought resolution to prohibit lawn watering as of Oct. 1.'),
           span('denver7_aug', 'expected to remain off well into spring 2027.')]),
    claim('winter_projection', 'reported', 'La empresa advierte que el almacenamiento podría caer a 55–60 % antes del deshielo de primavera.',
          'Proyección sin método publicado en la nota; rango, no valor puntual.',
          [span('gazette_oct15', "Officials warn levels could fall to 55% to 60% before next spring's runoff.")]),
    claim('recent_decline', 'reported', 'El almacenamiento bajó de 72 % (24/8) a 67 % (12/10) con riego de Etapa 1 hasta el 30/9.',
          'Cinco a siete semanas; incluye evaporación de verano y riego de fin de temporada.',
          [span('gazette_oct15', "The system's reservoir storage dropped from 72% capacity to 67% in just five weeks."),
           span('denver7_aug', "As of Aug. 24, storage in Denver Water's supply reservoirs sat at 72% full,")]),
    claim('dry_runoff_2026', 'reported', 'El escurrimiento de abril a julio de 2026 fue 95.000 acre-pies, 22 % de lo normal; el almacenamiento pasó de 80 % (marzo) a 72 % (agosto).',
          'Año más seco en 110 años de registro según la nota.',
          [span('denver7_aug', 'just 95,000 acre-feet — 22% of normal,'),
           span('dw_resolution', "storage in Denver Water's supply reservoirs is currently at 80% of full.")]),
    claim('refill_needs', 'reported', 'Hace falta una nieve mayor al 150 % de lo normal para llenar los embalses; normalmente llegan al deshielo con 85 %.',
          'Declaración cualitativa de la empresa.',
          [span('gazette_oct15', "It would take a snowpack that's more than 150% of normal this winter."),
           span('gazette_oct15', 'Typically, levels would be at 85% capacity before the snowmelt begins.')]),
    claim('record_low', 'reported', 'El mínimo histórico del sistema fue 50 % de capacidad en 2003.', 'Dato histórico citado por la prensa.',
          [span('gazette_oct15', 'To put these numbers into perspective, Denver Water\'s reservoir storage "bottomed out" at 50% of the system\'s capacity in 2003')]),
    claim('population', 'reported', 'El suministro sirve a 1,5 millones de personas.', 'Cifra redondeada.',
          [span('gazette_oct15', 'Denver Water depends on snowpack for a water supply that serves 1.5 million people across the metro,')]),
    claim('h_winter_drawdown', 'hypothesis', 'Con riego prohibido, el almacenamiento neto baja 1,5 puntos por mes de mediados de octubre a mediados de abril (67 → 58, centro del rango oficial 55–60).',
          'Calibración lineal propia sobre la proyección oficial; la trayectoria mensual real no es lineal.', premises=['storage_now', 'winter_projection', 'lawn_ban']),
    claim('h_summer_base', 'hypothesis', 'De mayo a octubre, sin riego exterior, el uso interior y la evaporación restan 2 puntos por mes.',
          'Supuesto propio; mayor que el invierno por evaporación y demanda estival. Requiere datos mensuales de Denver Water.', premises=['h_winter_drawdown']),
    claim('h_outdoor_stage1', 'hypothesis', 'Reanudar el riego de Etapa 1 (dos días por semana) cuesta 2 puntos adicionales por mes de riego (mayo a septiembre).',
          'Supuesto propio, coherente con la caída 72 → 67 % de agosto a octubre con riego de Etapa 1. Requiere datos de consumo exterior.', premises=['recent_decline', 'h_summer_base']),
    claim('h_runoff', 'hypothesis', 'Aporte neto del deshielo (mayo, junio, julio): seco como 2026 = 2, 3, 1 puntos; normal = 8, 14, 6; húmedo (>150 % de nieve) = 12, 20, 12.',
          'Supuesto propio. El seco replica que en 2026 el almacenamiento casi no subió; el húmedo alcanza el llenado que la empresa asocia a >150 % de nieve; el normal queda entre ambos. Denver Water publica escenarios seco/normal/húmedo que deberían reemplazar estas cifras.',
          premises=['dry_runoff_2026', 'refill_needs']),
    claim('capacity_use', 'reported', 'Capacidad total de los embalses de suministro: 567.906 acre-pies (67 % lleno el 12/10/2026). Uso diario esperado en enero, febrero y marzo, sin riego: 109 millones de galones.',
          'Cifras de la empresa; el uso esperado es un promedio, no un mínimo garantizado.',
          [span('dw_water_watch', 'TOTAL 378,895 480,506 567,906 67 85 90'), span('dw_water_watch', 'Expected Daily Use 109 109 109 120 175 261 300 288 263 170 114 107 193'),
           span('dw_water_watch', 'Values are in million gallons (MG).')]),
    claim('h_life_reserve', 'hypothesis', 'Un año entero de uso de invierno (109 millones de galones por día durante 365 días) son unos 122.100 acre-pies, 21,5 % de la capacidad (109.000.000 × 365 / 325.851 galones por acre-pie / 567.906 = 21,499 %).',
          'Usa el uso de invierno como aproximación del uso esencial; el uso interior estricto es algo menor, así que el umbral es prudente.',
          premises=['capacity_use']),
    claim('d_life_task', 'decision', 'Condición de vida: los embalses guardan en todo momento al menos un año de agua de uso de invierno (21,5 % de la capacidad) para las 1,5 millones de personas servidas, aunque no entre agua.',
          'Elegida por el modelizador como condición material del suministro esencial hasta el deshielo siguiente; el mínimo de 50 % de 2003 queda como referencia histórica.',
          premises=['h_life_reserve', 'population', 'record_low']),
    claim('d_law', 'decision', 'Ley empírica admitida por AM-02 sobre los tres inviernos: seco 4/33, normal 8/11, húmedo 5/33. Cada año de los últimos 30 (1997 a 2026, regla de ventana de AM-02 elegida por Pedro el 18/10/2026) se asigna al escenario cuya nieve del 1 de abril se parece más (seco anclado en 2026, 34,4 % de la mediana; normal en 100 %; húmedo en 150 %), con 12 estaciones SNOTEL del NRCS en las cuencas de Denver Water. Resultaron 3 secos (2002, 2012, 2026), 23 normales y 4 húmedos (1997, 2011, 2014, 2019). Un tercio cada uno queda descalibrado; la frecuencia suavizada (k+1)/(n+3) pasa la calibración, con 30 resultados independientes. Con los 36 años desde 1991 la ley sería 4/39, 28/39, 7/39. Certificado: twin/history/denver_snow/law_certificate.json.',
          'Retrospectiva precuencial: se revoca si los contrastes prospectivos la descalibran. Las anclas de los escenarios son del modelizador; del lado del Platte Sur sólo Hoosier Pass tiene registro desde 1991. La PVS no depende de la ley en este caso (rango bajo toda ley de un único valor).',
          premises=['h_runoff']),
    claim('d_policies', 'decision', 'Opciones comparadas: mantener la prohibición todo el horizonte; reanudar riego de Etapa 1 de mayo a septiembre; reanudarlo sólo en los meses que empiezan con almacenamiento de 70 % o más.',
          'Opciones planteadas por el modelizador a partir de la discusión pública (Etapa 2 nunca aplicada, prohibición "hasta bien entrada la primavera"). El umbral de 70 % es elección propia.', premises=['lawn_ban']),
    claim('d_org_welfare', 'decision', 'El bienestar de Denver Water como organización se representa por la reserva que administra (almacenamiento, más es mejor).',
          'Representación elegida por el modelizador a partir de su objetivo público de preservar el suministro; no es una métrica declarada por la empresa.', premises=['lawn_ban', 'storage_now']),
    claim('d_functions', 'decision', 'Función del sistema (módulo I), medida en cada gemelo proyectado como meses cumplidos hasta cada momento: el suministro opera con los embalses en 50 % o más, el mínimo histórico de 2003.',
          'Más meses cumplidos es mejor. El 50 % es una referencia histórica, no una regla de Denver Water.', premises=['record_low', 'population']),
    claim('d_subsystems', 'decision', 'Subsistemas (módulo II): los embalses que administra Denver Water, y los jardines de la población servida. Los une el agua de riego exterior.',
          'Representación del modelizador; no se modelan embalses individuales ni la red de distribución.', premises=['lawn_ban', 'population', 'h_outdoor_stage1']),
    claim('modelling', 'definition', 'Unidad: puntos porcentuales de la capacidad de los embalses de suministro. Paso mensual, del 15/10/2026 al 15/10/2027 (paso 1 = mediados de noviembre). Riego exterior acumulado como existencia que registra el agua entregada a jardines. La ley sobre los inviernos se declara aparte (claim d_law).',
          'Decisiones de representación; no se modelan embalses individuales, derechos ni el río aguas abajo.', premises=['storage_now', 'population']),
]

H = 12
MONTHS = 'nov dic ene feb mar abr may jun jul ago sep oct'.split()
RUNOFF = dict(dry=['2/1', '3/1', '1/1'], normal=['8/1', '14/1', '6/1'], wet=['12/1', '20/1', '12/1'])
LABELS = dict(dry='Invierno seco, deshielo como 2026', normal='Invierno normal', wet='Invierno húmedo, nieve mayor a 150 %')


def events(scenario):
    out = []
    for step in range(1, H + 1):
        inflow = {'storage': RUNOFF[scenario][step - 7]} if 7 <= step <= 9 else {}
        out.append(dict(inflows=inflow, renewables={}, drains={'storage': '3/2' if step <= 6 else '2/1'}, remove_capabilities=[]))
    return out


SEASON = list(range(7, 12))  # May..Sep
ALL = ['storage_now', 'modelling']
FRAGMENTS = [
    ('/profile', 'STOCK_FLOW_FINITE_V1', ['modelling']),
    ('/name', 'Denver Water: sequía 2026/27 y riego exterior', ['modelling']),
    ('/horizon', H, ['modelling']),
    ('/step_unit', 'step', ['modelling']),
    ('/stocks/0', dict(id='storage', label='Almacenamiento de embalses de suministro', unit='pct_capacity', kind='persistent', initial='67/1', capacity='100/1'), ['storage_now', 'modelling']),
    ('/stocks/1', dict(id='outdoor', label='Agua entregada a riego exterior (acumulada)', unit='pct_capacity', kind='persistent', initial='0/1', capacity='100/1'), ['modelling', 'h_outdoor_stage1']),
    ('/carriers/0', dict(id='residents', label='Población servida (1,5 millones)', kind='person'), ['population']),
    ('/carriers/1', dict(id='denver_water', label='Denver Water (directorio)', kind='organization'), ['lawn_ban']),
    ('/capabilities/0', dict(id='supply', label='Sistema de suministro operando'), ['modelling']),
    ('/initial_capabilities/0', 'supply', ['modelling']),
    ('/actions/0', dict(id='no_outdoor', label='Sin riego de césped ni aspersión', requires=[], withdrawals={}, deposits={}, add_capabilities=[], remove_capabilities=[]), ['lawn_ban']),
    ('/actions/1', dict(id='stage1_watering', label='Riego de Etapa 1, dos días por semana', requires=['supply'], withdrawals={'storage': '2/1'}, deposits={'outdoor': '2/1'}, add_capabilities=[], remove_capabilities=[]), ['h_outdoor_stage1', 'd_policies']),
    ('/policies/0', dict(id='keep_ban', label='Mantener la prohibición todo el año', default_action='no_outdoor', rules=[]), ['d_policies']),
    ('/policies/1', dict(id='resume_may', label='Reanudar riego de Etapa 1 de mayo a septiembre', default_action='no_outdoor', rules=[dict(steps=SEASON, when=[], action='stage1_watering')]), ['d_policies']),
    ('/policies/2', dict(id='resume_if_70', label='Reanudar sólo los meses que empiezan con 70 % o más', default_action='no_outdoor',
                         rules=[dict(steps=SEASON, when=[dict(kind='stock', stock='storage', op='ge', value='70/1')], action='stage1_watering')]), ['d_policies']),
]
for i, s in enumerate(['dry', 'normal', 'wet']):
    FRAGMENTS.append((f'/scenarios/{i}', dict(id=s, label=LABELS[s], events=events(s)), ['h_winter_drawdown', 'h_summer_base', 'h_runoff']))
FRAGMENTS += [
    ('/law', {'dry': '4/33', 'normal': '8/11', 'wet': '5/33'}, ['d_law']),
    ('/welfare/0', dict(carrier='residents', dimension='outdoor_water', label='Agua disponible para jardines, árboles y césped', stock='outdoor', direction='higher'), ['modelling', 'lawn_ban']),
    ('/welfare/1', dict(carrier='denver_water', dimension='reserve', label='Reserva de los embalses que administra', stock='storage', direction='higher'), ['d_org_welfare']),
    ('/task', dict(kind='life_conditions', label='Guardar siempre al menos un año de agua de invierno (21,5 % de la capacidad) para la población', living_carriers=['residents'],
                   conditions=[dict(stock='storage', op='ge', threshold='43/2')], require_action_success=False), ['d_life_task']),
    ('/functions/0', dict(id='above_2003_low', kind='water', label='Suministro con los embalses en 50 % o más, el mínimo de 2003 (meses cumplidos)', serves=['residents', 'denver_water'],
                          measure='cumulative', when=[dict(kind='stock', stock='storage', op='ge', value='50/1')]), ['d_functions']),
    ('/subsystems/0', dict(id='reservoirs', label='Embalses de Denver Water', stocks=['storage'], carriers=['denver_water']), ['d_subsystems']),
    ('/subsystems/1', dict(id='gardens', label='Jardines de la población servida', stocks=['outdoor'], carriers=['residents']), ['d_subsystems']),
    ('/interfaces/0', dict(id='outdoor_watering', label='Agua de riego exterior de los embalses a los jardines (puntos de capacidad)', source='reservoirs', target='gardens'), ['d_subsystems']),
    ('/require_all_scenarios', True, ['modelling']),
    ('/selection', 'none', ['modelling']),
    ('/assumptions/0', dict(id='Calibration', kind='CALIBRATION', statement='Caídas mensuales, costo del riego y aportes del deshielo son hipótesis propias calibradas sobre cifras publicadas; no son datos mensuales de Denver Water.', provenance='Claims h_winter_drawdown, h_summer_base, h_outdoor_stage1, h_runoff'), ['h_winter_drawdown', 'h_runoff']),
    ('/assumptions/1', dict(id='LifeReserve', kind='NORMATIVE', statement='La condición de vida es guardar un año de agua de uso de invierno para la población (21,5 % de la capacidad); el riego exterior y la reserva se comparan como bienestar, sin sumarlos.', provenance='Claims capacity_use, h_life_reserve, d_life_task'), ['d_life_task']),
    ('/assumptions/2', dict(id='WinterLaw', kind='PROBABILITY', statement='Ley empírica admitida por AM-02 con la nieve del 1 de abril de los últimos 30 años, 1997 a 2026 (NRCS SNOTEL): seco 4/33, normal 8/11, húmedo 5/33. La PVS se informa también bajo toda ley.', provenance='Claim d_law; twin/history/snow_law.py, twin/history/denver_snow/law_certificate.json'), ['d_law']),
]

ENTITIES = [
    dict(id='storage', label='Embalses de suministro', kind='resource', evidence_ids=['e_storage']),
    dict(id='outdoor', label='Riego exterior', kind='resource', evidence_ids=['e_ban']),
    dict(id='residents', label='Población servida', kind='person', evidence_ids=['e_population']),
    dict(id='denver_water', label='Denver Water (directorio)', kind='organization', evidence_ids=['e_ban']),
]
EVIDENCE = [
    dict(id='e_storage', observed_at='2026-10-12T12:00:00-06:00', source=SOURCES[0]['origin'], basis='reported', statement='Embalses al 67 % el 12/10/2026, frente a 90 % promedio.', uncertainty='Dato de la empresa.'),
    dict(id='e_ban', observed_at='2026-10-12T12:00:00-06:00', source=SOURCES[0]['origin'], basis='reported', statement='Prohibición de riego de césped desde el 1/10/2026, decidida por el directorio.', uncertainty='Reanudación sin fecha.'),
    dict(id='e_population', observed_at='2026-10-15T12:00:00-06:00', source=SOURCES[1]['origin'], basis='reported', statement='El suministro sirve a 1,5 millones de personas.', uncertainty='Cifra redondeada.'),
]
RELATIONS = [
    dict(id='org_storage', source='denver_water', target='storage', kind='organizes', evidence_ids=['e_ban']),
    dict(id='org_outdoor', source='denver_water', target='outdoor', kind='organizes', evidence_ids=['e_ban']),
    dict(id='supply_res', source='storage', target='residents', kind='supplies', evidence_ids=['e_storage', 'e_population']),
    dict(id='outdoor_res', source='outdoor', target='residents', kind='affects', evidence_ids=['e_ban']),
]
OBSERVATION = dict(format='genius-system-observation/1', label='Denver Water: sequía 2026/27',
                   window=dict(start='2026-03-25T00:00:00-06:00', end='2026-10-15T23:59:00-06:00'),
                   entities=ENTITIES, evidence=EVIDENCE, relations=RELATIONS,
                   unknowns=['Consumo mensual por uso (interior/exterior) en acre-pies.', 'Pronósticos seco/normal/húmedo de Denver Water hasta marzo de 2027.',
                             'Efectos sobre el río South Platte y otros usuarios aguas abajo.'])
SCOPE = dict(format='genius-system-scope/1', observation_revision=1, label='Embalses, riego y población servida',
             members=['storage', 'outdoor', 'residents', 'denver_water'], intervention_entities=['denver_water'],
             evaluation_entities=['storage', 'outdoor', 'residents', 'denver_water'],
             bindings=[dict(collection='stocks', model_id='storage', entity_id='storage'), dict(collection='stocks', model_id='outdoor', entity_id='outdoor'),
                       dict(collection='carriers', model_id='residents', entity_id='residents'),
                       dict(collection='carriers', model_id='denver_water', entity_id='denver_water')],
             rationale='El directorio de Denver Water decide el riego; se evalúan embalses, riego y población. Fuera de alcance: río aguas abajo y otros municipios.')

WORLD = dict(
    narrative='Caso real con hipótesis declaradas: Denver Water llega al invierno 2026/27 con embalses al 67 % y riego de césped prohibido. Se comparan tres reglas de riego para 2027 ante un invierno seco, normal o húmedo.',
    observation=OBSERVATION,
    construction={'format': 'genius-world-construction/1', 'sources': SOURCES, 'claims': CLAIMS,
                  'fragments': [dict(path=p, value=v, claim_ids=c) for p, v, c in FRAGMENTS], 'scope': SCOPE, 'unresolved': []},
    provenance='Interpretación manual de extractos textuales citados; cifras no citadas declaradas como hipótesis.')

if __name__ == '__main__':
    out = Path(__file__).with_name('world.json')
    out.write_text(json.dumps(WORLD, ensure_ascii=False, indent=2) + '\n')
    print(out)
