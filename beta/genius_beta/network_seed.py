"""Opt-in reference node supervised with the existing service; ordinary public API."""
from copy import deepcopy
from datetime import datetime,timedelta,timezone
import json
import os
from pathlib import Path
import signal
from threading import Event

from federation.core import decode
from federation.internet import InternetNode,RemoteError,save
from federation.world_example import example

WORLD='genius-reference-synthetic-v1'


def reference_views(node_id,reference,expires):
    rows=example(reference,expires)
    for index,row in enumerate(rows):
        row['owner']=node_id;row['world_id']=WORLD;row['view_id']='reference-'+str(index)
    return rows


def bootstrap(state,hub,transport=None):
    client=InternetNode(state,**({'transport':transport} if transport else {}))
    client.init(hub,'Genius · nodo de referencia sintético',[WORLD],True)
    path=Path(state)/'reference-views.json'
    if not path.exists():
        stamp=datetime.now(timezone.utc)
        save(path,dict(views=reference_views(client.load()['node_id'],
             (stamp-timedelta(minutes=1)).isoformat(),(stamp+timedelta(days=30)).isoformat())))
    for view in decode(path.read_bytes())['views']:
        client.publish(deepcopy(view),True)
    return client


def main():
    if os.environ.get('GENIUS_NETWORK_NODE_ENABLED','false')!='true':
        raise SystemExit('Reference node not enabled')
    stopped=Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stopped.set())
    state=Path(os.environ['GENIUS_DATA_DIR'])/'network-reference'
    hub=os.environ['GENIUS_PUBLIC_URL']
    client=None
    attempts=0
    while not stopped.is_set():
        attempts+=1
        try:
            if client is None:client=bootstrap(state,hub)
            result=client.cycle(WORLD,['pump'])
            print(json.dumps(dict(component='network-reference',status=result['current']['status'],
                                  node_id=result['node_id'],synthetic=True)),flush=True)
        except Exception as exc:
            # The web, worker and backup remain available. No secrets or HTTP bodies.
            print(json.dumps(dict(component='network-reference',status='PAUSED_OR_REVIEW_REQUIRED',
                                 reason=str(exc) if isinstance(exc,RemoteError) else type(exc).__name__)),flush=True)
        stopped.wait(15 if client is None and attempts<5 else 600)


if __name__=='__main__':main()
