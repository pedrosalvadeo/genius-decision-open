"""Builds world.json for the US type O blood supply, winter 2026/27, from cited excerpts.

Run: python twin/cases/us_blood_2026/build.py
The first case outside water: same eight modules, same kernel, a different domain.
Quotes are copied verbatim from the cited pages and were checked against the live pages
by the history node (twin/history/source_quotes.py, quotes.json in twin/history/blood_2026).
Every number that is not quoted is a hypothesis or decision claim, listed in README.md.
"""
from fractions import Fraction
import json
from pathlib import Path

RC = 'https://www.redcross.org/about-us/news-and-events/press-release/2026/'
SOURCES = [
    dict(id='rc_crisis', origin=f'American Red Cross, "American Red Cross Declares Second-Ever National Blood Supply Crisis, Urges Immediate Blood Donations", 27/07/2026, {RC}red-cross-declares-national-blood-supply-crisis-urges-immediate-.html',
         observed_at='2026-07-27T12:00:00-04:00', content=' […] '.join([
             'The American Red Cross has declared its second-ever national blood supply crisis after blood donations fell to a four-year summer low.',
             'the Red Cross now has less than a one-day national supply of type O positive blood — the most commonly transfused blood type.',
             'To help ensure blood is available for patients facing the most critical, life-threatening emergencies across the country, the Red Cross has begun limiting distributions of type O blood to individual hospitals.',
             'Type O blood accounts for about 60% of Red Cross blood distributions because it is essential for both everyday patient care and medical emergencies',
             'Hospitals now schedule about 65% of their anticipated blood needs in advance'])),
    dict(id='rc_january', origin=f'American Red Cross, "Red Cross Declares Severe Shortage after Blood Supply Falls 35% in Past Month", 20/01/2026, {RC}red-cross-declares-shortage-after-blood-supply-falls-35-.html',
         observed_at='2026-01-20T12:00:00-05:00', content=' […] '.join([
             'the inventory has continued to drop at an alarming rate of about 35% over the past month']),),
    dict(id='rc_september', origin='American Red Cross Utah, Blood Donation Day release, 04/09/2026, https://www.redcross.org/local/utah/about-us/news-and-events/press-releases/blooddonationday2026ut.html',
         observed_at='2026-09-04T12:00:00-06:00', content=' […] '.join([
             'has eased after thousands of donors responded. However, the blood supply remains vulnerable and continued donations are needed to keep pace with hospital demand.',
             'The Red Cross must collect more than 13,000 blood donations each day to meet the needs of patients at hospitals and transfusion centers nationwide.'])),
    dict(id='hoodline', origin='Hoodline, "Red Cross Launches $300 Million Lifeblood Fund After Summer Blood Crisis Hits Four-Year Low", 04/10/2026, https://hoodline.com/2026/10/red-cross-launches-300-million-lifeblood-fund-after-summer-blood-crisis-hits-four-year-low/',
         observed_at='2026-10-04T12:00:00-04:00', content=' […] '.join([
             'Red Cross Launches $300 Million Lifeblood Fund After Summer Blood Crisis Hits Four-Year Low',
             'Donated red blood cells have a maximum shelf life of just 42 days under refrigeration'])),
    dict(id='flu', origin='CDC ILINet, national weighted influenza-like illness (%), via Delphi Epidata, seasons 1997/98 to 2025/26, harvested 18/10/2026 (twin/history/blood_2026/flu_peak_wili.csv)',
         observed_at='2026-10-18T02:24:00Z', content=' […] '.join([
             '2015/2016,33,3.56024,201610', '2004/2005,33,5.44151,200507', '2025/2026,34,8.29853,202552'])),
]
BY_ID = {s['id']: s for s in SOURCES}


def span(source_id, quote):
    content = BY_ID[source_id]['content']
    start = content.index(quote)
    return dict(source_id=source_id, start=start, end=start + len(quote), quote=quote)


def claim(id, basis, statement, uncertainty, spans=(), premises=()):
    return dict(id=id, basis=basis, statement=statement, uncertainty=uncertainty, spans=list(spans), premises=list(premises))


