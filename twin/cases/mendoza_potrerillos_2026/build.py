"""Builds world.json for the Mendoza River / Potrerillos 2026/27 case from cited excerpts.

Run: python twin/cases/mendoza_potrerillos_2026/build.py
Quotes are copied verbatim from the cited pages; every number that is not quoted
is a hypothesis or decision claim and is listed in README.md for review.
"""
from fractions import Fraction
import json
from pathlib import Path

SOURCES = [
    dict(id='dgi_forecast', origin='Departamento General de Irrigación, "Informe de la situación hídrica a partir del Pronóstico de Escurrimientos temporada 2026/2027", https://www.irrigacion.gov.ar/web/2026/10/02/informe-de-la-situacion-hidrica-a-partir-del-pronostico-de-escurrimientos-temporada-2026-2027/',
         observed_at='2026-10-02T12:00:00-03:00', content=' […] '.join([
             'En la Temporada 25/26 escurrieron 797 hm 3.',
             'se espera un derrame de 1780 hm³, lo que representa el 129% respecto de un año medio para la sección de aforos Guido.'])),
    dict(id='mdz_oct15', origin='MDZ Online, 2026-10-15, https://www.mdzol.com/sociedad/2026/10/15/la-impresionante-transformacion-de-potrerillos-bajante-historica-a-la-espera-de-las-crecidas-1988461.html',
         observed_at='2026-10-15T12:00:00-03:00', content=' […] '.join([
             'Potrerillos acumula 171 hectómetros cúbicos de agua.',
             'La capacidad máxima consignada para el embalse es de 395 hectómetros cúbicos',
             'el embalse se encuentra actualmente al 43% de su capacidad de almacenamiento',
             'el valor histórico informado desde 2010 es de 265 hectómetros cúbicos',
             'El mayor aporte comenzará con los primeros deshielos del verano'])),
    dict(id='elsol', origin='El Sol, "Irrigación pronosticó más agua, pero advierte un dato sobre Potrerillos", https://www.elsol.com.ar/mendoza/irrigacion-pronostico-mas-agua-pero-advierte-un-dato-sobre-potrerillos/',
         observed_at='2026-10-02T12:00:00-03:00', content=' […] '.join([
             'el embalse Potrerillos aparece clasificado con reservas extremadamente bajas',
             'le tenemos que restar los casi 300 del uso potable',
             'quedan unos 500 para el agro',
             'Para diciembre de 2026, Irrigación estima un derrame de 300 hm³',
             'para enero de 2027 prevé 320 hm³',
             'con 250 hm³ proyectados',
             'para el ciclo 2026-2027 se estima un derrame de 1.780 hectómetros cúbicos (hm³)'])),
    dict(id='diariouno', origin='Diario Uno, "El pronóstico de Irrigación: Va a sobrar agua equivalente al embalse Potrerillos en 1 año y medio", https://www.diariouno.com.ar/sociedad/el-pronostico-irrigacion-va-sobrar-agua-equivalente-al-embalse-potrerillos-1-ano-y-medio-n1602168',
         observed_at='2026-10-03T12:00:00-03:00', content=' […] '.join([
             'El año pasado fue un año de 800 hectómetros y este año llegaremos a 1.800 hectómetros.',
             'va a sobrar aproximadamente en 1 año y medio el volumen equivalente al embalse Potrerillos.',
             'recuperación de ecosistemas como las lagunas de Rosario',
             'el agua puede salirse del cauce, romper calles e inundar fincas'])),
]
BY_ID = {s['id']: s for s in SOURCES}


def span(source_id, quote):
    content = BY_ID[source_id]['content']
    start = content.index(quote)
    return dict(source_id=source_id, start=start, end=start + len(quote), quote=quote)


def claim(id, basis, statement, uncertainty, spans=(), premises=()):
    return dict(id=id, basis=basis, statement=statement, uncertainty=uncertainty, spans=list(spans), premises=list(premises))


