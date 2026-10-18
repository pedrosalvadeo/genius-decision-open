"""Shared catalog of function kinds (Module I across twins).

A twin's function may declare one `kind` from this catalog. Twins keep their own
thresholds and predicates; the kind only says which essential function a
measurement is about, so a federation (or any reader) can compare the same
function across different twins without summing them.
"""

CATALOG = {
    "water_supply": "Abastecimiento de agua a la población y sus usos",
    "hydropower": "Generación eléctrica",
    "dam_operation": "Operación confiable de una presa",
    "flood_margin": "Margen para amortiguar crecidas",
    "irrigation": "Riego",
    "ecological_flow": "Agua para ecosistemas",
}
