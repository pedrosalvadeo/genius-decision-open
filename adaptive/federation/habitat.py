"""Opt-in living observers: real public measurements, frozen predictions, later scores."""
import argparse
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
from decimal import Decimal
import fcntl
from http.client import HTTPSConnection
import json
import os
from pathlib import Path
import shutil
import signal
from threading import Event
import time

from .core import Node,canonical,decode,digest,event_key,instant,now,validate
from .internet import InternetNode,RemoteError,save
from .organism import Organism

STATIONS={'SAME':'Mendoza · El Plumerillo','SAMM':'Malargüe'}
INTERVAL=3600
SOURCE='https://aviationweather.gov/api/data/metar'


class SourceError(ValueError):
    pass


def ctx(station):
    if station not in STATIONS:raise ValueError('STATION_NOT_AUTHORIZED')
    return dict(system='weather-station-'+station,variable='air-temperature',unit='centikelvin',
                regime='METAR-next-report-v1',data_kind='reported')


def fetch(station):
    ctx(station)
    conn=HTTPSConnection('aviationweather.gov',443,timeout=15)
    try:
        conn.request('GET','/api/data/metar?ids='+station+'&format=json&hours=18',
            headers={'User-Agent':'GeniusDecision-Research/1.0 (+https://geniusdecision.app/network)','Accept':'application/json'})
        response=conn.getresponse();raw=response.read(262145)
        if response.status==204:return []
        if response.status!=200:raise SourceError('SOURCE_HTTP_'+str(response.status))
        if len(raw)>262144:raise SourceError('SOURCE_SIZE_LIMIT')
        def unique(pairs):
            result={}
            for key,value in pairs:
                if key in result:raise SourceError('SOURCE_DUPLICATE_KEY')
                result[key]=value
            return result
        def invalid(_):raise SourceError('SOURCE_INVALID_NUMBER')
        return json.loads(raw,parse_float=Decimal,parse_constant=invalid,object_pairs_hook=unique)
    finally:conn.close()


def observations(payload,station,stamp):
    context=ctx(station);current=instant(stamp)
    if type(payload) is not list or len(payload)>100:raise SourceError('SOURCE_SHAPE')
    result=[]
    for row in payload:
        if type(row) is not dict or row.get('icaoId')!=station:raise SourceError('SOURCE_STATION_MISMATCH')
        if row.get('temp') is None:continue
        if type(row.get('obsTime')) is not int:raise SourceError('SOURCE_TIME')
        observed=datetime.fromtimestamp(row['obsTime'],timezone.utc)
        if observed>current:raise SourceError('SOURCE_FUTURE_OBSERVATION')
        if observed<current-timedelta(hours=24):continue
        if type(row['temp']) not in (int,float,Decimal):raise SourceError('SOURCE_TEMPERATURE')
        c=Decimal(str(row['temp']));value=(c+Decimal('273.15'))*100
        if not c.is_finite() or not Decimal('-90')<=c<=Decimal('60') or value!=value.to_integral_value():
            raise SourceError('SOURCE_TEMPERATURE')
        raw=row.get('rawOb')
        if not isinstance(raw,str) or not raw or len(raw)>480 or station not in raw.split():raise SourceError('SOURCE_REPORT')
        record=dict(format='genius-node-observation/1',context=context,value=int(value),
            observed_at=observed.isoformat(),valid_until=(observed+timedelta(hours=48)).isoformat(),shareable=True,
            source=dict(origin=SOURCE+'?ids='+station,event=station+'-'+str(row['obsTime'])+'-temperature',excerpt=raw))
        validate(record);result.append(record)
    return sorted({digest(r):r for r in result}.values(),key=lambda r:(instant(r['observed_at']),digest(r)))