CLAIMS = [
    claim('storage_now', 'reported', 'Potrerillos almacena 171 hm³ de 395 hm³ de capacidad (43 %) a mediados de octubre de 2026; reservas clasificadas como extremadamente bajas.',
          'Cifras de boletín de Irrigación reproducidas por la prensa.',
          [span('mdz_oct15', 'Potrerillos acumula 171 hectómetros cúbicos de agua.'),
           span('mdz_oct15', 'La capacidad máxima consignada para el embalse es de 395 hectómetros cúbicos'),
           span('elsol', 'el embalse Potrerillos aparece clasificado con reservas extremadamente bajas')]),
    claim('forecast', 'reported', 'Pronóstico oficial del río Mendoza para 2026/27: 1780 hm³ (129 % de un año medio); en 2025/26 escurrieron 797 hm³.',
          'Pronóstico de escurrimiento, no medición; en 2025/26 el pronóstico inicial (845 hm³) resultó mayor que lo escurrido.',
          [span('dgi_forecast', 'se espera un derrame de 1780 hm³, lo que representa el 129% respecto de un año medio para la sección de aforos Guido.'),
           span('dgi_forecast', 'En la Temporada 25/26 escurrieron 797 hm 3.')]),
    claim('monthly_peak', 'reported', 'Derrames mensuales previstos: diciembre 300 hm³, enero 320 hm³, febrero 250 hm³.', 'Pronóstico mensual citado por la prensa.',
          [span('elsol', 'Para diciembre de 2026, Irrigación estima un derrame de 300 hm³'), span('elsol', 'para enero de 2027 prevé 320 hm³'),
           span('elsol', 'con 250 hm³ proyectados')]),
    claim('uses', 'reported', 'Del volumen anual, casi 300 hm³ van a uso potable y unos 500 hm³ quedaron para el agro en un año de 800 hm³.',
          'Declaración del titular de Irrigación sobre el año anterior; no es una dotación fijada para 2026/27.',
          [span('elsol', 'le tenemos que restar los casi 300 del uso potable'), span('elsol', 'quedan unos 500 para el agro'),
           span('diariouno', 'El año pasado fue un año de 800 hectómetros y este año llegaremos a 1.800 hectómetros.')]),
    claim('surplus_uses', 'reported', 'Irrigación prevé agua sobrante, menciona la recuperación de ecosistemas como las lagunas de Rosario y advierte riesgo de desbordes.',
          'Declaraciones públicas, sin volúmenes asignados.',
          [span('diariouno', 'va a sobrar aproximadamente en 1 año y medio el volumen equivalente al embalse Potrerillos.'),
           span('diariouno', 'recuperación de ecosistemas como las lagunas de Rosario'),
           span('diariouno', 'el agua puede salirse del cauce, romper calles e inundar fincas')]),
    claim('h_monthly', 'hypothesis', 'Reparto mensual del pronóstico (noviembre a septiembre): 120, 300, 320, 250, 185, 110, 85, 75, 75, 75, 85 hm³; suma 1680, el resto de los 1780 corresponde a octubre de 2026, ya transcurrido al inicio. Diciembre a febrero son los citados; el resto es reparto propio.',
          'Supuesto propio sobre la forma del hidrograma fuera de los tres meses citados. Requiere el pronóstico mensual completo de Irrigación.', premises=['forecast', 'monthly_peak']),
    claim('h_scenarios', 'hypothesis', 'Escenarios: el pronóstico; por debajo del pronóstico en la misma proporción que 2025/26 (797/845); y un año como 2025/26 (797 hm³ en total). Los dos últimos escalan el reparto mensual.',
          'Supuesto propio; no hay escenarios publicados por Irrigación.', premises=['forecast', 'h_monthly']),
    claim('h_potable', 'hypothesis', 'El uso potable retira 25 hm³ por mes del embalse (300 hm³ por año).', 'Reparto uniforme propio; el consumo real varía por estación.', premises=['uses']),
    claim('h_agro', 'hypothesis', 'Temporada de riego en el horizonte: noviembre a mayo (7 meses). Dotación de año seco: 62,5 hm³ por mes (500 hm³ repartidos en 8 meses de temporada); reforzada: 93,75 hm³ por mes (1,5 veces).',
          'Meses y refuerzo de 1,5 veces son supuestos propios; Irrigación no publicó dotaciones 2026/27.', premises=['uses']),
    claim('d_ecology', 'decision', 'Entrega ecológica a las lagunas: 20 hm³ en cada mes que empiece con el embalse en 355 hm³ (90 %) o más.',
          'Opción planteada por el modelizador a partir de la mención pública de las lagunas; volumen y umbral son elección propia.', premises=['surplus_uses', 'storage_now']),
    claim('d_life_task', 'decision', 'Condición de vida: Potrerillos guarda en todo momento al menos 25 hm³, un mes de agua potable para la población abastecida por el río Mendoza.',
          'Elegida por el modelizador como condición material del agua de consumo humano; no es una regla de Irrigación. El ecosistema de las lagunas no tiene todavía un umbral citado y se compara como bienestar.',
          premises=['h_potable', 'uses']),
    claim('d_law', 'decision', 'Ley de probabilidad declarada sobre los tres escenarios: un tercio cada uno.',
          'Sin respaldo empírico todavía: no hay archivo de pronósticos del río Mendoza contrastado con AM-02. La PVS es condicional a esta ley; cuando el rango bajo toda ley es un único valor, el resultado no depende de ella.',
          premises=['h_scenarios']),
    claim('d_policies', 'decision', 'Opciones: dotación de año seco; dotación reforzada; dotación reforzada más entrega ecológica cuando el embalse está casi lleno.',
          'Opciones planteadas por el modelizador; no son propuestas oficiales.', premises=['uses', 'surplus_uses']),
    claim('d_org_welfare', 'decision', 'El bienestar de Irrigación como organización se representa por la reserva de Potrerillos (más es mejor).',
          'Representación elegida por el modelizador; Irrigación no publicó una métrica propia.', premises=['storage_now']),
    claim('d_functions', 'decision', 'Función del sistema (módulo I), medida en cada gemelo proyectado como meses cumplidos hasta cada momento: Potrerillos conserva margen para amortiguar crecidas, con 355 hm³ (90 %) o menos.',
          'Más meses cumplidos es mejor. El margen de 10 % es elección del modelizador, el mismo umbral de la entrega ecológica; Irrigación advierte riesgo de desbordes pero no publicó un margen.', premises=['surplus_uses', 'storage_now']),
    claim('d_subsystems', 'decision', 'Subsistemas (módulo II): Potrerillos con Irrigación y la población abastecida; el riego con los regantes; las lagunas con su ecosistema. Los unen las entregas de riego y la entrega ecológica.',
          'Representación del modelizador; no se modelan canales, diques aguas abajo ni acuíferos.', premises=['uses', 'surplus_uses', 'h_agro', 'd_ecology']),
    claim('modelling', 'definition', 'Unidad hm³. Paso mensual de noviembre de 2026 a septiembre de 2027 (11 pasos; el límite de salida del gemelo impide un paso más con tres escenarios y tres opciones). El escurrimiento entra al embalse; lo que excede la capacidad se registra como derrame no controlado aguas abajo. Riego y entrega ecológica se acumulan como agua entregada. La ley sobre los escenarios se declara aparte (claim d_law).',
          'No se modelan diques aguas abajo (Cipolletti), acuíferos, generación eléctrica ni pérdidas de conducción.', premises=['storage_now', 'forecast']),
]

