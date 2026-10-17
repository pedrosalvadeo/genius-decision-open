"""Builds world.json for the Lake Mead / Lake Powell water year 2027 case from Reclamation's October 2026 studies.

Run: python twin/cases/lake_mead_2027/build.py
Prose quotes are copied verbatim. Table rows are transcribed cell by cell from the
24-Month Study PDFs (elevation in feet / end-of-month storage in 1000 acre-feet).
Every number that is not quoted or transcribed is a hypothesis claim listed in README.md.
"""
import json
from pathlib import Path

MONTHS = ['Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026', 'Jan 2027', 'Feb 2027', 'Mar 2027',
          'Apr 2027', 'May 2027', 'Jun 2027', 'Jul 2027', 'Aug 2027', 'Sep 2027']
# (elevation ft, storage 1000 ac-ft) at the end of each month, Sep 2026 (historical) to Sep 2027.
TABLES = {
    'mp6': dict(
        mead=[('1037.80', 6827), ('1035.29', 6657), ('1033.97', 6568), ('1034.52', 6605), ('1034.33', 6592), ('1033.64', 6547), ('1027.24', 6125),
              ('1019.35', 5624), ('1012.87', 5227), ('1008.47', 4964), ('1007.73', 4920), ('1010.01', 5055), ('1010.85', 5105)],
        powell=[('3518.08', 5155), ('3519.23', 5219), ('3519.44', 5230), ('3518.29', 5166), ('3517.00', 5096), ('3516.28', 5057), ('3516.53', 5070),
                ('3519.97', 5260), ('3533.28', 6034), ('3548.86', 7022), ('3547.97', 6963), ('3543.09', 6645), ('3540.65', 6490)]),
    'mp7': dict(
        mead=[('1037.80', 6827), ('1035.29', 6657), ('1033.97', 6568), ('1034.52', 6605), ('1034.33', 6592), ('1033.64', 6547), ('1027.24', 6125),
              ('1019.35', 5624), ('1015.68', 5397), ('1015.85', 5408), ('1018.43', 5567), ('1024.02', 5918), ('1025.86', 6036)],
        powell=[('3518.08', 5155), ('3519.23', 5219), ('3519.44', 5230), ('3518.29', 5166), ('3517.00', 5096), ('3516.28', 5057), ('3516.53', 5070),
                ('3519.97', 5260), ('3530.48', 5866), ('3542.13', 6584), ('3538.03', 6326), ('3529.28', 5794), ('3525.48', 5573)]),
    'min': dict(
        mead=[('1037.80', 6827), ('1034.98', 6636), ('1033.45', 6534), ('1034.15', 6580), ('1033.82', 6558), ('1033.17', 6515), ('1026.16', 6055),
              ('1017.48', 5508), ('1010.21', 5067), ('1005.04', 4763), ('1003.87', 4696), ('1005.88', 4812), ('1006.43', 4844)],
        powell=[('3518.08', 5155), ('3519.23', 5219), ('3519.44', 5230), ('3518.29', 5166), ('3515.58', 5018), ('3513.27', 4894), ('3511.22', 4785),
                ('3511.03', 4775), ('3512.40', 4847), ('3517.10', 5101), ('3511.76', 4814), ('3503.22', 4375), ('3497.03', 4072)]),
    'max': dict(
        mead=[('1037.80', 6827), ('1035.47', 6669), ('1034.57', 6609), ('1035.36', 6662), ('1035.54', 6674), ('1035.00', 6638), ('1029.71', 6286),
              ('1023.21', 5867), ('1020.67', 5706), ('1021.41', 5753), ('1024.38', 5941), ('1030.49', 6338), ('1032.71', 6484)],
        powell=[('3518.08', 5155), ('3519.50', 5233), ('3520.20', 5273), ('3519.61', 5240), ('3521.79', 5362), ('3524.57', 5520), ('3529.64', 5815),
                ('3540.90', 6506), ('3571.32', 8618), ('3606.71', 11608), ('3609.61', 11881), ('3606.13', 11554), ('3606.39', 11578)]),
}
MIN_2028_MEAD = 'Feb 2028 1002.87 / 4638; Mar 2028 995.09 / 4202'