H = 8                       # fortnights from 1 November 2026 to 20 February 2027
DAY = Fraction(39, 5)       # thousand type O units distributed per day: 60 % of 13,000
STEP = 14 * DAY             # 546/5 = 109.2 thousand units per fortnight
ELECTIVE = STEP * Fraction(15, 100)
INITIAL = DAY * Fraction(5, 2)
SHORTFALL = INITIAL * Fraction(35, 100) / 2     # severe: 35 % of the starting stock per month
PEAK = [4, 5, 6, 7]         # 13 December to 6 February
CAMPAIGN = STEP * Fraction(5, 100)
CAMPAIGN_STEPS = [1, 2, 3]
EFFECT = dict(mild=Fraction(0), moderate=Fraction(1, 2), severe=Fraction(1))
LABELS = dict(mild='Gripe leve (como 2015/16)', moderate='Gripe moderada (como 2004/05)', severe='Gripe grave (como 2025/26)')


def q(x):
    x = Fraction(x)
    return f'{x.numerator}/{x.denominator}'


CLAIMS = [
    claim('crisis', 'reported', 'El 27 de julio de 2026 la Cruz Roja declaró su segunda crisis nacional de sangre: menos de un día de reserva nacional de 0 positivo, y empezó a limitar la distribución de tipo 0 a cada hospital para las emergencias que amenazan la vida.',
          'Comunicado de la Cruz Roja; la reserva exacta en unidades no se publica.',
          [span('rc_crisis', 'The American Red Cross has declared its second-ever national blood supply crisis after blood donations fell to a four-year summer low.'),
           span('rc_crisis', 'the Red Cross now has less than a one-day national supply of type O positive blood — the most commonly transfused blood type.'),
           span('rc_crisis', 'To help ensure blood is available for patients facing the most critical, life-threatening emergencies across the country, the Red Cross has begun limiting distributions of type O blood to individual hospitals.')]),
    claim('type_o_share', 'reported', 'El tipo 0 es cerca del 60 % de lo que distribuye la Cruz Roja; los hospitales programan cerca del 65 % de su necesidad con anticipación.',
          'Proporciones aproximadas del comunicado.',
          [span('rc_crisis', 'Type O blood accounts for about 60% of Red Cross blood distributions because it is essential for both everyday patient care and medical emergencies'),
           span('rc_crisis', 'Hospitals now schedule about 65% of their anticipated blood needs in advance')]),
    claim('daily_need', 'reported', 'La Cruz Roja debe recolectar más de 13.000 donaciones por día; en septiembre la crisis había cedido, pero el suministro sigue vulnerable.',
          'Cifra redonda de un comunicado regional.',
          [span('rc_september', 'The Red Cross must collect more than 13,000 blood donations each day to meet the needs of patients at hospitals and transfusion centers nationwide.'),
           span('rc_september', 'has eased after thousands of donors responded. However, the blood supply remains vulnerable and continued donations are needed to keep pace with hospital demand.')]),
    claim('january_drop', 'reported', 'En enero de 2026, con la temporada de gripe más alta del registro, la reserva cayó cerca de 35 % en un mes.',
          'El comunicado no da la reserva inicial ni separa gripe, feriados y clima.',
          [span('rc_january', 'the inventory has continued to drop at an alarming rate of about 35% over the past month'),
           span('flu', '2025/2026,34,8.29853,202552')]),
    claim('fund', 'reported', 'En octubre de 2026 la Cruz Roja lanzó un fondo de 300 millones de dólares para reconstruir su base de donantes; los glóbulos rojos duran como máximo 42 días.',
          'Nota de prensa local.',
          [span('hoodline', 'Red Cross Launches $300 Million Lifeblood Fund After Summer Blood Crisis Hits Four-Year Low'),
           span('hoodline', 'Donated red blood cells have a maximum shelf life of just 42 days under refrigeration')]),
    claim('h_demand', 'hypothesis', 'Distribución de tipo 0 de la Cruz Roja: 7,8 mil unidades por día (60 % de 13.000), 109,2 mil por quincena. Un día de reserva = 7,8 mil unidades. Sin gripe, la recolección iguala la distribución.',
          'Supone que las 13.000 donaciones diarias equivalen a la necesidad diaria y que el tipo 0 se recolecta en la misma proporción en que se distribuye.',
          premises=['type_o_share', 'daily_need']),
    claim('h_elective', 'hypothesis', 'El 15 % de la distribución de tipo 0 (16,38 mil unidades por quincena) va a cirugías programadas que se pueden postergar.',
          'Supuesto propio, sin fuente: el 65 % programado incluye tratamientos que no se postergan (oncología, anemias crónicas).',
          premises=['type_o_share', 'h_demand']),
    claim('h_initial', 'hypothesis', 'Reserva de tipo 0 de la Cruz Roja al 1 de noviembre de 2026: 2,5 días (19,5 mil unidades).',
          'Supuesto propio: la Cruz Roja no publica la reserva; en septiembre la crisis había cedido pero el suministro seguía vulnerable. Es la hipótesis que más pesa en el resultado.',
          premises=['daily_need', 'crisis']),
    claim('h_flu', 'hypothesis', 'Gripe grave: entre el 13 de diciembre y el 6 de febrero la recolección cae por debajo de la distribución en 35 % de la reserva inicial por mes (3,4125 mil unidades por quincena), como en enero de 2026. Moderada: la mitad. Leve: sin caída.',
          'Supuesto propio que traslada la caída de enero de 2026 a una reserva de 2,5 días; no separa gripe de feriados.',
          premises=['january_drop', 'h_initial', 'h_demand']),
    claim('h_campaign', 'hypothesis', 'Una campaña de donantes en noviembre y la primera quincena de diciembre suma 5 % a la recolección (5,46 mil unidades por quincena).',
          'Supuesto propio sobre lo que el fondo de donantes puede lograr; no hay meta publicada.', premises=['fund', 'h_demand']),
    claim('d_scenarios', 'decision', 'Escenarios: gripe leve, moderada y grave, anclados en el pico semanal de ILINet de 2015/16 (3,56 %), 2004/05 (5,44 %) y 2025/26 (8,30 %).',
          'Las temporadas de referencia son elección del modelizador.', [span('flu', '2015/2016,33,3.56024,201610'), span('flu', '2004/2005,33,5.44151,200507'),
                                                                       span('flu', '2025/2026,34,8.29853,202552')], premises=['h_flu']),
    claim('d_law', 'decision', 'Ley declarada sobre los tres escenarios: un tercio cada uno.',
          'AM-02 sobre los picos de gripe (twin/history/blood_2026) tiene 29 temporadas, una menos de las 30 que exige; se admitirá con la temporada 2026/27. La PVS es condicional a esta ley y se informa su rango bajo toda ley.',
          premises=['d_scenarios']),
    claim('d_life_task', 'decision', 'Condición de vida: la reserva de tipo 0 nunca baja de un día (7,8 mil unidades), el nivel en que la Cruz Roja declaró la crisis y empezó a racionar para emergencias que amenazan la vida.',
          'Umbral elegido por el modelizador a partir del comunicado; protege a pacientes de trauma y emergencias. Las cirugías programadas se comparan como bienestar.',
          premises=['crisis', 'h_demand']),
    claim('d_policies', 'decision', 'Opciones: seguir igual; postergar cirugías programadas cuando la reserva baja de 2 días; campaña de donantes antes de las fiestas; campaña y postergación.',
          'Opciones planteadas por el modelizador a partir de lo que hizo la Cruz Roja en julio; no son propuestas oficiales.', premises=['crisis', 'fund']),
    claim('d_welfare', 'decision', 'Bienestar: los pacientes de cirugías programadas por las unidades que reciben; la Cruz Roja por su reserva (más es mejor); los donantes por las donaciones extra que se les piden (menos es mejor).',
          'Representación del modelizador; ninguna parte la declaró.', premises=['h_elective', 'h_campaign']),
    claim('d_functions', 'decision', 'Funciones del sistema (módulo I), en quincenas cumplidas: abastecer a los hospitales con 2 días de reserva o más (salud) y sostener la reserva mínima de emergencia de un día (seguridad).',
          'Más quincenas cumplidas es mejor; el umbral de 2 días es elección del modelizador.', premises=['crisis', 'h_demand']),
    claim('d_subsystems', 'decision', 'Subsistemas (módulo II): la reserva de la Cruz Roja con sus donantes, y los quirófanos con los pacientes de cirugías programadas. Los une la distribución para cirugías programadas.',
          'No se modelan otros proveedores (la Cruz Roja es cerca del 40 % del país), plaquetas ni plasma.', premises=['h_elective']),
    claim('modelling', 'definition', 'Unidad: mil unidades de glóbulos rojos tipo 0 de la Cruz Roja. Paso quincenal del 1 de noviembre de 2026 al 20 de febrero de 2027 (8 pasos). La recolección entra a la reserva y la distribución no programada sale cada quincena; la capacidad de 200 mil unidades es una cota de modelado que nunca se alcanza, porque la recolección de cada quincena entra antes que la distribución; el vencimiento (42 días) no se modela.',
          'Agrega tipos 0 positivo y negativo; no modela bancos de hospitales ni transferencias entre regiones.', premises=['h_demand', 'fund']),
]


