"""Context-bound evolution from frozen predictions and later reported outcomes.

Four discovery outcomes nominate a variant; four new outcomes confirm it.
This is an operational prediction experiment, not a biological fitness or PVS claim.
"""
import argparse
from contextlib import contextmanager
from copy import deepcopy
from datetime import timezone
import fcntl
import json
import os
from pathlib import Path

from .core import Node, canonical, context, decode, digest, event_key, fields, identifier, instant
from . import genetics as genes
from .network_protocol import identity, sign, verify

MAX_TRIALS = 4
PHASE_SIZE = 4


def metrics(rounds, genome_hash):
    errors = [abs(row['estimates'][genome_hash]['estimate']-row['score']['value']) for row in rounds]
    return dict(count=len(errors), absolute_error_sum=sum(errors), max_error=max(errors, default=0))


def improves(candidate, baseline):
    return (candidate['count'] == baseline['count'] == PHASE_SIZE and
            candidate['absolute_error_sum'] < baseline['absolute_error_sum'] and
            candidate['max_error'] <= baseline['max_error'])


def compare_native(baseline, candidate):
    from genius_adaptive.contextual import comparison_model
    from genius_twin.registry import evaluate
    model = comparison_model(dict(baseline=baseline, candidate=candidate))
    result = evaluate(model)
    if not result['verification']['valid']: raise ValueError('NATIVE_COMPARISON_FAILED')
    return dict(model_sha256=digest(model), verification=result['verification'],
                decision=result['canonical_results']['decision'],
                criterion='OBSERVED_ABSOLUTE_ERROR_NOT_WELLBEING_OR_PVS')


def validate_heredity(packet, parent_id, birth_id):
    fields(packet, 'payload signature')
    p = packet['payload']
    fields(p, 'format parent_node_id public_key birth_id founder adaptations')
    if (p['format'] != 'genius-heredity/1' or p['parent_node_id'] != parent_id or
        identity(p['public_key']) != parent_id or p['birth_id'] != birth_id):
        raise ValueError('HEREDITY_IDENTITY_MISMATCH')
    identifier(birth_id); genes.validate(p['founder'])
    if type(p['adaptations']) is not list or len(p['adaptations']) > MAX_TRIALS:
        raise ValueError('HEREDITY_BUDGET')
    seen = set()
    for row in p['adaptations']:
        fields(row, 'context genome'); context(row['context']); genes.validate(row['genome'])
        key = digest(row['context'])
        if key in seen: raise ValueError('DUPLICATE_CONTEXT')
        seen.add(key)
    verify(p, p['public_key'], packet['signature'])
    return p