def table_text(rows):
    return '; '.join(f'{month} {elevation} / {storage}' for month, (elevation, storage) in zip(MONTHS, rows))


def study(rows, footnote, extra=''):
    return ' […] '.join([footnote,
                         'Glen Canyon Dam - Lake Powell, Reservoir Elevation End of Month (Ft) / End Of Month Storage (1000 Ac-Ft): ' + table_text(rows['powell']),
                         'Hoover Dam - Lake Mead, Reservoir Elevation End of Month (Ft) / End Of Month Storage (1000 Ac-Ft): ' + table_text(rows['mead']) + extra])


LC = 'https://www.usbr.gov/lc/region/g4000/'
STUDY_AT = '2026-10-15T12:00:00-07:00'
FOOT6 = 'The October 2026 24-Month Study results in the attached report reflect a 6 maf release from Lake Powell in operating year 2027.'
FOOT7 = 'The October 2026 24-Month Study results in the attached report reflect a 7 maf release from Lake Powell in operating year 2027.'
FOOTMIN = 'The Probable Minimum 24-Month Study includes a release volume from Glen Canyon Dam of 6.00 maf in WY 2027 and WY 2028.'
FOOTMAX = 'The Probable Maximum 24-Month Study includes a release volume from Glen Canyon Dam of 7.00 maf in WY 2027 and 11.50 maf in WY 2028.'
SOURCES = [
    dict(id='usbr_mp6', origin=f'Bureau of Reclamation, "October 2026 Most Probable 24-Month Study: 6 maf Lake Powell Release Scenario", 15/10/2026, {LC}24mo_6.pdf',
         observed_at=STUDY_AT, content=study(TABLES['mp6'], FOOT6)),
    dict(id='usbr_mp7', origin=f'Bureau of Reclamation, "October 2026 Most Probable 24-Month Study: 7 maf Lake Powell Release Scenario", 15/10/2026, {LC}24mo_7.pdf',
         observed_at=STUDY_AT, content=study(TABLES['mp7'], FOOT7)),
    dict(id='usbr_min', origin=f'Bureau of Reclamation, "October 2026 Probable Minimum 24-Month Study", 15/10/2026, {LC}24mo_MIN.pdf',
         observed_at=STUDY_AT, content=study(TABLES['min'], FOOTMIN, '; ' + MIN_2028_MEAD)),
    dict(id='usbr_max', origin=f'Bureau of Reclamation, "October 2026 Probable Maximum 24-Month Study", 15/10/2026, {LC}24mo_MAX.pdf',
         observed_at=STUDY_AT, content=study(TABLES['max'], FOOTMAX)),
    dict(id='doi_aug21', origin='U.S. Department of the Interior / Reclamation, "Interior Department Finalizes Plans for 2027-2028 Colorado River Operations", 21/08/2026, https://www.usbr.gov/newsroom/news-release/5392',
         observed_at='2026-08-21T12:00:00-06:00', content=' […] '.join([
             'Lake Powell will begin the October 1 water year between elevations 3,540 and 3,510 feet,',
             'with an expected water year release between 6.0 and 7.0 million acre-feet.',
             'in order to attempt to maintain an elevation of 3,510 feet or higher',
             'The water year 2027 release volume will be determined in April.',
             'maintaining a minimum elevation of 3,510 feet to support continued operational reliability at Glen Canyon Dam.',
             'For Lake Mead, water deliveries to the Lower Basin States will be reduced by 1.25 million-acre feet for calendar year 2027.'])),
    dict(id='hoodline_oct16', origin='Hoodline, 16/10/2026, https://hoodline.com/2026/10/lake-mead-s-outlook-brightens-but-vegas-s-lifeline-still-sits-near-record-lows',
         observed_at='2026-10-16T12:00:00-07:00', content=' […] '.join([
             'was measured at 1,037.58 feet at noon that day',
             'The 1,000-foot mark is a major concern for water planners',
             'Mead usually hits its low point in July.'])),
    dict(id='nps_capacity', origin='National Park Service, Lake Mead National Recreation Area, "Storage Capacity of Lake Mead", https://www.nps.gov/lake/learn/nature/storage-capacity-of-lake-mead.htm',
         observed_at='2026-10-17T12:00:00-07:00', content=' […] '.join([
             "a 'dead pool' exists at 895 feet in elevation, which is the lowest water outlet at Hoover Dam."])),
]
BY_ID = {s['id']: s for s in SOURCES}


