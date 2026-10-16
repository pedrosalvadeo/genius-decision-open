"""Hand-interpreted synthetic views; domain details live only in this fixture."""
from copy import deepcopy
from .views import FORMAT


def example(reference, expires):
    frame=dict(reference_time=reference,step_unit='day',horizon=3,layout='synthetic-pumping-layout-v1')
    water={
        '/name':'Abastecimiento sintético: tres vistas complementarias',
        '/stocks/0':dict(id='reserve',label='Reserva',unit='litre',kind='persistent',initial='8/1',capacity='8/1'),
        '/stocks/1':dict(id='delivered',label='Agua entregada acumulada',unit='litre',kind='persistent',initial='1/1',capacity='9/1'),
        '/actions/0':dict(id='idle',label='Esperar',requires=['access'],withdrawals={},deposits={},add_capabilities=[],remove_capabilities=[]),
        '/actions/2':dict(id='pump',label='Bombear',requires=['access','powered'],withdrawals={'reserve':'2/1','energy':'1/1'},deposits={'delivered':'2/1'},add_capabilities=[],remove_capabilities=[]),
        '/policies/0':dict(id='wait',label='Esperar tres días',default_action='idle',rules=[]),
        '/policies/1':dict(id='restore_supply',label='Restaurar y después bombear',default_action='pump',rules=[dict(steps=[1],when=[],action='repair')]),
        '/law':None,
        '/require_all_scenarios':False,
        '/selection':'none',
        '/assumptions/0':dict(id='Synthetic',kind='SYNTHETIC',statement='Escenario hipotético: sin mediciones reales, pérdidas, demanda o impactos de campo validados.',provenance='Experimento distribuido declarado'),
    }
    energy={
        '/stocks/2':dict(id='energy',label='Energía disponible diaria',unit='kWh',kind='renewable',initial='1/1',capacity='1/1'),
        '/stocks/3':dict(id='hours',label='Mantenimiento disponible diario',unit='hour',kind='renewable',initial='1/1',capacity='1/1'),
        '/capabilities/0':dict(id='access',label='Acceso de simulación'),
        '/capabilities/1':dict(id='powered',label='Equipo operativo después de la reparación simulada'),
        '/initial_capabilities':['access'],
        '/actions/1':dict(id='repair',label='Restaurar el equipo',requires=['access'],withdrawals={'hours':'1/1'},deposits={},add_capabilities=['powered'],remove_capabilities=[]),
        '/scenarios/0':dict(id='available',label='Disponibilidad hipotética constante',events=[dict(inflows={},renewables={'energy':'1/1','hours':'1/1'},drains={},remove_capabilities=[]) for _ in range(3)]),
    }
    community={
        '/carriers/0':dict(id='community',label='Comunidad sintética',kind='organization'),
        '/welfare/0':dict(carrier='community',dimension='access',label='Agua entregada, indicador operacional parcial',stock='delivered',direction='higher'),
        '/task':dict(kind='operational',label='Comparar entrega acumulada y ejecución de la ruta',living_carriers=[],conditions=[dict(stock='delivered',op='ge',threshold='0/1')],require_action_success=True),
    }
    parts=[
        ('water',water,[('tank','reserve','resource'),('supply','delivered','resource'),('pump_tag','pump','physical')],
         [('tank','pump_tag','supplies'),('pump_tag','supply','supplies')],
         [('stocks','reserve','tank'),('stocks','delivered','supply')],
         'Reserva inicial 8 litros; entrega inicial 1 litro. Bombear requiere equipo operativo, consume 2 litros y 1 kWh y entrega 2 litros. Se compara esperar con reparar el primer día y bombear los siguientes. No se conocen probabilidades.'),
        ('energy',energy,[('electricity','energy','resource'),('crew_time','hours','resource'),('device_7','pump','physical')],
         [('electricity','device_7','supplies'),('crew_time','device_7','supplies')],
         [('stocks','energy','electricity'),('stocks','hours','crew_time')],
         'Hay 1 kWh y 1 hora disponibles cada día. El equipo no está operativo inicialmente. Una reparación consume 1 hora y habilita powered. La correspondencia device_7 con la bomba del escenario es una declaración explícita.'),
        ('community',community,[('received_water','delivered','resource'),('residents','community','organization')],
         [('received_water','residents','affects')],
         [('carriers','community','residents')],
         'La entrega acumulada afecta a una comunidad sintética. Se usa más agua entregada como indicador operacional parcial. No se han medido salud, bienestar integral, distribución entre personas ni sostenimiento de vida.'),
    ]
    views=[]
    for owner,values,entities,relations,bindings,statement in parts:
        values={**values,'/profile':'STOCK_FLOW_FINITE_V1','/horizon':3,'/step_unit':'day'}
        doc=dict(format='genius-world-construction/1',sources=[dict(id='source',origin='fixture:'+owner,observed_at=reference,content=statement)],
            claims=[dict(id='interpretation',basis='synthetic',statement='Interpretación manual del escenario y decisiones de representación declaradas.',
                uncertainty='Hipótesis sintética; exactitud semántica y causal no verificadas.',
                spans=[dict(source_id='source',start=0,end=len(statement),quote=statement)],premises=[])],
            fragments=[dict(path=k,value=v,claim_ids=['interpretation']) for k,v in values.items()],scope=None,unresolved=[])
        snapshot=dict(format='genius-system-observation/1',label='Vista '+owner,
            window=dict(start=reference,end=reference),
            entities=[dict(id=local,label=local,kind=kind,evidence_ids=['e']) for local,_,kind in entities],
            evidence=[dict(id='e',observed_at=reference,source='fixture:'+owner,basis='synthetic',statement=statement,uncertainty='Relaciones e identidades declaradas; no observación de campo.')],
            relations=[dict(id='r'+str(i),source=a,target=b,kind=kind,evidence_ids=['e']) for i,(a,b,kind) in enumerate(relations)],
            unknowns=['Faltan observaciones de campo y efectos fuera de estas vistas.'])
        views.append(dict(format=FORMAT,world_id='pumping-study',view_id='snapshot',owner=owner,shareable=True,
            valid_until=expires,frame=deepcopy(frame),observation=snapshot,
            identities=[dict(local_id=local,global_id=global_id,status='confirmed',rationale='Correspondencia explícita del escenario; no deducida por parecido del nombre.',evidence_ids=['e']) for local,global_id,_ in entities],
            denials=[],construction=doc,
            bindings=[dict(collection=collection,model_id=model_id,entity_id=entity_id) for collection,model_id,entity_id in bindings]))
    return views
