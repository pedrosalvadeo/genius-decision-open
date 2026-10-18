"""Comparison chat: market answer and Genius answer from the kernel, with a fake language model."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from genius_beta.app import create_app
from genius_beta import compare

DRAFT = {
    "name": "Cuidar con reserva", "horizon": 3, "step_unit": "day",
    "stocks": [{"id": "water", "label": "Agua", "unit": "litros (L)", "initial": 8, "capacity": 8},
               {"id": "time", "label": "Tiempo", "unit": "3 minutos", "kind": "renewable", "initial": 30, "capacity": 30},
               {"id": "buffer", "label": "Reserva viva", "unit": "litros (L)", "initial": 2, "capacity": "4"}],
    "carriers": [{"id": "A", "label": "Persona cuidadora"}, {"id": "P", "label": "Planta", "kind": "living"}],
    "capabilities": [{"id": "care", "label": "Cuidado"}, {"id": "ready", "label": "Reserva lista"}],
    "initial_capabilities": ["care"],
    "actions": [{"id": "manual", "label": "Ordinario", "requires": ["care"], "withdrawals": {"water": 1, "time": 20}, "deposits": {"buffer": 1}},
                {"id": "prepare", "label": "Preparar", "requires": ["care"], "withdrawals": {"water": 2, "time": 30}, "deposits": {"buffer": 2}, "add_capabilities": ["ready"]},
                {"id": "reserve", "label": "Con reserva", "requires": ["care", "ready"], "withdrawals": {"water": 2, "time": 10}, "deposits": {"buffer": 2}}],
    "policies": [{"id": "keep", "label": "Seguir igual", "default_action": "manual"},
                 {"id": "plan", "label": "Preparar y usar reserva", "default_action": "reserve", "rules": [{"steps": [1], "action": "prepare"}]}],
    "scenarios": [{"id": "usual", "label": "Habitual", "events": [{"drains": {"buffer": 1}}] * 3},
                  {"id": "peak", "label": "Pico", "events": [{"drains": {"buffer": 1}}, {"drains": {"buffer": 3}}, {"drains": {"buffer": 0}}]}],
    "law": {"usual": "2/3", "peak": "1/3"},
    "welfare": [{"carrier": "A", "dimension": "time", "label": "Tiempo libre", "stock": "time"},
                {"carrier": "P", "dimension": "reserve", "label": "Reserva", "stock": "buffer"}],
    "task": {"label": "La planta conserva al menos 1 L", "living_carriers": ["P"], "conditions": [{"stock": "buffer", "op": "ge", "threshold": 1}]},
    "assumptions": [{"id": "all", "kind": "SYNTHETIC", "statement": "Cantidades supuestas", "provenance": "Supuesto del modelador a partir de la pregunta"},
                    {"id": "law", "kind": "PROBABILITY", "statement": "Pico en un tercio de los casos"}],
}


class FakeClient:
    def __init__(self, texts):
        self.texts, self.calls = list(texts), []
        self.messages = self

    def with_options(self, **_):
        return self

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(stop_reason="end_turn", content=[SimpleNamespace(type="thinking", thinking=""),
                                                                 SimpleNamespace(type="text", text=self.texts.pop(0))])


class GeniusAnswerTests(unittest.TestCase):
    def test_kernel_reads_life_pvs_and_carriers_after_a_repair(self):
        broken = deepcopy(DRAFT)
        broken["actions"][0]["deposits"] = {"buffer": 5}
        client = FakeClient(["```json\n" + json.dumps(broken) + "\n```", json.dumps(DRAFT)])
        result = compare.genius_answer(client, "¿Cómo cuido la planta?")
        self.assertEqual(result["status"], "EVALUATED", result)
        self.assertEqual(result["attempts"], 2)
        self.assertIn("deposits exceed withdrawals", result["repairs"][0])
        self.assertIn("validator rejected", client.calls[1]["messages"][-1]["content"])
        self.assertEqual(client.calls[0]["system"], compare.MODELLER)
        s = result["summary"]
        routes = {r["id"]: r for r in s["routes"]}
        self.assertEqual(routes["plan"]["keeps_life_in"], ["usual", "peak"])
        self.assertEqual(routes["plan"]["pvs"]["value"], "1/1")
        self.assertEqual(routes["keep"]["loses_life_in"], ["peak"])
        self.assertEqual(routes["keep"]["pvs"]["value"], "2/3")
        self.assertEqual(s["life_filter"]["keep_life_everywhere"], ["plan"])
        self.assertEqual({c["id"]: c["best"] for c in s["carriers"]}, {"A": ["plan"], "P": ["plan"]})
        self.assertEqual(result["model"]["stocks"][1]["initial"], "30/1")
        self.assertEqual([x["unit"] for x in result["model"]["stocks"]], ["litros_L", "u_3_minutos", "litros_L"])
        self.assertEqual(result["model"]["scenarios"][0]["events"][0]["renewables"], {"time": "30/1"})
        self.assertEqual(result["model"]["assumptions"][1]["provenance"], "Supuesto del modelador a partir de la pregunta")

    def test_gives_up_after_three_invalid_models(self):
        result = compare.genius_answer(FakeClient(["no json", "{}", "{\"stocks\": 3}"]), "x")
        self.assertEqual(result["status"], "MODEL_NOT_VALID")
        self.assertEqual(len(result["repairs"]), 3)

    def test_not_a_decision(self):
        result = compare.genius_answer(FakeClient(['{"not_a_decision": "Contame entre qué opciones dudás."}']), "hola")
        self.assertEqual(result, {"status": "NOT_A_DECISION", "explanation": "Contame entre qué opciones dudás.", "attempts": 1})

    def test_market_side_is_the_question_alone(self):
        client = FakeClient(["Mudate."])
        self.assertEqual(compare.market_answer(client, "¿Me mudo?")["text"], "Mudate.")
        self.assertNotIn("system", client.calls[0])
        self.assertEqual(client.calls[0]["messages"], [{"role": "user", "content": "¿Me mudo?"}])


class CompareEndpointTests(unittest.TestCase):
    def make(self, client):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.app = create_app(dict(DATA_DIR=root, DATABASE=root / 'db.sqlite3', SUSPEND_FILE=root / 'SUSPENDED',
                                   PUBLIC_URL='http://localhost', TESTING=True, ENV='development', REGISTRATION_OPEN=True,
                                   COMPARE_CLIENT=client, MAX_COMPARE_DAILY=1))
        self.http = self.app.test_client()
        r = self.http.post('/api/register', json=dict(username='persona', password='A-long-password-123', privacy_accepted=True,
                                                      privacy_version=self.app.config['PRIVACY_VERSION'], adult_confirmed=True))
        self.assertEqual(r.status_code, 201, r.json)
        self.csrf = {'X-CSRF-Token': r.json['csrf_token']}

    def tearDown(self):
        self.temp.cleanup()

    def test_both_sides_and_daily_limit(self):
        self.make(FakeClient(["Respuesta libre", json.dumps(DRAFT)]))
        self.assertEqual(self.http.get('/comparar').status_code, 200)
        self.assertTrue(self.http.get('/api/compare/status').json['enabled'])
        market = self.http.post('/api/compare/market', json={'question': '¿Qué hago?'}, headers=self.csrf)
        self.assertEqual(market.json['text'], 'Respuesta libre')
        genius = self.http.post('/api/compare/genius', json={'question': '¿Qué hago?'}, headers=self.csrf)
        self.assertEqual(genius.json['status'], 'EVALUATED')
        again = self.http.post('/api/compare/market', json={'question': '¿Qué hago?'}, headers=self.csrf)
        self.assertEqual(again.status_code, 429)

    def test_recalculate_with_the_persons_corrections(self):
        self.make(FakeClient([json.dumps(DRAFT)]))
        model = self.http.post('/api/compare/genius', json={'question': 'x'}, headers=self.csrf).json['model']
        model['scenarios'][1]['events'][1]['drains']['buffer'] = '1'  # a milder peak: keeping as usual now keeps life
        r = self.http.post('/api/compare/recalculate', json={'model': model, 'changes': ['Pico, paso 2: 3 → 1']}, headers=self.csrf)
        self.assertEqual(r.status_code, 200, r.json)
        routes = {x['id']: x for x in r.json['summary']['routes']}
        self.assertEqual(routes['keep']['loses_life_in'], [])
        self.assertTrue(r.json['recalculated'])
        self.assertEqual(r.json['model']['assumptions'][-1]['id'], 'person_corrections')
        self.assertIn('3 → 1', r.json['model']['assumptions'][-1]['statement'])
        model['law'] = {'usual': '1/2', 'peak': '1/3'}
        bad = self.http.post('/api/compare/recalculate', json={'model': model}, headers=self.csrf)
        self.assertEqual((bad.status_code, bad.json['error']['code']), (400, 'invalid_model'))

    def test_needs_login_and_a_key(self):
        self.make(None)
        self.assertEqual(self.app.test_client().post('/api/compare/market', json={'question': 'x'}).status_code, 401)
        self.assertFalse(self.http.get('/api/compare/status').json['enabled'])
        r = self.http.post('/api/compare/genius', json={'question': 'x'}, headers=self.csrf)
        self.assertEqual((r.status_code, r.json['error']['code']), (503, 'compare_not_configured'))
        self.assertEqual(self.http.post('/api/compare/genius', json={'question': ''}, headers=self.csrf).status_code, 400)


if __name__ == '__main__':
    unittest.main()