def span(source_id, quote):
    content = BY_ID[source_id]['content']
    start = content.index(quote)
    return dict(source_id=source_id, start=start, end=start + len(quote), quote=quote)


def claim(id, basis, statement, uncertainty, spans=(), premises=()):
    return dict(id=id, basis=basis, statement=statement, uncertainty=uncertainty, spans=list(spans), premises=list(premises))


def rows(key, lake):
    return span('usbr_' + key, table_text(TABLES[key][lake]))


CLAIMS = [
    claim('storage_now', 'measurement', 'Fin de septiembre de 2026 (dato histórico): Lake Mead 1.037,80 pies y 6.827 mil acre-pies; Lake Powell 3.518,08 pies y 5.155 mil acre-pies.',
          'Fila histórica del estudio de octubre; Reclamation puede revisarla en estudios posteriores.',
          [span('usbr_mp6', 'Sep 2026 1037.80 / 6827'), span('usbr_mp6', 'Sep 2026 3518.08 / 5155')]),
    claim('release_range', 'reported', 'Con las directrices 2027-2028, Powell empieza el año hidrológico entre 3.540 y 3.510 pies y se espera liberar entre 6,0 y 7,0 millones de acre-pies; el volumen de 2027 se decide en abril.',
          'Reclamation puede salir de ese rango tras consultas; el modelo sólo compara los dos extremos publicados.',
          [span('doi_aug21', 'Lake Powell will begin the October 1 water year between elevations 3,540 and 3,510 feet,'),
           span('doi_aug21', 'with an expected water year release between 6.0 and 7.0 million acre-feet.'),
           span('doi_aug21', 'The water year 2027 release volume will be determined in April.')]),
    claim('powell_3510', 'reported', 'Interior fija como objetivo mantener Lake Powell en 3.510 pies o más por la confiabilidad operativa de Glen Canyon Dam.',
          'Es un objetivo operativo ("attempt to maintain"), no una garantía.',
          [span('doi_aug21', 'in order to attempt to maintain an elevation of 3,510 feet or higher'),
           span('doi_aug21', 'maintaining a minimum elevation of 3,510 feet to support continued operational reliability at Glen Canyon Dam.')]),
    claim('lower_basin_cut', 'reported', 'Las entregas a los estados de la cuenca baja se reducen 1,25 millones de acre-pies en el año calendario 2027.',
          'Ya incluida por Reclamation en las proyecciones de Lake Mead que usa el modelo.',
          [span('doi_aug21', 'For Lake Mead, water deliveries to the Lower Basin States will be reduced by 1.25 million-acre feet for calendar year 2027.')]),
    claim('mead_1000', 'reported', 'Los 1.000 pies de Lake Mead son una preocupación mayor para los planificadores; el lago suele tocar su mínimo en julio.',
          'Referencia periodística, no una regla operativa.',
          [span('hoodline_oct16', 'The 1,000-foot mark is a major concern for water planners'), span('hoodline_oct16', 'Mead usually hits its low point in July.')]),
    claim('mp6_path', 'reported', 'Trayectoria más probable con 6 millones de acre-pies liberados desde Powell en el año operativo 2027 (fin de cada mes, sep 2026 a sep 2027).',
          'Proyección oficial condicionada a la afluencia más probable.',
          [span('usbr_mp6', FOOT6), rows('mp6', 'powell'), rows('mp6', 'mead')]),
    claim('mp7_path', 'reported', 'Trayectoria más probable con 7 millones de acre-pies liberados desde Powell; idéntica a la de 6 hasta abril de 2027.',
          'Proyección oficial condicionada a la afluencia más probable.',
          [span('usbr_mp7', FOOT7), rows('mp7', 'powell'), rows('mp7', 'mead')]),
    claim('min_path', 'reported', 'Trayectoria con afluencia mínima probable y 6,00 millones de acre-pies liberados en el año hidrológico 2027.',
          'Proyección oficial; no hay estudio mínimo con 7 millones.',
          [span('usbr_min', FOOTMIN), rows('min', 'powell'), rows('min', 'mead')]),
    claim('max_path', 'reported', 'Trayectoria con afluencia máxima probable y 7,00 millones de acre-pies liberados en el año hidrológico 2027.',
          'Proyección oficial; no hay estudio máximo con 6 millones.',
          [span('usbr_max', FOOTMAX), rows('max', 'powell'), rows('max', 'mead')]),
    claim('h_release_effect', 'hypothesis', 'Liberar 7 en vez de 6 millones mueve de Powell a Mead, de mayo a septiembre de 2027, lo que Mead gana entre ambos estudios más probables: 170, 274, 203, 216 y 68 mil acre-pies.',
          'Se supone el mismo efecto con cualquier afluencia. Powell queda hasta 14 mil acre-pies por debajo del estudio de 7 millones (su evaporación menor no se modela), un sesgo prudente.',
          premises=['mp6_path', 'mp7_path']),
    claim('h_cross_scenarios', 'hypothesis', 'Los cruces sin estudio publicado (mínima con 7 millones, máxima con 6) se obtienen sumando o restando ese efecto a los estudios mínimo y máximo.',
          'Construcción propia; los otros cuatro cruces reproducen los estudios publicados.', premises=['h_release_effect', 'min_path', 'max_path']),
    claim('h_powell_storage_3510', 'hypothesis', 'A 3.510 pies, Lake Powell guarda unos 4.724 mil acre-pies (interpolación lineal entre jul 2027, 3.511,76 pies y 4.814, y ago 2027, 3.503,22 pies y 4.375, del estudio mínimo; da 4.723,5 y se redondea hacia arriba).',
          'La relación cota-volumen no es lineal; error esperado de pocos mil acre-pies.',
          [span('usbr_min', 'Jul 2027 3511.76 / 4814; Aug 2027 3503.22 / 4375')], ['powell_3510']),
    claim('h_mead_storage_1000', 'hypothesis', 'A 1.000 pies, Lake Mead guarda unos 4.478 mil acre-pies (interpolación lineal entre feb 2028, 1.002,87 pies y 4.638, y mar 2028, 995,09 pies y 4.202, del estudio mínimo; da 4.477,2 y se redondea hacia arriba).',
          'La relación cota-volumen no es lineal; error esperado de pocos mil acre-pies.',
          [span('usbr_min', MIN_2028_MEAD)], ['mead_1000']),
    claim('mead_dead_pool', 'reported', 'El nivel muerto de Lake Mead está en 895 pies, la salida más baja de Hoover Dam: por debajo, el agua ya no puede salir hacia Arizona, California y México.',
          'Cota física de la presa; el estado del sistema bajo ese nivel no se modela.',
          [span('nps_capacity', "a 'dead pool' exists at 895 feet in elevation, which is the lowest water outlet at Hoover Dam.")]),
    claim('h_mead_dead_storage', 'hypothesis', 'Se toma 2.547 mil acre-pies como almacenamiento de Lake Mead en el nivel muerto. Es la diferencia entre la capacidad total (30.167.000 acre-pies) y la viva (27.620.000) de la tabla de asignación de capacidad de Reclamation de 2022 (https://www.usbr.gov/lc/region/g4000/LakeMeadReservoirCapacityAllocations_2022.pdf).',
          'Si la columna de los 24-Month Study es almacenamiento vivo, el nivel muerto corresponde a 0 y este umbral es prudente; si es total, corresponde a unos 2.547. Con cualquiera de las dos lecturas, superar 2.547 garantiza estar sobre los 895 pies.',
          premises=['mead_dead_pool']),
    claim('d_life_task', 'decision', 'Condición de vida: Lake Mead se mantiene sobre su nivel muerto todos los meses del año hidrológico 2027, de modo que el agua puede seguir llegando a la población de la cuenca baja.',
          'Es la condición material mínima del suministro; no mide cuánta agua recibe cada persona, que se compara como bienestar. Los objetivos de 3.510 pies en Powell y 1.000 pies en Mead son operativos y se miden como funciones del sistema (claim d_functions).',
          premises=['h_mead_dead_storage', 'lower_basin_cut']),
    claim('d_law', 'decision', 'Ley de probabilidad sobre las tres afluencias: un tercio cada una. Es el candidato que elige la enmienda AM-02 al contrastar contra la afluencia no regulada de Lake Powell los estudios de octubre de 2009 a 2025: está calibrado (mínima 5, más probable 6, máxima 2 de 13 octubres) y puntúa mejor que la frecuencia observada.',
          'No está admitida empíricamente: AM-02 exige 30 resultados independientes y hay 13. La PVS que se calcula con ella es condicional a esta ley; el rango bajo toda ley se informa junto a ella.',
          premises=['min_path', 'mp6_path', 'max_path']),
    claim('d_policies', 'decision', 'Opciones comparadas: liberar 6 o 7 millones de acre-pies desde Powell en el año operativo 2027, los dos volúmenes que Reclamation proyecta.',
          'Volúmenes intermedios o menores a 6 no tienen proyección publicada y quedan fuera.', premises=['release_range', 'mp6_path', 'mp7_path']),
    claim('d_welfare', 'decision', 'El bienestar de los usuarios de la cuenca baja se representa por el agua en Lake Mead; el de la operación de Glen Canyon Dam, por el agua en Lake Powell (más es mejor).',
          'Representación elegida por el modelizador; ninguna de las partes la declaró.', premises=['lower_basin_cut', 'powell_3510']),
    claim('d_functions', 'decision', 'Funciones del sistema (módulo I), medidas en cada gemelo proyectado como meses cumplidos hasta cada momento: Glen Canyon Dam opera con Powell en 3.510 pies o más (unos 4.724 mil acre-pies), y Hoover entrega a la cuenca baja con Mead en 1.000 pies o más (unos 4.478).',
          'Más meses cumplidos es mejor; no se suman entre funciones. Los volúmenes son interpolaciones; los 1.000 pies son una referencia periodística, no una regla operativa.',
          premises=['powell_3510', 'h_powell_storage_3510', 'mead_1000', 'h_mead_storage_1000']),
    claim('d_subsystems', 'decision', 'Subsistemas (módulo II): Lake Powell con la operación de Glen Canyon Dam, y Lake Mead con la cuenca baja. Los une la liberación de Glen Canyon hacia Mead; la interfaz registra la liberación adicional a los 6 millones de acre-pies.',
          'La liberación base de 6 millones ya está dentro de las proyecciones de cada lago, así que la interfaz sólo mide lo que la decisión cambia.', premises=['release_range', 'powell_3510', 'lower_basin_cut', 'h_release_effect']),
    claim('modelling', 'definition', 'Unidad: mil acre-pies de almacenamiento a fin de mes. Paso mensual: paso 0 = fin de septiembre de 2026, paso k = fin de cada mes de octubre de 2026 a septiembre de 2027. Los escenarios son las tres afluencias que publica Reclamation. La ley sobre las afluencias se declara aparte (claim d_law). La capacidad de 30.000 es una cota de modelado, no la física.',
          'No se modelan otros embalses, la generación eléctrica ni el reparto entre estados.', premises=['storage_now']),
]