def events(scenario):
    out = []
    for step in range(1, H + 1):
        collected = STEP - (SHORTFALL * EFFECT[scenario] if step in PEAK else 0)
        out.append(dict(inflows={'inventory': q(collected)}, renewables={}, drains={'inventory': q(STEP - ELECTIVE)}, remove_capabilities=[]))
    return out


TWO_DAYS = [dict(kind='stock', stock='inventory', op='ge', value=q(2 * DAY))]
FRAGMENTS = [
    ('/profile', 'STOCK_FLOW_FINITE_V1', ['modelling']),
    ('/name', 'Sangre tipo 0 en EE.UU.: invierno 2026/27', ['modelling']),
    ('/horizon', H, ['modelling']),
    ('/step_unit', 'step', ['modelling']),
    ('/stocks/0', dict(id='inventory', label='Reserva de glóbulos rojos tipo 0 de la Cruz Roja', unit='kunits', kind='persistent', initial=q(INITIAL), capacity='200/1'), ['h_initial', 'modelling']),
    ('/stocks/1', dict(id='electives', label='Unidades entregadas a cirugías programadas (acumulado)', unit='kunits', kind='persistent', initial='0/1', capacity='5000/1'), ['h_elective']),
    ('/stocks/2', dict(id='donor_pool', label='Donaciones extra que la campaña puede pedir', unit='kunits', kind='persistent', initial=q(CAMPAIGN * len(CAMPAIGN_STEPS)), capacity=q(CAMPAIGN * len(CAMPAIGN_STEPS))), ['h_campaign']),
    ('/carriers/0', dict(id='emergency_patients', label='Pacientes de trauma y emergencias', kind='person'), ['crisis']),
    ('/carriers/1', dict(id='surgical_patients', label='Pacientes de cirugías programadas', kind='person'), ['h_elective']),
    ('/carriers/2', dict(id='red_cross', label='Cruz Roja Americana', kind='organization'), ['crisis']),
    ('/carriers/3', dict(id='donors', label='Donantes de sangre', kind='person'), ['h_campaign']),
    ('/capabilities/0', dict(id='operate', label='Distribución de sangre'), ['modelling']),
    ('/initial_capabilities/0', 'operate', ['modelling']),
    ('/actions/0', dict(id='defer', label='Postergar cirugías programadas', requires=[], withdrawals={}, deposits={}, add_capabilities=[], remove_capabilities=[]), ['d_policies']),
    ('/actions/1', dict(id='supply_electives', label='Abastecer cirugías programadas', requires=['operate'], withdrawals={'inventory': q(ELECTIVE)},
                        deposits={'electives': q(ELECTIVE)}, add_capabilities=[], remove_capabilities=[]), ['h_elective']),
    ('/actions/2', dict(id='campaign_and_electives', label='Campaña de donantes y cirugías programadas', requires=['operate'],
                        withdrawals={'inventory': q(ELECTIVE), 'donor_pool': q(CAMPAIGN)}, deposits={'electives': q(ELECTIVE), 'inventory': q(CAMPAIGN)},
                        add_capabilities=[], remove_capabilities=[]), ['h_elective', 'h_campaign']),
    ('/actions/3', dict(id='campaign_only', label='Campaña de donantes y cirugías postergadas', requires=['operate'], withdrawals={'donor_pool': q(CAMPAIGN)},
                        deposits={'inventory': q(CAMPAIGN)}, add_capabilities=[], remove_capabilities=[]), ['h_campaign']),
    ('/policies/0', dict(id='as_usual', label='Seguir igual', default_action='supply_electives', rules=[]), ['d_policies']),
    ('/policies/1', dict(id='defer_below_two_days', label='Postergar cirugías programadas con menos de 2 días', default_action='defer',
                         rules=[dict(steps=list(range(1, H + 1)), when=TWO_DAYS, action='supply_electives')]), ['d_policies']),
    ('/policies/2', dict(id='campaign', label='Campaña de donantes antes de las fiestas', default_action='supply_electives',
                         rules=[dict(steps=CAMPAIGN_STEPS, when=[], action='campaign_and_electives')]), ['d_policies', 'h_campaign']),
    ('/policies/3', dict(id='campaign_and_defer', label='Campaña y postergación con menos de 2 días', default_action='defer', rules=[
        dict(steps=CAMPAIGN_STEPS, when=TWO_DAYS, action='campaign_and_electives'),
        dict(steps=CAMPAIGN_STEPS, when=[], action='campaign_only'),
        dict(steps=list(range(1, H + 1)), when=TWO_DAYS, action='supply_electives')]), ['d_policies', 'h_campaign']),
]
for i, s in enumerate(['mild', 'moderate', 'severe']):
    FRAGMENTS.append((f'/scenarios/{i}', dict(id=s, label=LABELS[s], events=events(s)), ['d_scenarios', 'h_flu', 'h_demand', 'h_elective']))