class Organism:
    def __init__(self, node, inheritance=None, parent_id=None, birth_id=None):
        self.node = node
        parent = validate_heredity(inheritance, parent_id, birth_id) if inheritance is not None else None
        with self.lock(), node.db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS organism (id INTEGER PRIMARY KEY CHECK(id=1), body TEXT NOT NULL)')
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT body FROM organism WHERE id=1').fetchone()
            if row is None:
                base = genes.inherit(parent['founder'], birth_id) if parent else genes.founder(node.node_id)
                inherited = {digest(r['context']):dict(context=r['context'],
                    genome=genes.inherit(r['genome'], digest([birth_id, r['context']])),
                    evidence='INHERITED_TRAIT_NOT_LOCAL_VALIDATION') for r in parent['adaptations']} if parent else {}
                pool = genes.variants(base, birth_id or node.node_id)
                variant = pool[int(digest(birth_id or node.node_id)[:8],16)%len(pool)] if pool else None
                state = dict(format='genius-organism/1', node_id=node.node_id,
                    constitution_sha256=genes.CONSTITUTION_HASH, founder=base,
                    birth_variant=variant, birth_packet_sha256=digest(inheritance) if parent else None,
                    parent_node_id=parent_id if parent else None, adaptations=inherited, trials={})
                db.execute('INSERT INTO organism VALUES (1,?)', (canonical(state).decode(),))
            else:
                state = json.loads(row[0]); self.validate_state(state)
                if parent and state['birth_packet_sha256'] != digest(inheritance):
                    raise ValueError('BIRTH_ALREADY_BOUND')

    @contextmanager
    def lock(self):
        fd = os.open(self.node.directory/'organism.lock', os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally: os.close(fd)

    def validate_state(self, state):
        if state['node_id'] != self.node.node_id or state['constitution_sha256'] != genes.CONSTITUTION_HASH:
            raise ValueError('ORGANISM_IDENTITY_OR_CONSTITUTION_CHANGED')
        genes.validate(state['founder'])
        if state['birth_variant'] is not None: genes.validate(state['birth_variant'])
        for key, row in state['adaptations'].items():
            context(row['context']); genes.validate(row['genome'])
            if key != digest(row['context']): raise ValueError('CONTEXT_CHANGED')

    def load(self):
        with self.node.db() as db:
            state = json.loads(db.execute('SELECT body FROM organism WHERE id=1').fetchone()[0])
        self.validate_state(state)
        return state

    def save(self, state):
        self.validate_state(state)
        raw = canonical(state)
        if len(raw) > 262144: raise ValueError('ORGANISM_MEMORY_BUDGET')
        with self.node.db() as db: db.execute('UPDATE organism SET body=? WHERE id=1', (raw.decode(),))

    def status(self):
        state = self.load()
        history=state.get('history',{})
        return dict(format='genius-organism-status/1', constitution_sha256=genes.CONSTITUTION_HASH,
            founder_sha256=digest(state['founder']), founder_generation=state['founder']['generation'],
            founder_genes=state['founder']['genes'], parent_node_id=state['parent_node_id'],
            birth_variant_sha256=digest(state['birth_variant']) if state['birth_variant'] else None, adapted_contexts=len(state['adaptations']),
            locally_confirmed_changes=history.get('adopted_changes',0)+sum(t['status']=='ADOPTED' for t in state['trials'].values()),
            scored_outcomes=history.get('scored_outcomes',0)+sum(sum('score' in r for r in t['rounds']) for t in state['trials'].values()),
            archived_trials=history.get('completed_trials',0),
            trials={k:t['status'] for k,t in state['trials'].items()},
            trial_progress=[dict(id=k,status=t['status'],phase_size=PHASE_SIZE,
                discovery_scored=sum('score' in r for r in t['rounds'][:PHASE_SIZE]),
                confirmation_scored=sum('score' in r for r in t['rounds'][PHASE_SIZE:]),
                pending_outcome=bool(t['rounds'] and 'score' not in t['rounds'][-1]))
                for k,t in sorted(state['trials'].items())],
            context_traits=[dict(context_sha256=key,genome_sha256=digest(row['genome']),
                generation=row['genome']['generation'],genes=row['genome']['genes'],evidence=row['evidence'])
                for key,row in sorted(state['adaptations'].items())],
            wellbeing_effect='UNMEASURED', life_sustainment_probability=None)

    def miss_target(self,trial_id):
        """A missing later measurement is a gap, never a fabricated zero/error."""
        with self.lock():
            state=self.load();trial=state['trials'][trial_id]
            if trial['status'] not in ('DISCOVERY','CONFIRMATION'):return
            if not trial['rounds'] or 'score' in trial['rounds'][-1]:raise ValueError('NO_PENDING_TARGET')
            if instant(self.node.clock())<=instant(trial['rounds'][-1]['window'][1]):raise ValueError('TARGET_WINDOW_OPEN')
            trial['status']='MISSED_TARGET';self.save(state)

    def archive_finished(self,trial_id):
        """Explicit stream maintenance: archive evidence before releasing a trial slot.

        Keeps 64 complete archives locally plus cumulative counters and a hash chain.
        Current genotypes, identity and active forecast evidence are never pruned.
        """
        from .internet import save
        with self.lock():
            state=self.load();trial=state['trials'][trial_id]
            if trial['status'] in ('DISCOVERY','CONFIRMATION'):raise ValueError('ACTIVE_TRIAL_CANNOT_ARCHIVE')
            ids={r['forecast_id'] for r in trial['rounds']}
            with self.node.db() as db:
                forecasts=[];evidence=set();conflicts=set()
                for id_,body,result in db.execute('SELECT id,body,result FROM forecasts'):
                    frozen=json.loads(body)
                    if id_ in ids or frozen['sha256']==trial.get('blocked_forecast'):
                        ids.add(id_);forecasts.append(dict(forecast=frozen,result=json.loads(result) if result else None))
                        evidence.update(r['hash'] for r in frozen['evidence'])
                        conflicts.update(frozen['conflicts'])
                observations=[json.loads(body) for hash_,event,body in db.execute('SELECT hash,event,body FROM records ORDER BY hash') if hash_ in evidence or event in conflicts]
            history=state.setdefault('history',dict(completed_trials=0,adopted_changes=0,scored_outcomes=0,last_archive_sha256=None))
            archive=dict(format='genius-evolution-archive/1',node_id=self.node.node_id,trial=trial,
                         previous_sha256=history['last_archive_sha256'],forecasts=sorted(forecasts,key=lambda f:f['forecast']['id']),observations=observations)
            hash_=digest(archive);directory=self.node.directory/'evolution-history';directory.mkdir(mode=0o700,exist_ok=True)
            path=directory/(f"{history['completed_trials']+1:09d}-"+hash_+'.json')
            if len(canonical(archive))>1048576:raise ValueError('ARCHIVE_BUDGET')
            save(path,archive)  # Durable copy precedes the atomic SQLite transition.
            history['completed_trials']+=1;history['adopted_changes']+=int(trial['status']=='ADOPTED')
            history['scored_outcomes']+=sum('score' in r for r in trial['rounds']);history['last_archive_sha256']=hash_
            del state['trials'][trial_id];self.validate_state(state)
            with self.node.db() as db:
                db.execute('BEGIN IMMEDIATE')
                db.execute('UPDATE organism SET body=? WHERE id=1',(canonical(state).decode(),))
                db.executemany('DELETE FROM forecasts WHERE id=?',[(id_,) for id_ in ids])
                protected={r['hash'] for (raw,) in db.execute('SELECT body FROM forecasts') for r in json.loads(raw)['evidence']}
                rows=[(hash_,event,json.loads(raw)) for hash_,event,raw in db.execute('SELECT hash,event,body FROM records')]
                # Keep every version of retained events, so pruning cannot hide a conflict.
                recent={event for _,event,_ in sorted(rows,key=lambda r:instant(r[2]['observed_at']),reverse=True)[:48]}
                removed=[(hash_,) for hash_,event,_ in rows if hash_ not in protected and event not in recent]
                db.executemany('DELETE FROM receipts WHERE hash=?',removed)
                db.executemany('DELETE FROM records WHERE hash=?',removed)
            for old in sorted(directory.glob('*.json'))[:-64]:old.unlink()
            return dict(sha256=hash_,status=trial['status'],completed_trials=history['completed_trials'])

    def heredity(self, config, birth_id):
        identifier(birth_id)
        if config['node_id'] != self.node.node_id: raise ValueError('WRONG_PARENT')
        with self.lock():
            state = self.load()
            p = dict(format='genius-heredity/1', parent_node_id=self.node.node_id,
                     public_key=config['keys']['public_key'], birth_id=birth_id,
                     founder=state['founder'], adaptations=[dict(context=r['context'],genome=r['genome'])
                        for _,r in sorted(state['adaptations'].items())])
            return dict(payload=p, signature=sign(p, config['keys']['private_key']))

    def begin(self, trial_id, ctx):
        identifier(trial_id); context(ctx)
        with self.lock():
            state = self.load()
            if trial_id in state['trials']:
                trial = state['trials'][trial_id]
                if trial['context'] != ctx: raise ValueError('TRIAL_ID_CONFLICT')
                return deepcopy(trial)
            if len(state['trials']) >= MAX_TRIALS: raise ValueError('EVOLUTION_TRIAL_BUDGET')
            if any(t['status'] in ('DISCOVERY','CONFIRMATION') for t in state['trials'].values()):
                raise ValueError('EVOLUTION_ALREADY_RUNNING')
            baseline = state['adaptations'].get(digest(ctx), {}).get('genome', state['founder'])
            variants = genes.variants(baseline, digest([self.node.node_id, trial_id]))
            if not variants: raise ValueError('GENERATION_LIMIT')
            # Preserve the recorded birth mutation when it is one of these neighbors.
            variants = [state['birth_variant'] if state['birth_variant'] is not None and v['genes']==state['birth_variant']['genes'] and
                        state['birth_variant']['parents']==[digest(baseline)] else v for v in variants]
            trial = dict(id=trial_id, context=deepcopy(ctx), baseline=digest(baseline),
                candidates={digest(g):g for g in [baseline,*variants]}, rounds=[],
                status='DISCOVERY', started_at=self.node.clock(), candidate=None)
            state['trials'][trial_id] = trial; self.save(state)
            return deepcopy(trial)

    def predict(self, trial_id, target_after, target_before):
        identifier(trial_id)
        with self.lock():
            state = self.load(); trial = state['trials'][trial_id]
            self.advance(state,trial); self.save(state)
            if trial['status'] not in ('DISCOVERY','CONFIRMATION'): raise ValueError('TRIAL_FINISHED')
            rounds = trial['rounds']
            if rounds and 'score' not in rounds[-1]:
                if rounds[-1]['window'] != [target_after,target_before]: raise ValueError('UNSCORED_FORECAST')
                return deepcopy(rounds[-1])
            if rounds and instant(target_after or self.node.clock()) <= instant(rounds[-1]['score']['observed_at']):
                raise ValueError('SUCCESSIVE_TARGET_WINDOWS_REQUIRED')
            forecast_id = 'evo-'+digest([trial_id,len(rounds)])[:48]
            frozen = self.node.predict(forecast_id, trial['context'], 'connected', target_after, target_before)
            if frozen['status'] != 'FROZEN':
                trial['status'] = 'EVIDENCE_REVIEW'; trial['blocked_forecast'] = frozen['sha256']; self.save(state)
                return dict(status='EVIDENCE_REVIEW', forecast=frozen)
            evidence = []
            with self.node.db() as db:
                for row in frozen['evidence']:
                    body = json.loads(db.execute('SELECT body FROM records WHERE hash=?',(row['hash'],)).fetchone()[0])
                    # Normalize instants before comparing chronology (different timezone offsets).
                    evidence.append({**row,'observed_at':instant(body['observed_at']).astimezone(timezone.utc).isoformat()})
            active = [trial['baseline'],trial['candidate']] if trial['status']=='CONFIRMATION' else list(trial['candidates'])
            row = dict(forecast_id=forecast_id, forecast_sha256=frozen['sha256'], window=[target_after,target_before],
                phase=trial['status'], frozen_at=frozen['frozen_at'],
                estimates={key:genes.express(trial['candidates'][key],evidence) for key in active},
                expressed_genome=trial['baseline'])
            rounds.append(row); self.save(state)
            return deepcopy(row)

    def feedback(self, trial_id, target):
        identifier(trial_id)
        from .core import validate
        validate(target)
        with self.lock():
            state = self.load(); trial = state['trials'][trial_id]
            if not trial['rounds']: raise ValueError('PREDICTION_REQUIRED')
            row = trial['rounds'][-1]
            if 'score' in row:
                if row['score']['target_sha256'] != digest(target): raise ValueError('OUTCOME_IMMUTABLE')
                self.advance(state,trial); self.save(state)
                return deepcopy(trial)
            key = event_key(target)
            if any(r.get('score',{}).get('event')==key for t in state['trials'].values() for r in t['rounds']):
                raise ValueError('OUTCOME_EVENT_ALREADY_USED')
            score = self.node.observe_target(row['forecast_id'], target)
            row['score'] = dict(value=target['value'], event=key, target_sha256=score['target_sha256'],
                observed_at=target['observed_at'], received_at=score['received_at'])
            # Persist the measured outcome first; an interrupted comparison can be retried.
            self.save(state); self.advance(state,trial); self.save(state)
            return deepcopy(trial)

    def advance(self, state, trial):
        n = len(trial['rounds'])
        if trial['status'] not in ('DISCOVERY','CONFIRMATION') or any('score' not in r for r in trial['rounds']): return
        if n == PHASE_SIZE and trial['status']=='DISCOVERY':
            comparison = {key:metrics(trial['rounds'],key) for key in trial['candidates']}
            baseline = comparison[trial['baseline']]
            eligible = [key for key in comparison if key!=trial['baseline'] and improves(comparison[key],baseline)]
            trial['discovery_metrics'] = comparison
            if not eligible: trial['status']='NO_IMPROVEMENT'; return
            selected = min(eligible,key=lambda key:(comparison[key]['absolute_error_sum'],comparison[key]['max_error'],key))
            trial['discovery_native'] = compare_native(baseline,comparison[selected])
            if trial['discovery_native']['decision']['selected']!='candidate': raise ValueError('NATIVE_SELECTION_MISMATCH')
            trial['candidate']=selected; trial['status']='CONFIRMATION'
        elif n == PHASE_SIZE*2 and trial['status']=='CONFIRMATION':
            baseline = metrics(trial['rounds'][PHASE_SIZE:],trial['baseline'])
            candidate = metrics(trial['rounds'][PHASE_SIZE:],trial['candidate'])
            trial['confirmation_metrics']=dict(baseline=baseline,candidate=candidate)
            trial['confirmation_native']=compare_native(baseline,candidate)
            accepted = improves(candidate,baseline) and trial['confirmation_native']['decision']['selected']=='candidate'
            trial['status']='ADOPTED' if accepted else 'REJECTED'
            if accepted:
                state['adaptations'][digest(trial['context'])]=dict(context=trial['context'],
                    genome=trial['candidates'][trial['candidate']], evidence='LOCAL_PROSPECTIVE_OPERATIONAL_COMPARISON')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--node-state',type=Path,required=True)
    commands=parser.add_subparsers(dest='command',required=True)
    commands.add_parser('status')
    ingest=commands.add_parser('observe'); ingest.add_argument('file',type=Path)
    begin=commands.add_parser('begin'); begin.add_argument('id'); begin.add_argument('context',type=Path)
    predict=commands.add_parser('predict'); predict.add_argument('id'); predict.add_argument('--after'); predict.add_argument('--before',required=True)
    feedback=commands.add_parser('feedback'); feedback.add_argument('id'); feedback.add_argument('file',type=Path)
    args=parser.parse_args()
    from .internet import InternetNode
    cfg=InternetNode(args.node_state).load(); node=Node(args.node_state/'memory',cfg['node_id']); organism=Organism(node)
    if args.command=='status': result=organism.status()
    elif args.command=='observe': result=node.ingest(decode(args.file.read_bytes()))
    elif args.command=='begin': result=organism.begin(args.id,decode(args.context.read_bytes()))
    elif args.command=='predict': result=organism.predict(args.id,args.after,args.before)
    else: result=organism.feedback(args.id,decode(args.file.read_bytes()))
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__': main()