H = 12
MAY = 8  # step 8 = end of May 2027
EFFECT = ['170/1', '274/1', '203/1', '216/1', '68/1']  # May..Sep, Mead gain from 7 instead of 6 maf
LABELS = dict(minimum='Afluencia mínima probable', most_probable='Afluencia más probable', maximum='Afluencia máxima probable')


def cumulative_effect():
    total, out = 0, [0] * (H + 1)
    for step in range(MAY, H + 1):
        total += int(EFFECT[step - MAY].split('/')[0])
        out[step] = total
    return out


def base_series():
    """Storage under the 6 maf release for each inflow scenario."""
    effect = cumulative_effect()
    storage = {key: {lake: [s for _, s in TABLES[key][lake]] for lake in ('mead', 'powell')} for key in TABLES}
    maximum = dict(mead=[v - e for v, e in zip(storage['max']['mead'], effect)],
                   powell=[v + e for v, e in zip(storage['max']['powell'], effect)])
    return dict(minimum=storage['min'], most_probable=storage['mp6'], maximum=maximum)


def events(series):
    out = []
    for step in range(1, H + 1):
        inflows, drains = {}, {}
        for lake, values in series.items():
            change = values[step] - values[step - 1]
            if change > 0:
                inflows[lake] = f'{change}/1'
            elif change < 0:
                drains[lake] = f'{-change}/1'
        out.append(dict(inflows=inflows, renewables={}, drains=drains, remove_capabilities=[]))
    return out


