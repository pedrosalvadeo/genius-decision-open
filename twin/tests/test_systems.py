"""Independent graph oracles, evidence identity and version/authorization boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from genius_twin import registry, systems
from genius_twin.app import create_app


class SystemGraphTests(unittest.TestCase):
    def setUp(self):
        fixture = systems.example()
        self.model, self.observation, self.scope = (fixture[k] for k in ('model', 'observation', 'scope'))

    def test_candidates_preserve_overlap_identity_and_external_impacts(self):
        saved = deepcopy(self.observation)
        recognized = systems.recognize(self.observation)
        self.assertEqual(self.observation, saved)
        groups = {tuple(c['members']) for c in recognized['candidates']}
        self.assertEqual(groups, {('neighbors',), ('source', 'target', 'team', 'time'),
                                 ('neighbors', 'source', 'target', 'team', 'time')})
        core = next(c for c in recognized['candidates'] if len(c['members']) == 4)
        self.assertEqual(core['potential_impacts'], ['neighbors'])
        self.assertEqual(core['crossing_relations'], ['downstream'])
        self.assertEqual(core['dependencies'], [])
        self.assertFalse(recognized['probabilities_inferred'])
        self.assertEqual(recognized['empirical_validation'], 'NOT_ASSESSED')
        # Reordering declarations never changes candidate identities or members.
        self.observation['entities'].reverse()
        self.observation['relations'].reverse()
        self.assertEqual(systems.recognize(self.observation)['candidates'], recognized['candidates'])

    def test_directional_dependencies_impacts_cycles_and_uncertainty(self):
        o = self.observation
        o['entities'] = [dict(id=i, label=i, kind='physical', evidence_ids=['demo']) for i in 'abcde']
        o['evidence'][0]['basis'] = 'inference'
        o['relations'] = [dict(id='r'+str(n), source=a, target=b, kind=k, evidence_ids=['demo'])
                          for n, (a,b,k) in enumerate([('a','b','supplies'), ('b','c','affects'),
                              ('c','d','affects'), ('d','b','affects'), ('b','e','depends_on')])]
        systems.validate(o)
        boundary = systems.boundary(o, ['b'])
        self.assertEqual(boundary['dependencies'], ['a', 'e'])
        self.assertEqual(boundary['potential_impacts'], ['c', 'd'])
        self.assertEqual(boundary['required_evaluation_entities'], list('abcde'))
        # An uncertain/inferred edge cannot be silently dropped from impact scope.
        self.assertEqual(boundary['coverage'], 'DECLARED_GRAPH_ONLY')

    def test_impact_cannot_be_excluded_and_identity_cannot_be_double_counted(self):
        receipt = systems.review_scope(self.model, self.observation, self.scope)
        self.assertEqual(receipt['unmapped_entities'], ['neighbors'])
        self.assertTrue(receipt['review_required'])
        reduced = deepcopy(self.scope)
        reduced['evaluation_entities'].remove('neighbors')
        with self.assertRaisesRegex(ValueError, 'omite'):
            systems.review_scope(self.model, self.observation, reduced)
        self.model['carriers'].append(dict(id='team2', label='Equipo en otra vista', kind='organization'))
        self.scope['bindings'].append(dict(collection='carriers', model_id='team2', entity_id='team'))
        with self.assertRaisesRegex(ValueError, 'dos portadores'):
            systems.review_scope(self.model, self.observation, self.scope)

    def test_schema_dates_references_and_limits_fail_closed(self):
        def broken(fn):
            obj = deepcopy(self.observation)
            fn(obj)
            with self.assertRaises(ValueError):
                systems.recognize(obj)
        for fn in [lambda o:o.update(extra=True), lambda o:o['evidence'][0].update(source='  '),
                   lambda o:o['evidence'][0].update(observed_at='2026-01-01T00:00:00'),
                   lambda o:o['evidence'][0].update(observed_at='2027-01-01T00:00:00Z'),
                   lambda o:o['entities'][0].update(evidence_ids=['missing']),
                   lambda o:o['relations'][0].update(target='missing'),
                   lambda o:o['entities'].append(dict(o['entities'][0], label='Other')),
                   lambda o:o.update(unknowns=[]),
                   lambda o:o.update(entities=[dict(id='e'+str(i),label='e',kind='physical',evidence_ids=['demo']) for i in range(33)])]:
            broken(fn)


class SystemLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / 'twin.sqlite3'
        self.app = create_app(self.path, testing=True, evaluator=registry.evaluate)
        self.client = self.app.test_client()
        self.service = self.app.extensions['twin_service']
        self.fixture = systems.example()
        self.cid = self.post('/cases', dict(text='Sistemas de prueba', profile=registry.STOCKFLOW))['case']['id']

    def tearDown(self):
        self.temp.cleanup()

    def post(self, path, payload, expected=200):
        r = self.client.post('/api'+path, json=payload)
        self.assertIn(r.status_code, (200, 201) if expected == 200 else (expected,), r.json)
        return r.json

    def observe(self, revision=0, base=0, observation=None, expected=200):
        return self.post(f'/cases/{self.cid}/systems', dict(base_version=base, observation_revision=revision,
            idempotency_key='observation-'+str(revision), observation=observation or self.fixture['observation']), expected)

    def propose(self, kind, base, structured, expected=200):
        return self.post(f'/cases/{self.cid}/proposals', dict(base_version=base,kind=kind,text='Premisas de prueba',structured=structured), expected)

    def accept(self, proposal, base, expected=200):
        return self.post('/proposals/'+proposal['id']+'/accept',dict(base_version=base, confirmed=True,
            acknowledge_declared=True,idempotency_key='accept-'+proposal['id']), expected)

    def model(self):
        proposal = self.propose('declared_model',0,{'model':self.fixture['model']})['proposal']
        self.accept(proposal,0)

    def scope(self, base=1, revision=1):
        scope = dict(self.fixture['scope'], observation_revision=revision)
        proposal = self.propose('system_scope',base,{'scope':scope})['proposal']
        return self.accept(proposal,base)

    def test_observe_before_model_native_evaluation_and_frozen_export(self):
        first = self.observe()
        self.assertEqual(first, self.observe())
        self.assertFalse(first['model_changed'])
        self.assertEqual(self.service.read_case(self.cid)['case']['current_version'],0)
        self.model()
        self.post(f'/cases/{self.cid}/evaluate', {'version':1},409)
        confirmed = self.scope()
        self.assertEqual(confirmed['version']['model'], self.fixture['model'])
        evaluated = self.post(f'/cases/{self.cid}/evaluate', {'version':2})
        self.assertEqual(evaluated['job']['status'], 'completed')
        self.assertTrue(evaluated['evaluation']['verification']['valid'])
        self.assertEqual(evaluated['evaluation']['recommendation_status'],'SUSPENDED_PENDING_MODEL_REVIEW')
        self.assertEqual(evaluated['evaluation']['system_scope']['unmapped_entities'], ['neighbors'])
        self.assertEqual(evaluated['evaluation']['canonical_results'], registry.evaluate(self.fixture['model'])['canonical_results'])
        exported = self.service.export(self.cid)['dossier']
        self.assertEqual(len(exported['system_observations']),1)
        self.assertEqual(exported['observations'],[])
        self.assertEqual(exported['evaluations'][0]['evaluation'],evaluated['evaluation'])
        compare = self.service.compare(self.cid,1,2)
        self.assertEqual(compare['model_changes'], [])
        self.assertFalse(compare['system_scope_comparison']['same_scope'])

    def test_revisions_stale_proposals_idempotence_and_immutable_history(self):
        self.observe(); self.model()
        proposal = self.propose('system_scope',1,{'scope':self.fixture['scope']})['proposal']
        second = deepcopy(self.fixture['observation'])
        second['unknowns'].append('Se revisa una nueva fuente sin afirmar la desaparición de relaciones.')
        recorded = self.observe(1,1,second)
        self.accept(proposal,1,409)
        self.scope(1,2)
        frozen = self.post(f'/cases/{self.cid}/evaluate',{'version':2})
        self.observe(2,2,second)
        self.assertEqual(self.service.system_context(self.cid)['status'],'REVIEW_REQUIRED')
        self.post(f'/cases/{self.cid}/evaluate',{'version':2},409)
        self.assertEqual(self.service.read_job(frozen['job']['id']),frozen)
        self.assertEqual(self.observe(1,1,second),recorded)  # safe historical retry
        self.assertEqual(self.observe(0,0,second,409)['error']['code'],'idempotency_conflict')
        self.assertEqual(len(self.service.export(self.cid)['dossier']['system_observations']),3)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.service.store.transaction() as conn:
                conn.execute('UPDATE observations SET record_json=? WHERE case_id=?',('{}',self.cid))
        with self.assertRaises(sqlite3.IntegrityError):
            with self.service.store.transaction() as conn:
                conn.execute('DELETE FROM observations WHERE case_id=?',(self.cid,))
        reopened = create_app(self.path,testing=True).extensions['twin_service']
        self.assertEqual(reopened.system_context(self.cid)['observation_revision'],3)

    def test_identity_omission_model_edit_and_erasure(self):
        self.observe(); self.model(); self.scope()
        bad = deepcopy(self.fixture['observation']); bad['entities'][0]['kind']='person'
        self.assertEqual(self.observe(1,2,bad,422)['error']['code'],'identity_conflict')
        # Model edits cannot carry an old boundary receipt as current.
        changed = deepcopy(self.fixture['model']); changed['name']='Nueva premisa'
        p = self.propose('declared_model',2,{'model':changed})['proposal']; self.accept(p,2)
        self.assertEqual(self.service.system_context(self.cid)['status'],'REVIEW_REQUIRED')
        self.post(f'/cases/{self.cid}/evaluate',{'version':3},409)
        # A later snapshot may omit an entity, but its previous record survives.
        reduced = deepcopy(self.fixture['observation'])
        reduced['entities']=[e for e in reduced['entities'] if e['id']!='neighbors']
        reduced['relations']=[r for r in reduced['relations'] if r['id']!='downstream']
        self.observe(1,3,reduced)
        records=self.service.read_case(self.cid)['system_observations']
        self.assertEqual(len(records[0]['observation']['entities']),5)
        self.assertEqual(len(records[1]['observation']['entities']),4)
        self.assertEqual(records[1]['historical_gaps']['unobserved_entities'],['neighbors'])
        self.assertEqual(records[1]['historical_gaps']['unobserved_relations'],['downstream'])
        scope = deepcopy(self.fixture['scope']); scope['observation_revision']=2
        scope['evaluation_entities'].remove('neighbors')
        proposal = self.propose('system_scope',3,{'scope':scope})['proposal']
        self.assertTrue(proposal['metadata']['review_required'])
        result=self.client.delete('/api/cases/'+self.cid,json={'base_version':3})
        self.assertEqual(result.status_code,200,result.json)
        self.assertEqual(self.service.store.read('SELECT * FROM observations'),[])

    def test_limits_and_read_only_recognition(self):
        self.service.execution_context['system_observation_limit']=1
        first=self.observe()
        self.assertEqual(first,self.observe())
        self.observe(1,0,expected=429)
        for _ in range(2):
            state=self.client.get('/api/cases/'+self.cid+'/systems')
            self.assertEqual(state.status_code,200)
        self.assertEqual(len(self.service._system_records(self.cid)),1)
        self.assertEqual(self.client.get('/api/systems/schema').json['title'],systems.FORMAT)


if __name__ == '__main__':
    unittest.main()
