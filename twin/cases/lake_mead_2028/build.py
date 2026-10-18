"""Builds world.json for Lake Mead / Lake Powell over water years 2027 and 2028 from Reclamation's October 2026 studies.

Run: python twin/cases/lake_mead_2028/build.py
Same sources as lake_mead_2027, now with all 24 projected months. Table rows are
transcribed from the 24-Month Study PDFs (elevation ft / end-of-month storage in
1000 acre-feet; the archive twin/history/lake_mead/studies.csv keeps each PDF's
sha256). Every number that is not quoted or transcribed is a hypothesis claim.
"""
import json
from pathlib import Path

YEARS = [(2026, 9)] + [(2026 + (m > 12) + (m > 24), (m - 1) % 12 + 1) for m in range(10, 34)]
NAMES = 'Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split()
MONTHS = [f'{NAMES[m - 1]} {y}' for y, m in YEARS]
# (elevation ft, storage 1000 ac-ft) at the end of each month, Sep 2026 (historical) to Sep 2028.
TABLES = {
    'mp6': dict(
        mead=[('1037.80', 6827), ('1035.29', 6657), ('1033.97', 6568), ('1034.52', 6605), ('1034.33', 6592), ('1033.64', 6547), ('1027.24', 6125),
              ('1019.35', 5624), ('1012.87', 5227), ('1008.47', 4964), ('1007.73', 4920), ('1010.01', 5055), ('1010.85', 5105), ('1011.99', 5174),
              ('1011.81', 5163), ('1014.25', 5310), ('1019.95', 5662), ('1024.22', 5931), ('1022.58', 5827), ('1018.20', 5552), ('1012.74', 5219),
              ('1009.36', 5016), ('1009.85', 5045), ('1013.16', 5244), ('1014.81', 5344)],
        powell=[('3518.08', 5155), ('3519.23', 5219), ('3519.44', 5230), ('3518.29', 5166), ('3517.00', 5096), ('3516.28', 5057), ('3516.53', 5070),
              ('3519.97', 5260), ('3533.28', 6034), ('3548.86', 7022), ('3547.97', 6963), ('3543.09', 6645), ('3540.65', 6490), ('3540.09', 6455),
              ('3538.87', 6378), ('3535.54', 6171), ('3529.21', 5791), ('3524.68', 5526), ('3521.54', 5348), ('3523.29', 5447), ('3538.63', 6363),
              ('3557.16', 7587), ('3555.35', 7462), ('3549.95', 7095), ('3546.58', 6872)]),
    'mp7': dict(
        mead=[('1037.80', 6827), ('1035.29', 6657), ('1033.97', 6568), ('1034.52', 6605), ('1034.33', 6592), ('1033.64', 6547), ('1027.24', 6125),
              ('1019.35', 5624), ('1015.68', 5397), ('1015.85', 5408), ('1018.43', 5567), ('1024.02', 5918), ('1025.86', 6036), ('1026.87', 6102),
              ('1026.66', 6088), ('1028.91', 6234), ('1032.47', 6468), ('1034.98', 6636), ('1031.79', 6424), ('1026.10', 6052), ('1019.31', 5621),
              ('1014.39', 5318), ('1013.01', 5235), ('1014.29', 5312), ('1014.43', 5321)],
        powell=[('3518.08', 5155), ('3519.23', 5219), ('3519.44', 5230), ('3518.29', 5166), ('3517.00', 5096), ('3516.28', 5057), ('3516.53', 5070),
              ('3519.97', 5260), ('3530.48', 5866), ('3542.13', 6584), ('3538.03', 6326), ('3529.28', 5794), ('3525.48', 5573), ('3524.91', 5540),
              ('3523.60', 5464), ('3519.97', 5260), ('3515.12', 4993), ('3512.06', 4830), ('3510.69', 4757), ('3514.35', 4952), ('3532.11', 5963),
              ('3552.79', 7287), ('3552.59', 7272), ('3548.91', 7025), ('3546.90', 6893)]),
    'min': dict(
        mead=[('1037.80', 6827), ('1034.98', 6636), ('1033.45', 6534), ('1034.15', 6580), ('1033.82', 6558), ('1033.17', 6515), ('1026.16', 6055),
              ('1017.48', 5508), ('1010.21', 5067), ('1005.04', 4763), ('1003.87', 4696), ('1005.88', 4812), ('1006.43', 4844), ('1005.97', 4817),
              ('1003.92', 4699), ('1003.25', 4660), ('1003.28', 4662), ('1002.87', 4638), ('995.09', 4202), ('989.43', 3895), ('985.88', 3708),
              ('983.53', 3586), ('982.43', 3530), ('984.94', 3659), ('985.87', 3707)],
        powell=[('3518.08', 5155), ('3519.23', 5219), ('3519.44', 5230), ('3518.29', 5166), ('3515.58', 5018), ('3513.27', 4894), ('3511.22', 4785),
              ('3511.03', 4775), ('3512.40', 4847), ('3517.10', 5101), ('3511.76', 4814), ('3503.22', 4375), ('3497.03', 4072), ('3495.61', 4004),
              ('3494.43', 3948), ('3493.05', 3884), ('3491.39', 3807), ('3490.99', 3788), ('3492.71', 3868), ('3496.20', 4032), ('3507.95', 4615),
              ('3519.10', 5211), ('3513.49', 4906), ('3506.00', 4515), ('3501.61', 4295)]),
    'max': dict(
        mead=[('1037.80', 6827), ('1035.47', 6669), ('1034.57', 6609), ('1035.36', 6662), ('1035.54', 6674), ('1035.00', 6638), ('1029.71', 6286),
              ('1023.21', 5867), ('1020.67', 5706), ('1021.41', 5753), ('1024.38', 5941), ('1030.49', 6338), ('1032.71', 6484), ('1036.83', 6761),
              ('1039.20', 6923), ('1043.50', 7221), ('1053.32', 7925), ('1060.97', 8497), ('1063.68', 8705), ('1063.84', 8717), ('1062.97', 8650),
              ('1064.41', 8761), ('1069.31', 9145), ('1076.33', 9709), ('1081.03', 10097)],
        powell=[('3518.08', 5155), ('3519.50', 5233), ('3520.20', 5273), ('3519.61', 5240), ('3521.79', 5362), ('3524.57', 5520), ('3529.64', 5815),
              ('3540.90', 6506), ('3571.32', 8618), ('3606.71', 11608), ('3609.61', 11881), ('3606.13', 11554), ('3606.39', 11578), ('3606.63', 11600),
              ('3605.83', 11526), ('3602.74', 11240), ('3595.52', 10593), ('3589.55', 10078), ('3584.15', 9629), ('3584.15', 9630), ('3600.52', 11038),
              ('3617.70', 12676), ('3617.81', 12686), ('3611.99', 12111), ('3608.21', 11749)]),
}