EXTRA = ['may', 'jun', 'jul', 'aug', 'sep']
FRAGMENTS = [
    ('/profile', 'STOCK_FLOW_FINITE_V1', ['modelling']),
    ('/name', 'Lake Mead y Lake Powell: año hidrológico 2027', ['modelling']),
    ('/horizon', H, ['modelling']),
    ('/step_unit', 'step', ['modelling']),
    ('/stocks/0', dict(id='mead', label='Almacenamiento de Lake Mead', unit='kaf', kind='persistent', initial='6827/1', capacity='30000/1'), ['storage_now', 'modelling']),
    ('/stocks/1', dict(id='powell', label='Almacenamiento de Lake Powell', unit='kaf', kind='persistent', initial='5155/1', capacity='30000/1'), ['storage_now', 'modelling']),
    ('/carriers/0', dict(id='lower_basin', label='Población y usuarios de la cuenca baja (Arizona, California, Nevada)', kind='person'), ['lower_basin_cut']),
    ('/carriers/1', dict(id='glen_canyon', label='Operación de Glen Canyon Dam', kind='organization'), ['powell_3510']),
    ('/capabilities/0', dict(id='glen_release', label='Glen Canyon Dam liberando agua hacia Lake Mead'), ['modelling']),
    ('/initial_capabilities/0', 'glen_release', ['modelling']),
    ('/actions/0', dict(id='base_release', label='Liberación del volumen de 6 millones', requires=[], withdrawals={}, deposits={}, add_capabilities=[], remove_capabilities=[]), ['mp6_path']),
]
for i, (month, amount) in enumerate(zip(EXTRA, EFFECT), 1):
    FRAGMENTS.append((f'/actions/{i}', dict(id='extra_' + month, label=f'Liberación adicional del volumen de 7 millones ({month})', requires=['glen_release'],
                                            withdrawals={'powell': amount}, deposits={'mead': amount}, add_capabilities=[], remove_capabilities=[]), ['h_release_effect']))
