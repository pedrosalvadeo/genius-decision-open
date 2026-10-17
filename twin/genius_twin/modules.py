"""The eight Genius modules as components of one evaluated twin.

Each entry names what embodies the module in the twin, what it takes and gives,
and whether it is filled, neutral or missing. It reads results; it computes none.
Computation order follows the specification DAG (05 §1), not the numbering:
0 -> V -> {I, II, III, IV, VI} -> VII.
"""

ORDER = [["0", "V"], ["V", "I"], ["V", "II"], ["V", "III"], ["V", "IV"], ["V", "VI"],
         ["I", "VII"], ["II", "VII"], ["III", "VII"], ["IV", "VII"], ["VI", "VII"]]


def module_ledger(model, canonical, trajectories):
    policies, scenarios = model["policies"], model["scenarios"]
    projected = len(policies) * len(scenarios)
    functions = model.get("functions", [])
    life = model["task"]["kind"] == "life_conditions"
    decision = canonical["decision"]
    pvs = {pid: p["pvs"].get("value") for pid, p in canonical["policies"].items()}
    organizations = sorted({row["organization"] for traces in trajectories.values() for tr in traces.values() for row in tr["daily"]})
    entries = [
        dict(module="0", name="Representación", embodied_by="El gemelo: existencias, capacidades e historia del sistema real",
             inputs=["fuentes y afirmaciones citadas", "supuestos declarados"], outputs=["estado inicial", "historias", "información disponible"],
             status="FILLED", detail=dict(stocks=[s["id"] for s in model["stocks"]], horizon=model["horizon"],
                                          step_unit=model["step_unit"], assumptions=len(model["assumptions"]))),
        dict(module="V", name="Futuros", embodied_by="Rutas por escenarios: cada par genera un gemelo proyectado",
             inputs=["estado inicial (0)", "rutas", "escenarios"], outputs=["gemelos proyectados", "trayectorias causales"],
             status="FILLED", detail=dict(routes=[p["id"] for p in policies], scenarios=[s["id"] for s in scenarios],
                                          projected_twins=projected, states_per_twin=model["horizon"] + 1)),
        dict(module="I", name="Funcionalidad", embodied_by="Funciones del sistema medidas en cada gemelo proyectado",
             inputs=["gemelos proyectados (V)", "funciones declaradas"], outputs=["perfil funcional por estado", "perfil terminal por escenario"],
             status="FILLED" if functions else "NEUTRAL",
             detail=dict(functions=[f["id"] for f in functions], measured_twins=projected if functions else 0,
                         criterion=decision.get("functional_criterion"))),
        dict(module="II", name="Multiescala", embodied_by="Existencias del gemelo como puertos de un solo sistema",
             inputs=["gemelos proyectados (V)"], outputs=["balances conjuntos", "ocupación de recursos"],
             status="SINGLE_SYSTEM", detail=dict(ports=[s["id"] for s in model["stocks"]], subsystems=[], interfaces=[])),
        dict(module="III", name="Capacidad generativa", embodied_by="Organizaciones (firmas de capacidades) que cada ruta alcanza y conserva",
             inputs=["gemelos proyectados (V)", "capacidades"], outputs=["CAG posible y robusta por ruta"],
             status="FILLED", detail=dict(capabilities=[c["id"] for c in model["capabilities"]], organizations=len(organizations))),
        dict(module="IV", name="Bienestar", embodied_by="Portadores y sus dimensiones a lo largo del tiempo",
             inputs=["gemelos proyectados (V)", "vínculos de bienestar"], outputs=["perfil de bienestar por escenario, mes, portador y dimensión"],
             status="FILLED" if model["welfare"] else "MISSING",
             detail=dict(carriers=[c["id"] for c in model["carriers"]], dimensions=sorted({w["dimension"] for w in model["welfare"]}))),
        dict(module="VI", name="Evidencia y PVS", embodied_by="Condición de vida, ley de escenarios y su procedencia",
             inputs=["gemelos proyectados (V)", "ley declarada", "condición de vida"], outputs=["PVS por ruta", "rango bajo toda ley"],
             status="FILLED" if life and model["law"] is not None else "NO_LIFE_CONDITION" if not life else "NO_LAW",
             detail=dict(task=model["task"]["kind"], law_declared=model["law"] is not None, pvs=pvs)),
        dict(module="VII", name="Decisión", embodied_by="Comparación conjunta, frontera y selección explícita",
             inputs=["perfiles funcionales (I)", "composición (II)", "CAG (III)", "bienestar (IV)", "PVS (VI)"],
             outputs=["factibles", "frontera", "selección"],
             status="FILLED" if decision.get("coverage") is not None else "MISSING",
             detail=dict(feasible=decision.get("feasible"), frontier=decision.get("frontier"), selected=decision.get("selected"))),
    ]
    return {"order": ORDER, "modules": entries,
            "complete": all(e["status"] == "FILLED" for e in entries),
            "interpretation": "LEDGER_OF_WHAT_EMBODIES_EACH_MODULE_NOT_A_NEW_RESULT"}
