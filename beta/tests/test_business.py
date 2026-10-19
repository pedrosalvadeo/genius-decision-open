"""Decision report for companies: boundary tags, the planetary view and the endpoints, with a fake language model."""
from copy import deepcopy
import json
import time
from pathlib import Path
import tempfile
import unittest

from genius_beta.app import create_app
from genius_beta import business
from test_compare import DRAFT, FakeClient

TAGGED = deepcopy(DRAFT)
TAGGED["stocks"][2]["boundary"] = "freshwater"
TAGGED["step_label"] = "año"


class ReportTests(unittest.TestCase):
    def test_planetary_view_after_a_missing_tag_is_repaired(self):
        client = FakeClient([json.dumps(DRAFT), json.dumps(TAGGED)])
        result = business.report(client, "¿Plantamos más?")
        self.assertEqual(result["status"], "EVALUATED", result)
        self.assertIn("no stock carries a planetary boundary", result["repairs"][0])
        self.assertEqual(client.calls[0]["system"], business.MODELLER)
        self.assertEqual((result["boundaries"], result["step_label"]), ({"buffer": "freshwater"}, "año"))
        [row] = result["planetary"]
        self.assertEqual((row["boundary"], row["direction"], row["initial"]), ("freshwater", "higher", "2/1"))
        self.assertEqual(set(row["by_scenario"]), {"usual", "peak"})
        self.assertEqual(set(row["by_scenario"]["peak"]), {"keep", "plan"})
        for sid, best in row["most_room"].items():
            finals = {r: row["by_scenario"][sid][r]["final"] for r in ("keep", "plan")}
            self.assertTrue(best, finals)

    def test_tags_must_be_known_and_welfare(self):
        bad = deepcopy(TAGGED)
        bad["stocks"][2]["boundary"] = "happiness"
        with self.assertRaisesRegex(ValueError, "boundary must be one of"):
            business.tags(bad, business.compare.expand(bad))
        unbound = deepcopy(TAGGED)
        unbound["stocks"][0]["boundary"] = "climate"
        with self.assertRaisesRegex(ValueError, "welfare dimensions"):
            business.tags(unbound, business.compare.expand(unbound))

    def test_question_needs_a_decision(self):
        self.assertIsNone(business.question_from({"company": "Bodega"}))
        text = business.question_from({"company": "Bodega", "decision": "Plantar", "lang": "en"})
        self.assertIn("Decisión / Decision: Plantar", text)
        self.assertIn("in English", text)


class BoundaryDataTests(unittest.TestCase):
    def test_nine_boundaries_laws_and_pages_agree(self):
        static = Path(business.__file__).parent / 'static'
        data = json.loads((static / 'boundaries.json').read_text())
        ids = [b['id'] for b in data['boundaries']]
        self.assertEqual(ids, list(business.BOUNDARIES))
        self.assertEqual(sum(b['crossed'] for b in data['boundaries']), 7)
        for law in data['laws']:
            self.assertTrue(set(law['boundaries']) <= set(ids), law['id'])
            self.assertTrue(law['es']['name'] and law['en']['name'] and law['url'].startswith('https://'))
        import importlib.util
        spec = importlib.util.spec_from_file_location('build_pages', Path(business.__file__).parents[1] / 'tools' / 'build_business_pages.py')
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        self.assertEqual((static / 'business.html').read_text(), build.page('en', data), 'run beta/tools/build_business_pages.py')
        self.assertEqual((static / 'empresas.html').read_text(), build.page('es', data), 'run beta/tools/build_business_pages.py')


class EndpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.app = create_app(dict(DATA_DIR=root, DATABASE=root / 'db.sqlite3', SUSPEND_FILE=root / 'SUSPENDED',
                                   PUBLIC_URL='http://localhost', TESTING=True, ENV='development', REGISTRATION_OPEN=True,
                                   COMPARE_CLIENT=FakeClient([json.dumps(TAGGED)]), MAX_COMPARE_DAILY=1))
        self.http = self.app.test_client()
        r = self.http.post('/api/register', json=dict(username='empresa', password='A-long-password-123', privacy_accepted=True,
                                                      privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
        self.csrf = {'X-CSRF-Token': r.json['csrf_token']}

    def tearDown(self):
        self.temp.cleanup()

    def collect(self, job):
        for _ in range(200):
            r = self.http.get('/api/business/report/' + job)
            if r.status_code != 200 or r.json.get('status') != 'WORKING':
                return r
            time.sleep(0.05)
        self.fail('report never finished')

    def test_other_users_cannot_collect_a_report(self):
        started = self.http.post('/api/business/report', json={'decision': 'Plantar 40 ha'}, headers=self.csrf)
        other = self.app.test_client()
        o = other.post('/api/register', json=dict(username='otra', password='A-long-password-123', privacy_accepted=True,
                                                   privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
        self.assertEqual(o.status_code, 201, o.json)
        self.assertEqual(other.get('/api/business/report/' + started.json['job']).status_code, 404)
        self.assertEqual(self.collect(started.json['job']).json['status'], 'EVALUATED')

    def test_pages_report_recalculation_and_limit(self):
        for path in ('/business', '/empresas', '/business/report', '/empresas/informe'):
            self.assertEqual(self.http.get(path).status_code, 200, path)
        self.assertEqual(self.app.test_client().post('/api/business/report', json={'decision': 'x'}).status_code, 401)
        self.assertEqual(self.http.post('/api/business/report', json={'company': 'x'}, headers=self.csrf).status_code, 400)
        started = self.http.post('/api/business/report', json={'decision': 'Plantar 40 ha'}, headers=self.csrf)
        self.assertEqual(started.status_code, 202, started.json)
        r = self.collect(started.json['job'])
        self.assertEqual(r.json['status'], 'EVALUATED', r.json)
        self.assertEqual(self.http.get('/api/business/report/' + started.json['job']).status_code, 404)
        again = self.http.post('/api/business/report', json={'decision': 'Plantar 40 ha'}, headers=self.csrf)
        self.assertEqual(again.status_code, 429)
        model = r.json['model']
        model['scenarios'][1]['events'][1]['drains']['buffer'] = '1'
        re = self.http.post('/api/business/recalculate', json={'model': model, 'boundaries': r.json['boundaries'],
                                                               'step_label': 'año', 'changes': ['Pico: 3 → 1']}, headers=self.csrf)
        self.assertEqual(re.status_code, 200, re.json)
        self.assertTrue(re.json['recalculated'])
        self.assertEqual(re.json['planetary'][0]['boundary'], 'freshwater')
        bad = self.http.post('/api/business/recalculate', json={'model': model, 'boundaries': {'water': 'climate'}}, headers=self.csrf)
        self.assertEqual(bad.status_code, 400)


if __name__ == '__main__':
    unittest.main()