FRAGMENTS += [
    ('/law', {'mild': '1/3', 'moderate': '1/3', 'severe': '1/3'}, ['d_law']),
    ('/welfare/0', dict(carrier='surgical_patients', dimension='elective_supply', label='Sangre entregada a cirugías programadas', stock='electives', direction='higher'), ['d_welfare']),
    ('/welfare/1', dict(carrier='red_cross', dimension='reserve', label='Reserva de tipo 0', stock='inventory', direction='higher'), ['d_welfare']),
    ('/welfare/2', dict(carrier='donors', dimension='extra_asks', label='Donaciones extra que quedan sin pedir', stock='donor_pool', direction='higher'), ['d_welfare']),
    ('/task', dict(kind='life_conditions', label='La reserva de tipo 0 nunca baja de un día (7,8 mil unidades)', living_carriers=['emergency_patients'],
                   conditions=[dict(stock='inventory', op='ge', threshold=q(DAY))], require_action_success=False), ['d_life_task']),
    ('/functions/0', dict(id='hospital_supply', kind='health', label='Hospitales abastecidos con 2 días de reserva o más (quincenas cumplidas)', serves=['surgical_patients', 'emergency_patients'],
                          measure='cumulative', when=TWO_DAYS), ['d_functions']),
    ('/functions/1', dict(id='emergency_reserve', kind='safety', label='Reserva de emergencia de un día o más (quincenas cumplidas)', serves=['emergency_patients'],
                          measure='cumulative', when=[dict(kind='stock', stock='inventory', op='ge', value=q(DAY))]), ['d_functions']),
    ('/subsystems/0', dict(id='blood_bank', label='Reserva de la Cruz Roja y donantes', stocks=['inventory', 'donor_pool'], carriers=['red_cross', 'donors', 'emergency_patients']), ['d_subsystems']),
    ('/subsystems/1', dict(id='operating_rooms', label='Cirugías programadas', stocks=['electives'], carriers=['surgical_patients']), ['d_subsystems']),
    ('/interfaces/0', dict(id='elective_distribution', label='Sangre distribuida a cirugías programadas (mil unidades)', source='blood_bank', target='operating_rooms'), ['d_subsystems']),
    ('/require_all_scenarios', True, ['modelling']),
    ('/selection', 'none', ['modelling']),
    ('/assumptions/0', dict(id='Calibration', kind='CALIBRATION', statement='Distribución diaria, parte programada, reserva inicial, efecto de la gripe y efecto de la campaña son hipótesis propias sobre cifras publicadas.', provenance='Claims h_demand, h_elective, h_initial, h_flu, h_campaign'), ['h_demand', 'h_elective', 'h_initial', 'h_flu', 'h_campaign']),
    ('/assumptions/1', dict(id='LifeReserve', kind='NORMATIVE', statement='La condición de vida es no bajar de un día de reserva de tipo 0; cirugías programadas, reserva y pedidos a donantes se comparan como bienestar, sin sumarlos.', provenance='Claims d_life_task, d_welfare'), ['d_life_task', 'd_welfare']),
    ('/assumptions/2', dict(id='FluLaw', kind='PROBABILITY', statement='Un tercio para cada temporada de gripe, declarado: AM-02 tiene 29 temporadas y exige 30. La PVS es condicional a esta ley y se informa su rango bajo toda ley.', provenance='Claim d_law; twin/history/flu_seasons.py'), ['d_law']),
]