H = 11
FORECAST = [120, 300, 320, 250, 185, 110, 85, 75, 75, 75, 85]
SCALE = dict(forecast=Fraction(1), below=Fraction(797, 845), like_2025=Fraction(797, 1780))
LABELS = dict(forecast='Pronóstico oficial (1780 hm³)', below='Por debajo del pronóstico como en 2025/26', like_2025='Año como 2025/26 (797 hm³)')
IRRIGATION = [1, 2, 3, 4, 5, 6, 7]  # Nov..May


def q(x):
    x = Fraction(x)
    return f'{x.numerator}/{x.denominator}'


def events(scenario):
    return [dict(inflows={'potrerillos': q(v * SCALE[scenario])}, renewables={}, drains={'potrerillos': '25/1'}, remove_capabilities=[]) for v in FORECAST]


def release(id, label, stock, amount):
    return dict(id=id, label=label, requires=['operate'], withdrawals={'potrerillos': q(amount)}, deposits={stock: q(amount)}, add_capabilities=[], remove_capabilities=[])


FRAGMENTS = [
    ('/profile', 'STOCK_FLOW_FINITE_V1', ['modelling']),
    ('/name', 'Río Mendoza y Potrerillos: temporada 2026/27', ['modelling']),
    ('/horizon', H, ['modelling']),
    ('/step_unit', 'step', ['modelling']),
    ('/stocks/0', dict(id='potrerillos', label='Embalse Potrerillos', unit='hm3', kind='persistent', initial='171/1', capacity='395/1'), ['storage_now']),
    ('/stocks/1', dict(id='agro', label='Agua entregada a riego (acumulada)', unit='hm3', kind='persistent', initial='0/1', capacity='5000/1'), ['modelling', 'h_agro']),
    ('/stocks/2', dict(id='lagoons', label='Agua entregada a las lagunas (acumulada)', unit='hm3', kind='persistent', initial='0/1', capacity='5000/1'), ['modelling', 'd_ecology']),
    ('/carriers/0', dict(id='irrigators', label='Regantes del río Mendoza', kind='person'), ['uses']),
    ('/carriers/1', dict(id='lagoon_ecosystem', label='Ecosistema de las lagunas', kind='living'), ['surplus_uses']),
    ('/carriers/2', dict(id='dgi', label='Departamento General de Irrigación', kind='organization'), ['storage_now']),
    ('/carriers/3', dict(id='residents', label='Población abastecida con agua potable del río Mendoza', kind='person'), ['uses']),
    ('/capabilities/0', dict(id='operate', label='Operación del embalse'), ['modelling']),
    ('/initial_capabilities/0', 'operate', ['modelling']),
    ('/actions/0', dict(id='hold', label='Sin entregas de riego', requires=[], withdrawals={}, deposits={}, add_capabilities=[], remove_capabilities=[]), ['modelling']),
    ('/actions/1', release('dry_allocation', 'Riego con dotación de año seco', 'agro', Fraction(125, 2)), ['h_agro']),
    ('/actions/2', release('reinforced_allocation', 'Riego con dotación reforzada', 'agro', Fraction(375, 4)), ['h_agro']),
    ('/actions/3', dict(id='reinforced_and_lagoons', label='Riego reforzado y entrega a las lagunas', requires=['operate'],
                        withdrawals={'potrerillos': q(Fraction(375, 4) + 20)}, deposits={'agro': q(Fraction(375, 4)), 'lagoons': '20/1'}, add_capabilities=[], remove_capabilities=[]), ['h_agro', 'd_ecology']),
    ('/actions/4', release('lagoons_only', 'Entrega a las lagunas fuera de temporada de riego', 'lagoons', 20), ['d_ecology']),
    ('/policies/0', dict(id='dry_allocation', label='Dotación de año seco', default_action='hold', rules=[dict(steps=IRRIGATION, when=[], action='dry_allocation')]), ['d_policies']),
    ('/policies/1', dict(id='reinforced', label='Dotación reforzada', default_action='hold', rules=[dict(steps=IRRIGATION, when=[], action='reinforced_allocation')]), ['d_policies']),
    ('/policies/2', dict(id='reinforced_lagoons', label='Reforzada y lagunas con embalse casi lleno', default_action='hold', rules=[
        dict(steps=IRRIGATION, when=[dict(kind='stock', stock='potrerillos', op='ge', value='355/1')], action='reinforced_and_lagoons'),
        dict(steps=IRRIGATION, when=[], action='reinforced_allocation'),
        dict(steps=[s for s in range(1, H + 1) if s not in IRRIGATION], when=[dict(kind='stock', stock='potrerillos', op='ge', value='355/1')], action='lagoons_only')]), ['d_policies', 'd_ecology']),
]
for i, s in enumerate(['forecast', 'below', 'like_2025']):
    FRAGMENTS.append((f'/scenarios/{i}', dict(id=s, label=LABELS[s], events=events(s)), ['h_monthly', 'h_scenarios', 'h_potable']))