FRAGMENTS += [
    ('/policies/0', dict(id='release_6', label='Liberar 6 millones de acre-pies en 2027', default_action='base_release', rules=[]), ['d_policies']),
    ('/policies/1', dict(id='release_7', label='Liberar 7 millones de acre-pies en 2027', default_action='base_release',
                         rules=[dict(steps=[MAY + i], when=[], action='extra_' + month) for i, month in enumerate(EXTRA)]), ['d_policies', 'h_release_effect']),
]
for i, (scenario, series) in enumerate(base_series().items()):
    FRAGMENTS.append((f'/scenarios/{i}', dict(id=scenario, label=LABELS[scenario], events=events(series)), ['mp6_path', 'min_path', 'max_path', 'h_cross_scenarios']))
FRAGMENTS += [
    ('/law', {'minimum': '1/3', 'most_probable': '1/3', 'maximum': '1/3'}, ['d_law']),
    ('/welfare/0', dict(carrier='lower_basin', dimension='mead_reserve', label='Agua almacenada en Lake Mead', stock='mead', direction='higher'), ['d_welfare']),
    ('/welfare/1', dict(carrier='glen_canyon', dimension='powell_reserve', label='Agua almacenada en Lake Powell', stock='powell', direction='higher'), ['d_welfare']),
    ('/task', dict(kind='life_conditions', label='Lake Mead sobre su nivel muerto (895 pies) todos los meses: el agua sigue llegando a la cuenca baja', living_carriers=['lower_basin'],
                   conditions=[dict(stock='mead', op='ge', threshold='2547/1')],
                   require_action_success=False), ['d_life_task']),
    ('/functions/0', dict(id='glen_canyon_3510', label='Glen Canyon Dam opera con Powell en 3.510 pies o más (meses cumplidos)', serves=['glen_canyon'],
                          measure='cumulative', when=[dict(kind='stock', stock='powell', op='ge', value='4724/1')]), ['d_functions']),
    ('/functions/1', dict(id='mead_1000', label='Lake Mead en 1.000 pies o más para la cuenca baja (meses cumplidos)', serves=['lower_basin'],
                          measure='cumulative', when=[dict(kind='stock', stock='mead', op='ge', value='4478/1')]), ['d_functions']),
    ('/subsystems/0', dict(id='powell_sub', label='Lake Powell y Glen Canyon Dam', stocks=['powell'], carriers=['glen_canyon']), ['d_subsystems']),
    ('/subsystems/1', dict(id='mead_sub', label='Lake Mead y la cuenca baja', stocks=['mead'], carriers=['lower_basin']), ['d_subsystems']),
    ('/interfaces/0', dict(id='glen_release', label='Liberación de Glen Canyon a Lake Mead, adicional a 6 millones (mil acre-pies)', source='powell_sub', target='mead_sub'), ['d_subsystems']),
    ('/require_all_scenarios', True, ['modelling']),
    ('/selection', 'none', ['modelling']),
    ('/assumptions/0', dict(id='ReleaseEffect', kind='CALIBRATION', statement='El efecto de liberar 7 en vez de 6 millones se toma de los estudios más probables y se supone igual con cualquier afluencia.', provenance='Claims h_release_effect, h_cross_scenarios'), ['h_release_effect', 'h_cross_scenarios']),
    ('/assumptions/1', dict(id='DeadPoolStorage', kind='CALIBRATION', statement='El nivel muerto de Lake Mead se representa con 2.547 mil acre-pies, prudente con cualquier lectura de la columna de almacenamiento.', provenance='Claims mead_dead_pool, h_mead_dead_storage'), ['h_mead_dead_storage']),
    ('/assumptions/2', dict(id='LifeCondition', kind='NORMATIVE', statement='La condición de vida es que el agua pueda seguir saliendo de Lake Mead hacia la cuenca baja; cuánta agua recibe cada portador se compara como bienestar, sin sumarlo.', provenance='Claim d_life_task'), ['d_life_task']),
    ('/assumptions/3', dict(id='InflowLaw', kind='PROBABILITY', statement='Un tercio para cada afluencia: candidato calibrado de AM-02 sobre 13 octubres, no admitido (se exigen 30). La PVS es condicional a esta ley.', provenance='Claim d_law; twin/history/empirical_law.py --driver inflow'), ['d_law']),
]