ENTITIES = [
    dict(id='inventory', label='Reserva de tipo 0', kind='resource', evidence_ids=['e_crisis']),
    dict(id='electives', label='Cirugías programadas', kind='resource', evidence_ids=['e_share']),
    dict(id='donor_pool', label='Donaciones extra de campaña', kind='resource', evidence_ids=['e_fund']),
    dict(id='emergency_patients', label='Pacientes de trauma y emergencias', kind='person', evidence_ids=['e_crisis']),
    dict(id='surgical_patients', label='Pacientes de cirugías programadas', kind='person', evidence_ids=['e_share']),
    dict(id='red_cross', label='Cruz Roja Americana', kind='organization', evidence_ids=['e_crisis']),
    dict(id='donors', label='Donantes', kind='person', evidence_ids=['e_need']),
]
EVIDENCE = [
    dict(id='e_crisis', observed_at='2026-07-27T12:00:00-04:00', source=SOURCES[0]['origin'], basis='reported', statement='Menos de un día de 0 positivo; distribución de tipo 0 limitada a emergencias.', uncertainty='Comunicado.'),
    dict(id='e_share', observed_at='2026-07-27T12:00:00-04:00', source=SOURCES[0]['origin'], basis='reported', statement='Tipo 0 cerca del 60 % de la distribución; 65 % de la necesidad programada.', uncertainty='Proporciones aproximadas.'),
    dict(id='e_need', observed_at='2026-09-04T12:00:00-06:00', source=SOURCES[2]['origin'], basis='reported', statement='Más de 13.000 donaciones por día.', uncertainty='Cifra redonda.'),
    dict(id='e_fund', observed_at='2026-10-04T12:00:00-04:00', source=SOURCES[3]['origin'], basis='reported', statement='Fondo de 300 millones para la base de donantes.', uncertainty='Nota de prensa.'),
]
RELATIONS = [
    dict(id='org_inv', source='red_cross', target='inventory', kind='organizes', evidence_ids=['e_crisis']),
    dict(id='org_pool', source='red_cross', target='donor_pool', kind='organizes', evidence_ids=['e_fund']),
    dict(id='sup_em', source='inventory', target='emergency_patients', kind='supplies', evidence_ids=['e_crisis']),
    dict(id='sup_el', source='electives', target='surgical_patients', kind='supplies', evidence_ids=['e_share']),
    dict(id='sup_pool', source='donors', target='donor_pool', kind='supplies', evidence_ids=['e_need']),
]
OBSERVATION = dict(format='genius-system-observation/1', label='Sangre tipo 0 en EE.UU., invierno 2026/27',
                   window=dict(start='2026-01-20T00:00:00-05:00', end='2026-10-18T23:59:00-04:00'),
                   entities=ENTITIES, evidence=EVIDENCE, relations=RELATIONS,
                   unknowns=['Reserva actual de la Cruz Roja en unidades o días.', 'Parte de la sangre que va a cirugías que se pueden postergar.',
                             'Efecto de la gripe sobre donaciones separado del de las fiestas y el clima.', 'Otros proveedores (cerca del 60 % del país).'])