FRAGMENTS += [
    ('/law', {'forecast': '1/3', 'below': '1/3', 'like_2025': '1/3'}, ['d_law']),
    ('/welfare/0', dict(carrier='irrigators', dimension='irrigation', label='Agua entregada para riego', stock='agro', direction='higher'), ['uses', 'h_agro']),
    ('/welfare/1', dict(carrier='lagoon_ecosystem', dimension='lagoon_water', label='Agua entregada a las lagunas', stock='lagoons', direction='higher'), ['surplus_uses', 'd_ecology']),
    ('/welfare/2', dict(carrier='dgi', dimension='reserve', label='Reserva de Potrerillos', stock='potrerillos', direction='higher'), ['d_org_welfare']),
    ('/task', dict(kind='life_conditions', label='Guardar siempre al menos un mes de agua potable (25 hm³) en Potrerillos', living_carriers=['residents'],
                   conditions=[dict(stock='potrerillos', op='ge', threshold='25/1')], require_action_success=False), ['d_life_task']),
    ('/functions/0', dict(id='flood_margin', kind='flood_margin', label='Potrerillos con margen para amortiguar crecidas: 355 hm³ (90 %) o menos (meses cumplidos)', serves=['residents', 'irrigators'],
                          measure='cumulative', when=[dict(kind='stock', stock='potrerillos', op='le', value='355/1')]), ['d_functions']),
    ('/subsystems/0', dict(id='reservoir', label='Embalse Potrerillos', stocks=['potrerillos'], carriers=['dgi', 'residents']), ['d_subsystems']),
    ('/subsystems/1', dict(id='irrigation', label='Riego del río Mendoza', stocks=['agro'], carriers=['irrigators']), ['d_subsystems']),
    ('/subsystems/2', dict(id='lagoons_sub', label='Lagunas de Rosario', stocks=['lagoons'], carriers=['lagoon_ecosystem']), ['d_subsystems']),
    ('/interfaces/0', dict(id='irrigation_delivery', label='Entregas de riego desde Potrerillos (hm³)', source='reservoir', target='irrigation'), ['d_subsystems']),
    ('/interfaces/1', dict(id='ecological_delivery', label='Entrega ecológica desde Potrerillos a las lagunas (hm³)', source='reservoir', target='lagoons_sub'), ['d_subsystems']),
    ('/require_all_scenarios', True, ['modelling']),
    ('/selection', 'none', ['modelling']),
    ('/assumptions/0', dict(id='Calibration', kind='CALIBRATION', statement='Reparto mensual, escenarios, consumo potable mensual y dotaciones son hipótesis propias sobre cifras publicadas.', provenance='Claims h_monthly, h_scenarios, h_potable, h_agro'), ['h_monthly', 'h_agro']),
    ('/assumptions/1', dict(id='LifeReserve', kind='NORMATIVE', statement='La condición de vida es guardar un mes de agua potable (25 hm³); riego, lagunas y reserva se comparan como bienestar, sin sumarlos. La regla de entrega ecológica es elección del modelizador.', provenance='Claims d_life_task, d_ecology'), ['d_life_task', 'd_ecology']),
    ('/assumptions/2', dict(id='ScenarioLaw', kind='PROBABILITY', statement='Un tercio para cada escenario, declarado sin respaldo empírico; la PVS es condicional a esta ley y se informa su rango bajo toda ley.', provenance='Claim d_law'), ['d_law']),
]