def table_text(rows):
    return '; '.join(f'{month} {elevation} / {storage}' for month, (elevation, storage) in zip(MONTHS, rows))


def study(rows, footnote):
    return ' […] '.join([footnote,
                         'Glen Canyon Dam - Lake Powell, Reservoir Elevation End of Month (Ft) / End Of Month Storage (1000 Ac-Ft): ' + table_text(rows['powell']),
                         'Hoover Dam - Lake Mead, Reservoir Elevation End of Month (Ft) / End Of Month Storage (1000 Ac-Ft): ' + table_text(rows['mead'])])


LC = 'https://www.usbr.gov/lc/region/g4000/'
STUDY_AT = '2026-10-15T12:00:00-07:00'
FOOT6 = 'The October 2026 24-Month Study results in the attached report reflect a 6 maf release from Lake Powell in operating year 2027.'
FOOT7 = 'The October 2026 24-Month Study results in the attached report reflect a 7 maf release from Lake Powell in operating year 2027.'
FOOTMIN = 'The Probable Minimum 24-Month Study includes a release volume from Glen Canyon Dam of 6.00 maf in WY 2027 and WY 2028.'
FOOTMAX = 'The Probable Maximum 24-Month Study includes a release volume from Glen Canyon Dam of 7.00 maf in WY 2027 and 11.50 maf in WY 2028.'
POWER_POOL = '3,490 ft – minimum power pool'
NO_POWER = "below this level Glen Canyon Dam's ability to release water is reduced and it can no longer produce hydropower."
SOURCES = [
    dict(id='usbr_mp6', origin=f'Bureau of Reclamation, "October 2026 Most Probable 24-Month Study: 6 maf Lake Powell Release Scenario", 15/10/2026, {LC}24mo_6.pdf',
         observed_at=STUDY_AT, content=study(TABLES['mp6'], FOOT6)),
    dict(id='usbr_mp7', origin=f'Bureau of Reclamation, "October 2026 Most Probable 24-Month Study: 7 maf Lake Powell Release Scenario", 15/10/2026, {LC}24mo_7.pdf',
         observed_at=STUDY_AT, content=study(TABLES['mp7'], FOOT7)),
    dict(id='usbr_min', origin=f'Bureau of Reclamation, "October 2026 Probable Minimum 24-Month Study", 15/10/2026, {LC}24mo_MIN.pdf',
         observed_at=STUDY_AT, content=study(TABLES['min'], FOOTMIN)),
    dict(id='usbr_max', origin=f'Bureau of Reclamation, "October 2026 Probable Maximum 24-Month Study", 15/10/2026, {LC}24mo_MAX.pdf',
         observed_at=STUDY_AT, content=study(TABLES['max'], FOOTMAX)),
    dict(id='doi_aug21', origin='U.S. Department of the Interior / Reclamation, "Interior Department Finalizes Plans for 2027-2028 Colorado River Operations", 21/08/2026, https://www.usbr.gov/newsroom/news-release/5392',
         observed_at='2026-08-21T12:00:00-06:00', content=' […] '.join([
             'with an expected water year release between 6.0 and 7.0 million acre-feet.',
             'The water year 2027 release volume will be determined in April.',
             'maintaining a minimum elevation of 3,510 feet to support continued operational reliability at Glen Canyon Dam.',
             'For Lake Mead, water deliveries to the Lower Basin States will be reduced by 1.25 million-acre feet for calendar year 2027.'])),
    dict(id='usbr_5282', origin='Bureau of Reclamation, comunicado https://www.usbr.gov/newsroom/news-release/5282 (extractos tomados del índice del buscador el 17/10/2026; la página no se pudo abrir desde el entorno de construcción)',
         observed_at='2026-10-17T12:00:00-07:00', content=' […] '.join([POWER_POOL, NO_POWER])),
    dict(id='hoodline_oct16', origin='Hoodline, 16/10/2026, https://hoodline.com/2026/10/lake-mead-s-outlook-brightens-but-vegas-s-lifeline-still-sits-near-record-lows',
         observed_at='2026-10-16T12:00:00-07:00', content='The 1,000-foot mark is a major concern for water planners'),
    dict(id='nps_capacity', origin='National Park Service, Lake Mead National Recreation Area, "Storage Capacity of Lake Mead", https://www.nps.gov/lake/learn/nature/storage-capacity-of-lake-mead.htm',
         observed_at='2026-10-17T12:00:00-07:00', content="a 'dead pool' exists at 895 feet in elevation, which is the lowest water outlet at Hoover Dam."),
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


# Monthly states in WY2027, quarterly in WY2028: 2 routes x 3 inflows x 17 states fit the
# occurrence limit, and the evaluation artifact fits production's output limit.
STATES = list(range(13)) + [15, 18, 21, 24]  # indices into MONTHS: Sep 2026..Sep 2027, Dec 2027, Mar, Jun, Sep 2028
H = len(STATES) - 1
MAY = 8  # step 8 = end of May 2027; step 12 = Sep 2027; steps 13-16 = end of each WY2028 quarter
EXTRA = [('may', 170), ('jun', 274), ('jul', 203), ('aug', 216), ('sep', 68)]  # WY2027, Mead gain from 7 instead of 6 maf
# WY2028: Mead's loss of that gain between the two most probable studies, per quarter. Oct-Dec (3+3+1,
# evaporation) is not modelled; Jan-Mar 118+101+108, Apr-Jun 97+98+100, Jul-Sep 112+122+91.
LESS = {14: 327, 15: 295, 16: 325}
POWER_KAF = 3742

CLAIMS = [
    claim('storage_now', 'measurement', 'Fin de septiembre de 2026 (dato histórico): Lake Mead 1.037,80 pies y 6.827 mil acre-pies; Lake Powell 3.518,08 pies y 5.155 mil acre-pies.',
          'Fila histórica del estudio de octubre; Reclamation puede revisarla en estudios posteriores.',
          [span('usbr_mp6', 'Sep 2026 1037.80 / 6827'), span('usbr_mp6', 'Sep 2026 3518.08 / 5155')]),
    claim('release_range', 'reported', 'Se espera que Powell libere entre 6,0 y 7,0 millones de acre-pies en el año hidrológico 2027; el volumen se decide en abril.',
          'Reclamation puede salir de ese rango tras consultas; el modelo compara los dos extremos publicados.',
          [span('doi_aug21', 'with an expected water year release between 6.0 and 7.0 million acre-feet.'),
           span('doi_aug21', 'The water year 2027 release volume will be determined in April.')]),
    claim('powell_3510', 'reported', 'Interior fija como objetivo mantener Lake Powell en 3.510 pies o más por la confiabilidad operativa de Glen Canyon Dam.',
          'Objetivo operativo, no garantía.',
          [span('doi_aug21', 'maintaining a minimum elevation of 3,510 feet to support continued operational reliability at Glen Canyon Dam.')]),
    claim('lower_basin_cut', 'reported', 'Las entregas a los estados de la cuenca baja se reducen 1,25 millones de acre-pies en el año calendario 2027.',
          'Ya incluida en las proyecciones; las reglas de 2028 son las que Reclamation usó en sus estudios.',
          [span('doi_aug21', 'For Lake Mead, water deliveries to the Lower Basin States will be reduced by 1.25 million-acre feet for calendar year 2027.')]),
    claim('mead_1000', 'reported', 'Los 1.000 pies de Lake Mead son una preocupación mayor para los planificadores.',
          'Referencia periodística, no una regla operativa.', [span('hoodline_oct16', 'The 1,000-foot mark is a major concern for water planners')]),
    claim('power_pool', 'reported', 'La cota mínima de generación de Glen Canyon Dam es 3.490 pies: por debajo, la presa ve reducida su capacidad de liberar agua y deja de generar electricidad.',
          'Texto tomado de los extractos que muestra el buscador del comunicado de Reclamation, no de la página abierta; la cota de 3.490 pies coincide con otros documentos de Reclamation (Registro de Decisión post-2026).',
          [span('usbr_5282', POWER_POOL), span('usbr_5282', NO_POWER)]),
    claim('mp6_path', 'reported', 'Trayectoria más probable con 6 millones de acre-pies liberados desde Powell en el año operativo 2027, de septiembre de 2026 a septiembre de 2028.',
          'Proyección oficial condicionada a la afluencia más probable; la liberación de 2028 es la que Reclamation proyecta con sus reglas.',
          [span('usbr_mp6', FOOT6), rows('mp6', 'powell'), rows('mp6', 'mead')]),
    claim('mp7_path', 'reported', 'Trayectoria más probable con 7 millones de acre-pies liberados desde Powell en 2027, de septiembre de 2026 a septiembre de 2028.',
          'Proyección oficial; idéntica a la de 6 hasta abril de 2027.',
          [span('usbr_mp7', FOOT7), rows('mp7', 'powell'), rows('mp7', 'mead')]),
    claim('min_path', 'reported', 'Trayectoria con afluencia mínima probable y 6,00 millones de acre-pies liberados en 2027 y en 2028.',
          'Proyección oficial; no hay estudio mínimo con 7 millones.',
          [span('usbr_min', FOOTMIN), rows('min', 'powell'), rows('min', 'mead')]),
    claim('max_path', 'reported', 'Trayectoria con afluencia máxima probable: 7,00 millones liberados en 2027 y 11,50 en 2028.',
          'Proyección oficial; no hay estudio máximo con 6 millones en 2027.',
          [span('usbr_max', FOOTMAX), rows('max', 'powell'), rows('max', 'mead')]),
    claim('h_release_effect', 'hypothesis', 'Liberar 7 en vez de 6 millones en 2027 mueve de Powell a Mead, de mayo a septiembre de 2027, 170, 274, 203, 216 y 68 mil acre-pies (931 en total), lo que Mead gana entre ambos estudios más probables.',
          'Se supone el mismo efecto con cualquier afluencia; la menor evaporación de Powell no se modela (hasta 14 mil acre-pies de sesgo prudente).',
          premises=['mp6_path', 'mp7_path']),
    claim('h_effect_2028', 'hypothesis', 'En el año hidrológico 2028, según los dos estudios más probables, la ruta de 7 millones libera menos que la de 6: Mead pierde esa ventaja y termina 23 mil acre-pies por debajo. El modelo lo representa como agua que deja de pasar de Powell a Mead en cada trimestre de 2028: 327 mil acre-pies de enero a marzo (118, 101 y 108), 295 de abril a junio (97, 98 y 100) y 325 de julio a septiembre (112, 122 y 91).',
          'Octubre a diciembre de 2027 (3, 3 y 1, evaporación) no se modelan. Se supone igual con cualquier afluencia, aunque en la afluencia mínima Reclamation podría liberar todavía menos.',
          premises=['mp6_path', 'mp7_path']),
    claim('h_cross_scenarios', 'hypothesis', 'Los cruces sin estudio publicado (mínima con 7 millones, máxima con 6) se obtienen sumando o restando ambos efectos a los estudios mínimo y máximo.',
          'Construcción propia. Los otros cuatro cruces reproducen los estudios publicados, salvo 7 millones con afluencia más probable: en 2028 Mead se aparta hasta 7 mil acre-pies y Powell hasta 20 (evaporación no modelada).',
          premises=['h_release_effect', 'h_effect_2028', 'min_path', 'max_path']),
    claim('h_powell_storage_3510', 'hypothesis', 'A 3.510 pies, Lake Powell guarda unos 4.724 mil acre-pies (interpolación lineal entre jul 2027, 3.511,76 pies y 4.814, y ago 2027, 3.503,22 pies y 4.375, del estudio mínimo).',
          'La relación cota-volumen no es lineal; error esperado de pocos mil acre-pies.',
          [span('usbr_min', 'Jul 2027 3511.76 / 4814; Aug 2027 3503.22 / 4375')], ['powell_3510']),
    claim('h_powell_storage_3490', 'hypothesis', f'A 3.490 pies, Lake Powell guarda unos {POWER_KAF:,} mil acre-pies'.replace(',', '.') + ' (extrapolación lineal desde ene 2028, 3.491,39 pies y 3.807, y feb 2028, 3.490,99 pies y 3.788, del estudio mínimo: da 3.741,0 y se redondea hacia arriba).',
          'Extrapola un pie fuera de las filas publicadas; error esperado de pocos mil acre-pies. En febrero de 2028, dentro de un trimestre que el modelo no mide mes a mes, el estudio mínimo con 6 millones deja a Powell 46 mil acre-pies (cerca de un pie) sobre ese umbral.',
          [span('usbr_min', 'Jan 2028 3491.39 / 3807; Feb 2028 3490.99 / 3788')], ['power_pool']),
    claim('h_mead_storage_1000', 'hypothesis', 'A 1.000 pies, Lake Mead guarda unos 4.478 mil acre-pies (interpolación lineal entre feb 2028, 1.002,87 pies y 4.638, y mar 2028, 995,09 pies y 4.202, del estudio mínimo).',
          'La relación cota-volumen no es lineal; error esperado de pocos mil acre-pies.',
          [span('usbr_min', 'Feb 2028 1002.87 / 4638; Mar 2028 995.09 / 4202')], ['mead_1000']),
    claim('mead_dead_pool', 'reported', 'El nivel muerto de Lake Mead está en 895 pies, la salida más baja de Hoover Dam.',
          'Cota física de la presa.', [span('nps_capacity', "a 'dead pool' exists at 895 feet in elevation, which is the lowest water outlet at Hoover Dam.")]),
    claim('h_mead_dead_storage', 'hypothesis', 'Se toma 2.547 mil acre-pies como almacenamiento de Lake Mead en el nivel muerto (capacidad total menos viva en la tabla de Reclamation de 2022, https://www.usbr.gov/lc/region/g4000/LakeMeadReservoirCapacityAllocations_2022.pdf).',
          'Prudente con cualquier lectura de la columna de almacenamiento (viva o total).', premises=['mead_dead_pool']),
    claim('d_life_task', 'decision', 'Condición de vida: Lake Mead se mantiene sobre su nivel muerto todos los meses de los años hidrológicos 2027 y 2028, de modo que el agua puede seguir llegando a la población de la cuenca baja.',
          'Condición material mínima del suministro; cuánta agua recibe cada portador se compara como bienestar.', premises=['h_mead_dead_storage', 'lower_basin_cut']),
    claim('d_law', 'decision', 'Ley de probabilidad: un tercio para cada afluencia de dos años (mínima, más probable y máxima), el candidato calibrado de AM-02 para el primer año.',
          'Para el primer año AM-02 la admite sobre los últimos 30 años de afluencia de Powell (twin/history/powell_law.py; con el registro completo desde 1964 admitiría 12/65, 27/65 y 2/5) y la calibró con 13 octubres de estudios; para el segundo año no está contrastada y los estudios mínimo y máximo encadenan dos años extremos. La PVS es condicional a esta ley; el rango bajo toda ley se informa junto a ella.',
          premises=['min_path', 'mp6_path', 'max_path']),
    claim('d_policies', 'decision', 'Opciones comparadas: liberar 6 o 7 millones de acre-pies desde Powell en 2027, con la liberación de 2028 que Reclamation proyecta en cada caso.',
          'Volúmenes intermedios o menores a 6 no tienen proyección publicada.', premises=['release_range', 'mp6_path', 'mp7_path', 'h_effect_2028']),
    claim('d_welfare', 'decision', 'El bienestar de los usuarios de la cuenca baja se representa por el agua en Lake Mead; el de la operación de Glen Canyon Dam, por el agua en Lake Powell (más es mejor).',
          'Representación elegida por el modelizador.', premises=['lower_basin_cut', 'powell_3510']),
    claim('d_power', 'decision', 'Capacidad generativa (módulo III): Glen Canyon Dam genera electricidad sólo con Powell en 3.490 pies o más (unos 3.742 mil acre-pies). La capacidad sigue al estado: se pierde bajo ese nivel y vuelve si Powell lo recupera.',
          'Los clientes de esa electricidad no se modelan como portadores. La CAG del kernel siempre incluye la organización de origen, así que perder la generación no la cambia; la pérdida se ve en la organización de cada mes y en la función de meses con generación (claim d_functions).',
          premises=['power_pool', 'h_powell_storage_3490']),
    claim('d_functions', 'decision', 'Funciones del sistema (módulo I), como estados cumplidos hasta cada momento (un estado es un mes en 2027 y un trimestre en 2028): Glen Canyon opera con Powell en 3.510 pies o más; Glen Canyon genera electricidad; Hoover entrega a la cuenca baja con Mead en 1.000 pies o más.',
          'Más meses cumplidos es mejor; no se suman entre funciones.',
          premises=['powell_3510', 'h_powell_storage_3510', 'd_power', 'mead_1000', 'h_mead_storage_1000']),
    claim('d_subsystems', 'decision', 'Subsistemas (módulo II): Lake Powell con Glen Canyon Dam, y Lake Mead con la cuenca baja. Dos interfaces: la liberación adicional de 2027 hacia Mead, y la liberación de 2028 que la ruta de 7 millones deja de hacer (queda en Powell).',
          'Las liberaciones base ya están dentro de las proyecciones; las interfaces miden lo que la decisión cambia.',
          premises=['h_release_effect', 'h_effect_2028']),
    claim('modelling', 'definition', 'Unidad: mil acre-pies de almacenamiento a fin de mes. Paso 0 = fin de septiembre de 2026; pasos 1 a 12 = fin de cada mes hasta septiembre de 2027; pasos 13 a 16 = fin de cada trimestre del año hidrológico 2028 (diciembre, marzo, junio y septiembre). En 2028 no se mide lo que ocurre dentro de cada trimestre. Escenarios: las tres afluencias de Reclamation. La capacidad de 30.000 es una cota de modelado.',
          'No se modelan otros embalses, el reparto entre estados ni la menor capacidad de liberar bajo 3.490 pies.', premises=['storage_now']),
]
LABELS = dict(minimum='Afluencia mínima probable (dos años)', most_probable='Afluencia más probable (dos años)', maximum='Afluencia máxima probable (dos años)')


def cumulative_effect():
    """Water moved from Powell to Mead by the 7 maf route, up to each step."""
    total, out = 0, [0] * (H + 1)
    for step in range(1, H + 1):
        if MAY <= step < MAY + len(EXTRA):
            total += EXTRA[step - MAY][1]
        total -= LESS.get(step, 0)
        out[step] = total
    return out


def base_series():
    """Storage under the 6 maf route for each inflow scenario."""
    effect = cumulative_effect()
    storage = {key: {lake: [TABLES[key][lake][i][1] for i in STATES] for lake in ('mead', 'powell')} for key in TABLES}
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


AMOUNTS = sorted(set(LESS.values()))
FRAGMENTS = [
    ('/profile', 'STOCK_FLOW_FINITE_V1', ['modelling']),
    ('/name', 'Lake Mead y Lake Powell: años hidrológicos 2027 y 2028', ['modelling']),
    ('/horizon', H, ['modelling']),
    ('/step_unit', 'step', ['modelling']),
    ('/stocks/0', dict(id='mead', label='Almacenamiento de Lake Mead', unit='kaf', kind='persistent', initial='6827/1', capacity='30000/1'), ['storage_now', 'modelling']),
    ('/stocks/1', dict(id='powell', label='Almacenamiento de Lake Powell', unit='kaf', kind='persistent', initial='5155/1', capacity='30000/1'), ['storage_now', 'modelling']),
    ('/carriers/0', dict(id='lower_basin', label='Población y usuarios de la cuenca baja (Arizona, California, Nevada)', kind='person'), ['lower_basin_cut']),
    ('/carriers/1', dict(id='glen_canyon', label='Operación de Glen Canyon Dam', kind='organization'), ['powell_3510']),
    ('/capabilities/0', dict(id='glen_release', label='Glen Canyon Dam liberando agua hacia Lake Mead'), ['modelling']),
    ('/capabilities/1', dict(id='glen_power', label='Glen Canyon Dam generando electricidad (Powell en 3.490 pies o más)',
                             holds_when=[dict(kind='stock', stock='powell', op='ge', value=f'{POWER_KAF}/1')]), ['d_power']),
    ('/initial_capabilities/0', 'glen_release', ['modelling']),
    ('/actions/0', dict(id='base_release', label='Liberación del volumen de la ruta de 6 millones', requires=[], withdrawals={}, deposits={}, add_capabilities=[], remove_capabilities=[]), ['mp6_path']),
]
for i, (month, amount) in enumerate(EXTRA, 1):
    FRAGMENTS.append((f'/actions/{i}', dict(id='extra_' + month, label=f'Liberación adicional del volumen de 7 millones ({month} 2027)', requires=['glen_release'],
                                            withdrawals={'powell': f'{amount}/1'}, deposits={'mead': f'{amount}/1'}, add_capabilities=[], remove_capabilities=[]), ['h_release_effect']))
for i, amount in enumerate(AMOUNTS, len(EXTRA) + 1):
    FRAGMENTS.append((f'/actions/{i}', dict(id=f'less_{amount}', label=f'Liberación trimestral de 2028 menor en {amount} mil acre-pies que la de la ruta de 6 millones', requires=['glen_release'],
                                            withdrawals={'mead': f'{amount}/1'}, deposits={'powell': f'{amount}/1'}, add_capabilities=[], remove_capabilities=[]), ['h_effect_2028']))
FRAGMENTS += [
    ('/policies/0', dict(id='release_6', label='Liberar 6 millones de acre-pies en 2027', default_action='base_release', rules=[]), ['d_policies']),
    ('/policies/1', dict(id='release_7', label='Liberar 7 millones de acre-pies en 2027 (y menos en 2028, según Reclamation)', default_action='base_release',
                         rules=[dict(steps=[MAY + i], when=[], action='extra_' + month) for i, (month, _) in enumerate(EXTRA)]
                         + [dict(steps=sorted(s for s, a in LESS.items() if a == amount), when=[], action=f'less_{amount}') for amount in AMOUNTS]),
     ['d_policies', 'h_release_effect', 'h_effect_2028']),
]
for i, (scenario, series) in enumerate(base_series().items()):
    FRAGMENTS.append((f'/scenarios/{i}', dict(id=scenario, label=LABELS[scenario], events=events(series)), ['mp6_path', 'min_path', 'max_path', 'h_cross_scenarios']))
FRAGMENTS += [
    ('/law', {'minimum': '1/3', 'most_probable': '1/3', 'maximum': '1/3'}, ['d_law']),
    ('/welfare/0', dict(carrier='lower_basin', dimension='mead_reserve', label='Agua almacenada en Lake Mead', stock='mead', direction='higher'), ['d_welfare']),
    ('/welfare/1', dict(carrier='glen_canyon', dimension='powell_reserve', label='Agua almacenada en Lake Powell', stock='powell', direction='higher'), ['d_welfare']),
    ('/task', dict(kind='life_conditions', label='Lake Mead sobre su nivel muerto (895 pies) todos los meses de 2027 y 2028: el agua sigue llegando a la cuenca baja', living_carriers=['lower_basin'],
                   conditions=[dict(stock='mead', op='ge', threshold='2547/1')], require_action_success=False), ['d_life_task']),
    ('/functions/0', dict(id='glen_canyon_3510', kind='infrastructure', label='Glen Canyon Dam opera con Powell en 3.510 pies o más (estados cumplidos)', serves=['glen_canyon'],
                          measure='cumulative', when=[dict(kind='stock', stock='powell', op='ge', value='4724/1')]), ['d_functions']),
    ('/functions/1', dict(id='glen_generating', kind='energy', label='Glen Canyon Dam genera electricidad (estados cumplidos)', serves=['glen_canyon'],
                          measure='cumulative', when=[dict(kind='capability', capability='glen_power', present=True)]), ['d_functions']),
    ('/functions/2', dict(id='mead_1000', kind='water', label='Lake Mead en 1.000 pies o más para la cuenca baja (estados cumplidos)', serves=['lower_basin'],
                          measure='cumulative', when=[dict(kind='stock', stock='mead', op='ge', value='4478/1')]), ['d_functions']),
    ('/subsystems/0', dict(id='powell_sub', label='Lake Powell y Glen Canyon Dam', stocks=['powell'], carriers=['glen_canyon']), ['d_subsystems']),
    ('/subsystems/1', dict(id='mead_sub', label='Lake Mead y la cuenca baja', stocks=['mead'], carriers=['lower_basin']), ['d_subsystems']),
    ('/interfaces/0', dict(id='glen_release', label='Liberación de Glen Canyon a Lake Mead adicional a la ruta de 6 millones, 2027 (mil acre-pies)', source='powell_sub', target='mead_sub'), ['d_subsystems']),
    ('/interfaces/1', dict(id='release_withheld_2028', label='Liberación de 2028 que la ruta de 7 millones deja en Powell (mil acre-pies)', source='mead_sub', target='powell_sub'), ['d_subsystems']),
    ('/require_all_scenarios', True, ['modelling']),
    ('/selection', 'none', ['modelling']),
    ('/assumptions/0', dict(id='ReleaseEffect', kind='CALIBRATION', statement='El efecto de liberar 7 en vez de 6 millones en 2027, y la menor liberación de 2028 que sigue, se toman de los estudios más probables y se suponen iguales con cualquier afluencia.', provenance='Claims h_release_effect, h_effect_2028, h_cross_scenarios'), ['h_release_effect', 'h_effect_2028', 'h_cross_scenarios']),
    ('/assumptions/1', dict(id='DeadPoolStorage', kind='CALIBRATION', statement='El nivel muerto de Lake Mead se representa con 2.547 mil acre-pies.', provenance='Claims mead_dead_pool, h_mead_dead_storage'), ['h_mead_dead_storage']),
    ('/assumptions/2', dict(id='PowerPoolStorage', kind='CALIBRATION', statement='La cota mínima de generación de Glen Canyon (3.490 pies) se representa con 3.742 mil acre-pies, extrapolando un pie desde el estudio mínimo.', provenance='Claims power_pool, h_powell_storage_3490'), ['h_powell_storage_3490']),
    ('/assumptions/3', dict(id='LifeCondition', kind='NORMATIVE', statement='La condición de vida es que el agua pueda seguir saliendo de Lake Mead hacia la cuenca baja; cuánta agua recibe cada portador se compara como bienestar, sin sumarlo.', provenance='Claim d_life_task'), ['d_life_task']),
    ('/assumptions/4', dict(id='InflowLaw', kind='PROBABILITY', statement='Un tercio para cada afluencia de dos años: ley admitida por AM-02 para el primer año sobre los últimos 30 años de afluencia de Powell (1996-2025); no contrastada para el segundo. La PVS es condicional a esta ley.', provenance='Claim d_law; twin/history/powell_law.py; twin/history/empirical_law.py --driver inflow'), ['d_law']),
]

ENTITIES = [
    dict(id='mead', label='Lake Mead', kind='resource', evidence_ids=['e_storage']),
    dict(id='powell', label='Lake Powell', kind='resource', evidence_ids=['e_storage']),
    dict(id='lower_basin', label='Población y usuarios de la cuenca baja', kind='person', evidence_ids=['e_cut']),
    dict(id='glen_canyon', label='Operación de Glen Canyon Dam', kind='organization', evidence_ids=['e_release', 'e_power']),
]
EVIDENCE = [
    dict(id='e_storage', observed_at=STUDY_AT, source=SOURCES[0]['origin'], basis='measurement', statement='Fin de septiembre de 2026: Mead 6.827 y Powell 5.155 mil acre-pies.', uncertainty='Fila histórica del estudio de octubre.'),
    dict(id='e_release', observed_at='2026-08-21T12:00:00-06:00', source=SOURCES[4]['origin'], basis='reported', statement='Liberación esperada de Powell entre 6,0 y 7,0 millones de acre-pies en 2027, decidida en abril.', uncertainty='Puede salir del rango tras consultas.'),
    dict(id='e_cut', observed_at='2026-08-21T12:00:00-06:00', source=SOURCES[4]['origin'], basis='reported', statement='Entregas a la cuenca baja reducidas 1,25 millones de acre-pies en 2027.', uncertainty='Reparto entre estados no modelado.'),
    dict(id='e_power', observed_at='2026-10-17T12:00:00-07:00', source=SOURCES[5]['origin'], basis='reported', statement='Bajo 3.490 pies Glen Canyon Dam deja de generar electricidad.', uncertainty='Extractos del buscador, no la página abierta.'),
]
RELATIONS = [
    dict(id='powell_to_mead', source='powell', target='mead', kind='supplies', evidence_ids=['e_release']),
    dict(id='ops_powell', source='glen_canyon', target='powell', kind='organizes', evidence_ids=['e_release']),
    dict(id='mead_basin', source='mead', target='lower_basin', kind='supplies', evidence_ids=['e_cut']),
]
OBSERVATION = dict(format='genius-system-observation/1', label='Lake Mead y Lake Powell: años hidrológicos 2027 y 2028',
                   window=dict(start='2026-08-21T00:00:00-06:00', end='2026-10-17T23:59:00-07:00'),
                   entities=ENTITIES, evidence=EVIDENCE, relations=RELATIONS,
                   unknowns=['Liberaciones de Powell distintas de las proyectadas por Reclamation.', 'Probabilidad admitida de cada afluencia de dos años.',
                             'Clientes de la electricidad de Glen Canyon, México y los ecosistemas del Gran Cañón.'])
SCOPE = dict(format='genius-system-scope/1', observation_revision=1, label='Powell, Mead y quienes dependen de ellos',
             members=['mead', 'powell', 'lower_basin', 'glen_canyon'], intervention_entities=['glen_canyon'],
             evaluation_entities=['mead', 'powell', 'lower_basin', 'glen_canyon'],
             bindings=[dict(collection='stocks', model_id='mead', entity_id='mead'), dict(collection='stocks', model_id='powell', entity_id='powell'),
                       dict(collection='carriers', model_id='lower_basin', entity_id='lower_basin'),
                       dict(collection='carriers', model_id='glen_canyon', entity_id='glen_canyon')],
             rationale='La liberación de 2027 desde Glen Canyon Dam es la decisión; se siguen sus consecuencias en 2028 sobre ambos embalses, la generación y quienes dependen de ellos.')

WORLD = dict(
    narrative='Caso real con proyecciones oficiales a dos años (mensual en 2027, trimestral en 2028): en abril de 2027 Reclamation decide si Powell libera 6 o 7 millones de acre-pies. Con afluencia mínima, liberar 7 deja a Glen Canyon sin generar electricidad desde agosto de 2027 hasta la primavera de 2028; liberar 6 deja a Mead bajo 1.000 pies desde marzo de 2028.',
    observation=OBSERVATION,
    construction={'format': 'genius-world-construction/1', 'sources': SOURCES, 'claims': CLAIMS,
                  'fragments': [dict(path=p, value=v, claim_ids=c) for p, v, c in FRAGMENTS], 'scope': SCOPE, 'unresolved': []},
    provenance='Proyecciones oficiales de Reclamation transcritas de sus tablas y extractos textuales citados; cifras no citadas declaradas como hipótesis.')

if __name__ == '__main__':
    out = Path(__file__).with_name('world.json')
    out.write_text(json.dumps(WORLD, ensure_ascii=False, indent=2) + '\n')
    print(out)
