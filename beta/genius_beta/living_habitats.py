"""Explicitly enabled real-data observers within the existing service and volume."""
import json
import os
from pathlib import Path
import signal
from threading import Event

from federation.habitat import Habitat,STATIONS,INTERVAL


def main():
    stations=os.environ.get('GENIUS_LIVING_HABITATS','').split(',')
    if not 1<=len(stations)<=2 or len(set(stations))!=len(stations) or any(s not in STATIONS for s in stations):
        raise SystemExit('Explicit authorized stations required')
    root=Path(os.environ['GENIUS_DATA_DIR'])/'living-habitats'
    observers=[Habitat(root/s,s,os.environ['GENIUS_PUBLIC_URL']) for s in stations]
    for observer in observers:
        if not observer.path.exists():observer.authorize(True)
    stopped=Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stopped.set())
    while not stopped.is_set():
        for observer in observers:
            if stopped.is_set():break
            try:result=observer.step()
            except Exception as exc:result=dict(station=observer.station,status='REVIEW_REQUIRED',reason=type(exc).__name__)
            print(json.dumps(dict(component='living-habitat',**result)),flush=True)
        stopped.wait(INTERVAL)


if __name__=='__main__':main()