ENTITIES = [
    dict(id='mead', label='Lake Mead', kind='resource', evidence_ids=['e_storage']),
    dict(id='powell', label='Lake Powell', kind='resource', evidence_ids=['e_storage']),
    dict(id='lower_basin', label='Población y usuarios de la cuenca baja', kind='person', evidence_ids=['e_cut']),
    dict(id='glen_canyon', label='Operación de Glen Canyon Dam', kind='organization', evidence_ids=['e_release']),
]
EVIDENCE = [
    dict(id='e_storage', observed_at=STUDY_AT, source=SOURCES[0]['origin'], basis='measurement', statement='Fin de septiembre de 2026: Mead 6.827 y Powell 5.155 mil acre-pies.', uncertainty='Fila histórica del estudio de octubre.'),
    dict(id='e_release', observed_at='2026-08-21T12:00:00-06:00', source=SOURCES[4]['origin'], basis='reported', statement='Liberación esperada de Powell entre 6,0 y 7,0 millones de acre-pies en 2027, decidida en abril, con objetivo de 3.510 pies.', uncertainty='Puede salir del rango tras consultas.'),
    dict(id='e_cut', observed_at='2026-08-21T12:00:00-06:00', source=SOURCES[4]['origin'], basis='reported', statement='Entregas a la cuenca baja reducidas 1,25 millones de acre-pies en 2027.', uncertainty='Reparto entre estados no modelado.'),
]
RELATIONS = [
    dict(id='powell_to_mead', source='powell', target='mead', kind='supplies', evidence_ids=['e_release']),
    dict(id='ops_powell', source='glen_canyon', target='powell', kind='organizes', evidence_ids=['e_release']),
    dict(id='mead_basin', source='mead', target='lower_basin', kind='supplies', evidence_ids=['e_cut']),
]
OBSERVATION = dict(format='genius-system-observation/1', label='Lake Mead y Lake Powell: año hidrológico 2027',
                   window=dict(start='2026-08-21T00:00:00-06:00', end='2026-10-16T23:59:00-07:00'),
                   entities=ENTITIES, evidence=EVIDENCE, relations=RELATIONS,
                   unknowns=['Liberaciones de Powell distintas de 6 y 7 millones de acre-pies.', 'Probabilidad admitida de cada afluencia (la declarada no alcanza los 30 resultados que exige AM-02).',
                             'Efectos sobre la generación eléctrica, México y los ecosistemas del Gran Cañón.'])