SCOPE = dict(format='genius-system-scope/1', observation_revision=1, label='Reserva de tipo 0, cirugías programadas y donantes',
             members=[e['id'] for e in ENTITIES], intervention_entities=['red_cross'], evaluation_entities=[e['id'] for e in ENTITIES],
             bindings=[dict(collection='stocks', model_id=s, entity_id=s) for s in ('inventory', 'electives', 'donor_pool')] +
                      [dict(collection='carriers', model_id=c, entity_id=c) for c in ('emergency_patients', 'surgical_patients', 'red_cross', 'donors')],
             rationale='La Cruz Roja y los hospitales deciden campañas y postergaciones; se evalúan reserva, cirugías y donantes. Fuera de alcance: otros bancos de sangre, plaquetas y plasma.')

WORLD = dict(
    narrative='Caso real con hipótesis declaradas, el primero fuera del agua: tras la crisis de sangre del verano de 2026, la reserva de tipo 0 de la Cruz Roja entra al invierno. Se comparan seguir igual, postergar cirugías programadas cuando la reserva baja de 2 días, una campaña de donantes antes de las fiestas, y ambas, ante gripes leve, moderada y grave.',
    observation=OBSERVATION,
    construction={'format': 'genius-world-construction/1', 'sources': SOURCES, 'claims': CLAIMS,
                  'fragments': [dict(path=p, value=v, claim_ids=c) for p, v, c in FRAGMENTS], 'scope': SCOPE, 'unresolved': []},
    provenance='Interpretación manual de extractos textuales citados y verificados contra las páginas; cifras no citadas declaradas como hipótesis.')

if __name__ == '__main__':
    out = Path(__file__).with_name('world.json')
    out.write_text(json.dumps(WORLD, ensure_ascii=False, indent=2) + '\n')
    print(out)
