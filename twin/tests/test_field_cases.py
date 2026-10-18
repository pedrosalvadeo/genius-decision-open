"""Cited field cases are listed by the API and open through the regular world-construction flow."""
from pathlib import Path
import tempfile
import unittest

from genius_twin import construction, registry
from genius_twin.process_runner import ProcessEvaluator
from genius_twin.app import create_app


class FieldCaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.client = create_app(Path(self.temp.name) / 'db.sqlite3', testing=True, evaluator=registry.evaluate).test_client()

    def tearDown(self):
        self.temp.cleanup()

    def post(self, path, payload):
        response = self.client.post('/api' + path, json=payload)
        self.assertIn(response.status_code, (200, 201), response.json)
        return response.json

    def test_catalog_and_full_flow_for_each_case(self):
        rows = self.client.get('/api/field-cases').json['field_cases']
        self.assertEqual({row['id'] for row in rows}, {'denver_water_2026', 'lake_mead_2027', 'lake_mead_2028', 'mendoza_potrerillos_2026', 'us_blood_2026'})
        self.assertEqual(self.client.get('/api/field-cases/missing').status_code, 404)
        for row in rows:
            with self.subTest(case=row['id']):
                data = self.client.get('/api/field-cases/' + row['id']).json
                self.assertEqual(data['provenance'], 'CITED_FIELD_CASE_WITH_DECLARED_HYPOTHESES')
                cid = self.post('/cases', dict(text=data['narrative'], title=data['title'], profile=registry.STOCKFLOW))['case']['id']
                self.post(f'/cases/{cid}/systems', dict(base_version=0, observation_revision=0, idempotency_key='observe-' + cid, observation=data['observation']))
                proposal = self.post(f'/cases/{cid}/proposals', dict(base_version=0, kind='world_model', text=data['narrative'], structured=dict(construction=data['construction'])))['proposal']
                self.post(f"/proposals/{proposal['id']}/accept", dict(base_version=0, confirmed=True, acknowledge_declared=True, idempotency_key='accept-' + cid))
                result = self.post(f'/cases/{cid}/evaluate', dict(version=1))
                self.assertEqual(result['job']['status'], 'completed')
                self.assertTrue(result['evaluation']['verification']['valid'])

    def test_observation_contrasts_a_stock_with_the_frozen_prediction(self):
        data = self.client.get('/api/field-cases/denver_water_2026').json
        cid = self.post('/cases', dict(text=data['narrative'], title=data['title'], profile=registry.STOCKFLOW))['case']['id']
        self.post(f'/cases/{cid}/systems', dict(base_version=0, observation_revision=0, idempotency_key='observe-system', observation=data['observation']))
        proposal = self.post(f'/cases/{cid}/proposals', dict(base_version=0, kind='world_model', text=data['narrative'], structured=dict(construction=data['construction'])))['proposal']
        self.post(f"/proposals/{proposal['id']}/accept", dict(base_version=0, confirmed=True, acknowledge_declared=True, idempotency_key='accept-world'))
        observation = dict(base_version=1, policy_id='keep_ban', scenario_id='dry', day=1, variable='storage', unit='pct_capacity',
                           value='65', observed_at='2026-11-16T12:00:00+00:00', source='Synthetic test observation; no field data',
                           idempotency_key='storage-november')
        self.assertEqual(self.client.post(f'/api/cases/{cid}/observations', json=observation).status_code, 422)
        self.post(f'/cases/{cid}/evaluate', dict(version=1))
        record = self.post(f'/cases/{cid}/observations', observation)['observation']
        self.assertEqual(record['comparison']['predicted_exact'], '131/2')
        self.assertEqual(record['comparison']['delta_exact'], '-1/2')
        self.assertEqual(record['comparison']['status'], 'DISCREPANCY_REQUIRES_REVIEW')
        for field, value in (('variable', 'outdoor_litres'), ('unit', 'hm3'), ('day', 13), ('policy_id', 'unknown')):
            with self.subTest(field=field):
                response = self.client.post(f'/api/cases/{cid}/observations', json={**observation, 'base_version': 2, field: value, 'idempotency_key': 'invalid-' + field})
                self.assertIn(response.status_code, (400, 422), response.json)

    def test_each_case_fits_production_execution_limits(self):
        # Mirrors beta/genius_beta/config.py TWIN_TIMEOUT/TWIN_MEMORY_MB/TWIN_OUTPUT_BYTES defaults.
        evaluator = ProcessEvaluator(timeout=90, memory_mb=384, output_bytes=16777216)
        for row in registry.field_cases():
            with self.subTest(case=row['id']):
                data = registry.field_case(row['id'])
                model = construction.prepare(data['construction'], dict(id='o', revision=1, observation=data['observation'], historical_gaps={}))['model']
                self.assertTrue(evaluator(model)['verification']['valid'])


if __name__ == '__main__':
    unittest.main()