ENTITIES = [
    dict(id='potrerillos', label='Embalse Potrerillos', kind='resource', evidence_ids=['e_storage']),
    dict(id='agro', label='Riego agrícola', kind='resource', evidence_ids=['e_uses']),
    dict(id='lagoons', label='Entrega a lagunas', kind='resource', evidence_ids=['e_lagoons']),
    dict(id='irrigators', label='Regantes', kind='person', evidence_ids=['e_uses']),
    dict(id='lagoon_ecosystem', label='Ecosistema de las lagunas', kind='living', evidence_ids=['e_lagoons']),
    dict(id='dgi', label='Departamento General de Irrigación', kind='organization', evidence_ids=['e_storage']),
    dict(id='residents', label='Población con agua potable', kind='person', evidence_ids=['e_uses']),
]
EVIDENCE = [
    dict(id='e_storage', observed_at='2026-10-15T12:00:00-03:00', source=SOURCES[1]['origin'], basis='reported', statement='Potrerillos con 171 hm³ de 395 hm³.', uncertainty='Boletín citado por la prensa.'),
    dict(id='e_uses', observed_at='2026-10-02T12:00:00-03:00', source=SOURCES[2]['origin'], basis='reported', statement='Casi 300 hm³ de uso potable y unos 500 hm³ para el agro en el año anterior.', uncertainty='Declaración pública.'),
    dict(id='e_lagoons', observed_at='2026-10-03T12:00:00-03:00', source=SOURCES[3]['origin'], basis='reported', statement='Irrigación menciona la recuperación de las lagunas con el agua sobrante.', uncertainty='Sin volumen asignado.'),
]
RELATIONS = [
    dict(id='org_res', source='dgi', target='potrerillos', kind='organizes', evidence_ids=['e_storage']),
    dict(id='org_agro', source='dgi', target='agro', kind='organizes', evidence_ids=['e_uses']),
    dict(id='org_lag', source='dgi', target='lagoons', kind='organizes', evidence_ids=['e_lagoons']),
    dict(id='sup_agro', source='agro', target='irrigators', kind='supplies', evidence_ids=['e_uses']),
    dict(id='sup_lag', source='lagoons', target='lagoon_ecosystem', kind='supplies', evidence_ids=['e_lagoons']),
    dict(id='sup_potable', source='potrerillos', target='residents', kind='supplies', evidence_ids=['e_uses']),
]
OBSERVATION = dict(format='genius-system-observation/1', label='Río Mendoza y Potrerillos 2026/27',
                   window=dict(start='2026-10-02T00:00:00-03:00', end='2026-10-15T23:59:00-03:00'),
                   entities=ENTITIES, evidence=EVIDENCE, relations=RELATIONS,
                   unknowns=['Pronóstico mensual completo y dotaciones 2026/27.', 'Número de personas abastecidas y umbral ecológico de las lagunas.',
                             'Acuífero, dique Cipolletti, generación eléctrica y riesgo de crecidas aguas abajo.'])