class Habitat:
    def __init__(self,state,station,hub,transport=None,source=fetch,clock=now):
        ctx(station);self.state=Path(state).resolve();self.state.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.station=station;self.hub=hub;self.source=source;self.clock=clock
        self.client=InternetNode(self.state,**({'transport':transport} if transport else {}))
        self.path=self.state/'habitat.json';self.report=self.state/'public-report.json'

    @contextmanager
    def lock(self):
        fd=os.open(self.state/'habitat.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
        try:
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);yield
        finally:os.close(fd)

    def authorize(self,confirmed=False):
        if confirmed is not True:raise ValueError('HABITAT_AUTHORIZATION_REQUIRED')
        with self.lock():
            if self.path.exists():
                state=self.load()
                if state['revoked']:raise ValueError('HABITAT_REVOKED')
            else:
                save(self.path,dict(format='genius-living-habitat/1',station=self.station,hub=self.hub,
                     next_at=0,revoked=False,paused=False,enrolled=False,enrollment_attempts=0,
                     last_scored=None,last_prediction=None,last_archive=None,source_blocked=False))
        return dict(authorized=True,station=self.station)

    def load(self):
        state=decode(self.path.read_bytes())
        if state['station']!=self.station or state['hub']!=self.hub:raise ValueError('HABITAT_SCOPE_CHANGED')
        return state

    def control(self,action):
        if action not in ('pause','resume','revoke'):raise ValueError('INVALID_CONTROL')
        with self.lock():
            state=self.load()
            if action=='resume' and state['revoked']:raise ValueError('HABITAT_REVOKED')
            if action=='revoke':state['revoked']=True
            else:state['paused']=action=='pause'
            save(self.path,state)
            if action!='revoke':return self.publish(state,'OPERATOR_PAUSE' if state['paused'] else 'WAITING')
        return self.step()

    def publish(self,state,status,organism=None,**details):
        report=dict(format='genius-living-report/1',station=self.station,label=STATIONS[self.station],
            status=status,checked_at=self.clock(),next_check_at=state['next_at'],node_id=state.get('node_id'),
            source=SOURCE+'?ids='+self.station+'&format=json',source_kind='REAL_REPORTED_OBSERVATIONS',
            host_kind='OPERATOR_AUTHORIZED',physical_actions=False,wellbeing_effect='UNMEASURED',
            life_sustainment_probability=None,latest_observation=state.get('latest_observation'),
            last_scored=state.get('last_scored'),last_prediction=state.get('last_prediction'),
            last_archive=state.get('last_archive'),organism=organism.status() if organism else state.get('organism'),**details)
        # Only scored, later outcomes enter this bounded public history. Missing
        # observations and pending predictions never become zero-error samples.
        report['recent_results']=state.get('recent_results',[])
        if organism:state['organism']=report['organism']
        save(self.path,state);save(self.report,report)
        return report

    def step(self):
        with self.lock():
            state=self.load();stamp=self.clock();moment=instant(stamp);tick=int(moment.timestamp())
            if state['revoked']:
                status='REVOKED'
                if state.get('enrolled'):
                    try:self.client.leave();state['enrolled']=False
                    except (OSError,ValueError):status='RETIREMENT_PENDING'
                return self.publish(state,status)
            if state['next_at']>tick:
                return decode(self.report.read_bytes()) if self.report.exists() else self.publish(state,'WAITING')
            state['next_at']=tick+INTERVAL;save(self.path,state)
            try:
                if shutil.disk_usage(self.state).free<64*1024**2:return self.publish(state,'RESOURCE_REST')
                if state['enrolled'] and not self.client.credentials_path.exists():raise ValueError('IDENTITY_REVIEW_REQUIRED')
                if not state['enrolled']:
                    if state['paused']:return self.publish(state,'OPERATOR_PAUSE')
                    if state['enrollment_attempts']>=3:raise ValueError('ENROLLMENT_REVIEW_REQUIRED')
                    state['enrollment_attempts']+=1;save(self.path,state)
                    self.client.init(self.hub,'Genius observador · '+STATIONS[self.station],['metar-'+self.station.lower()],True)
                    state['node_id']=self.client.load()['node_id'];state['enrolled']=True;save(self.path,state)
                cfg=self.client.load();self.client.renew(cfg)
                self.client.call(cfg,'POST','/api/network/heartbeat',{},True)
                node=Node(self.state/'memory',state['node_id'],self.clock);organism=Organism(node)
                if state['paused']:return self.publish(state,'OPERATOR_PAUSE',organism)
                if state['source_blocked']:return self.publish(state,'SOURCE_ACCESS_REVIEW',organism)
                rows=observations(self.source(self.station),self.station,stamp)
                if not rows:return self.publish(state,'NO_OBSERVATIONS',organism)
                latest=rows[-1]
                state['latest_observation']=dict(observed_at=latest['observed_at'],centikelvin=latest['value'],sha256=digest(latest))
                trials=organism.load()['trials'];trial=next(iter(trials.values()),None)
                if trial and trial['status'] in ('DISCOVERY','CONFIRMATION') and trial['rounds'] and 'score' not in trial['rounds'][-1]:
                    pending=trial['rounds'][-1]
                    targets=[r for r in rows if instant(pending['frozen_at'])<instant(r['observed_at']) and
                             instant(pending['window'][0] or pending['frozen_at'])<=instant(r['observed_at'])<=instant(pending['window'][1])]
                    if targets:
                        first=targets[0];variants={digest(r) for r in targets if event_key(r)==event_key(first)}
                        with node.db() as db:
                            variants.update(r[0] for r in db.execute('SELECT hash FROM records WHERE event=?',(event_key(first),)))
                        if len(variants)>1:
                            node.ingest(rows)
                            return self.publish(state,'SOURCE_CONFLICT_REVIEW',organism)
                        # Score the frozen prediction BEFORE adding this outcome to training memory.
                        trial=organism.feedback(trial['id'],first)
                        scored=trial['rounds'][-1];pred=scored['estimates'][scored['expressed_genome']]['estimate']
                        state['last_scored']=dict(observed_at=first['observed_at'],predicted_centikelvin=pred,
                            actual_centikelvin=first['value'],absolute_error_centikelvin=abs(pred-first['value']),
                            forecast_sha256=pending['forecast_sha256'],target_sha256=digest(first))
                        recent=state.setdefault('recent_results',[])
                        if not any(r['forecast_sha256']==pending['forecast_sha256'] for r in recent):
                            recent.append(dict(state['last_scored']))
                        state['recent_results']=recent[-24:]
                    elif moment>instant(pending['window'][1]):
                        organism.miss_target(trial['id']);trial=organism.load()['trials'][trial['id']]
                node.ingest(rows)
                if trial and trial['status'] not in ('DISCOVERY','CONFIRMATION'):
                    state['last_archive']=organism.archive_finished(trial['id']);trial=None
                if instant(latest['observed_at'])<moment-timedelta(hours=2):return self.publish(state,'STALE_OBSERVATIONS',organism)
                if trial is None:
                    serial=organism.status()['archived_trials']+1
                    trial=organism.begin('metar-'+str(serial),ctx(self.station))
                if trial['rounds'] and 'score' not in trial['rounds'][-1]:return self.publish(state,'WAITING_FOR_OUTCOME',organism)
                # Freeze at the actual post-fetch clock, never at the cycle's start.
                prediction=organism.predict(trial['id'],None,(instant(self.clock())+timedelta(hours=2)).isoformat())
                if prediction.get('status')=='EVIDENCE_REVIEW':return self.publish(state,'EVIDENCE_REVIEW',organism)
                value=prediction['estimates'][prediction['expressed_genome']]['estimate']
                state['last_prediction']=dict(frozen_at=prediction['frozen_at'],target_window=[prediction['frozen_at'],prediction['window'][1]],
                    predicted_centikelvin=value,genome_sha256=prediction['expressed_genome'],
                    forecast_sha256=prediction['forecast_sha256'],trial_id=trial['id'])
                return self.publish(state,'WAITING_FOR_OUTCOME',organism)
            except SourceError as exc:
                if str(exc) in ('SOURCE_HTTP_403','SOURCE_HTTP_404'):state['source_blocked']=True
                return self.publish(state,'SOURCE_UNAVAILABLE',reason=str(exc))
            except (OSError,ValueError,KeyError,TypeError) as exc:
                # No response bodies, tokens or arbitrary source text in public status.
                codes={'GENERATION_LIMIT','MEMORY_BUDGET','EVOLUTION_TRIAL_BUDGET','ENROLLMENT_REVIEW_REQUIRED','IDENTITY_REVIEW_REQUIRED'}
                reason=str(exc) if isinstance(exc,RemoteError) or str(exc) in codes else type(exc).__name__
                return self.publish(state,'PAUSED_OR_REVIEW_REQUIRED',reason=reason)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state',type=Path,required=True);parser.add_argument('--station',choices=STATIONS,required=True)
    parser.add_argument('--hub',default='https://geniusdecision.app')
    parser.add_argument('--allow-observation',action='store_true');parser.add_argument('--continuous',action='store_true')
    parser.add_argument('--control',choices=('pause','resume','revoke'))
    args=parser.parse_args();habitat=Habitat(args.state,args.station,args.hub)
    if args.control:print(json.dumps(habitat.control(args.control)));return
    habitat.authorize(args.allow_observation);stop=Event()
    for sig in (signal.SIGTERM,signal.SIGINT):signal.signal(sig,lambda *_:stop.set())
    while not stop.is_set():
        print(json.dumps(habitat.step()),flush=True)
        if not args.continuous:return
        stop.wait(INTERVAL)


if __name__=='__main__':main()