SCOPE = dict(format='genius-system-scope/1', observation_revision=1, label='Powell, Mead y quienes dependen de ellos',
             members=['mead', 'powell', 'lower_basin', 'glen_canyon'], intervention_entities=['glen_canyon'],
             evaluation_entities=['mead', 'powell', 'lower_basin', 'glen_canyon'],
             bindings=[dict(collection='stocks', model_id='mead', entity_id='mead'), dict(collection='stocks', model_id='powell', entity_id='powell'),
                       dict(collection='carriers', model_id='lower_basin', entity_id='lower_basin'),
                       dict(collection='carriers', model_id='glen_canyon', entity_id='glen_canyon')],
             rationale='La liberación desde Glen Canyon Dam es la decisión; se evalúan ambos embalses y quienes dependen de ellos. Fuera de alcance: cuenca alta, México y otros embalses.')

WORLD = dict(
    narrative='Caso real con proyecciones oficiales: Lake Mead y Lake Powell empiezan el año hidrológico 2027 en mínimos. En abril Reclamation decide si Powell libera 6 o 7 millones de acre-pies. Se comparan ambas opciones ante una afluencia mínima, más probable o máxima.',
    observation=OBSERVATION,
    construction={'format': 'genius-world-construction/1', 'sources': SOURCES, 'claims': CLAIMS,
                  'fragments': [dict(path=p, value=v, claim_ids=c) for p, v, c in FRAGMENTS], 'scope': SCOPE, 'unresolved': []},
    provenance='Proyecciones oficiales de Reclamation transcritas de sus tablas y extractos textuales citados; cifras no citadas declaradas como hipótesis.')

if __name__ == '__main__':
    out = Path(__file__).with_name('world.json')
    out.write_text(json.dumps(WORLD, ensure_ascii=False, indent=2) + '\n')
    print(out)