SCOPE = dict(format='genius-system-scope/1', observation_revision=1, label='Embalse, agua potable, riego y lagunas',
             members=[e['id'] for e in ENTITIES], intervention_entities=['dgi'], evaluation_entities=[e['id'] for e in ENTITIES],
             bindings=[dict(collection='stocks', model_id=s, entity_id=s) for s in ('potrerillos', 'agro', 'lagoons')] +
                      [dict(collection='carriers', model_id=c, entity_id=c) for c in ('irrigators', 'lagoon_ecosystem', 'dgi', 'residents')],
             rationale='Irrigación decide entregas; se evalúan embalse, riego y lagunas. Fuera de alcance: acuífero, energía y crecidas.')

WORLD = dict(
    narrative='Caso real con hipótesis declaradas: Potrerillos empieza la temporada 2026/27 al 43 % tras un año seco, con un pronóstico húmedo de 1780 hm³. Se comparan tres reglas de entrega para riego y lagunas ante el pronóstico, un año algo menor y un año como 2025/26.',
    observation=OBSERVATION,
    construction={'format': 'genius-world-construction/1', 'sources': SOURCES, 'claims': CLAIMS,
                  'fragments': [dict(path=p, value=v, claim_ids=c) for p, v, c in FRAGMENTS], 'scope': SCOPE, 'unresolved': []},
    provenance='Interpretación manual de extractos textuales citados; cifras no citadas declaradas como hipótesis.')

if __name__ == '__main__':
    out = Path(__file__).with_name('world.json')
    out.write_text(json.dumps(WORLD, ensure_ascii=False, indent=2) + '\n')
    print(out)
