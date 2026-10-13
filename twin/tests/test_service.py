"""Service and loopback boundary checks, separate from mathematical acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from genius_twin.app import create_app


class ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "case.sqlite3"
        self.app = create_app(self.db, testing=True)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def initial(self):
        response = self.client.post("/api/cases", json={"text": "Quiero cuidar un semillero durante 14 días"})
        self.assertEqual(response.status_code, 201)
        result = response.get_json()
        return result["case"]["id"], result["proposal"]["id"]

    def confirm(self, pid, base=0, key="initial-confirmation"):
        return self.client.post(f"/api/proposals/{pid}/accept", json={"base_version": base,
            "confirmed": True, "acknowledge_synthetic": True, "idempotency_key": key})

    def relay(self, cid, base=1):
        response = self.client.post(f"/api/cases/{cid}/proposals", json={"base_version": base,
            "kind": "hypothetical_intervention", "text": "Formación al día 9; A cubre si B falta.",
            "structured": {"operation": "apply_relay_policy"}})
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["proposal"]["id"]

    def test_unsupported_story_remains_obligation_not_fake_model(self):
        response = self.client.post("/api/cases", json={"text": "Elegir un discurso para la audiencia"})
        value = response.get_json()
        self.assertIsNone(value["proposal"])
        self.assertEqual(value["case"]["current_version"], 0)
        self.assertEqual(value["obligations"][0]["cause"], "MODELO_PENDIENTE")
        rejected = self.client.post(f'/api/cases/{value["case"]["id"]}/evaluate', json={"version": 1})
        self.assertEqual(rejected.status_code, 404)

    def test_material_confirmation_is_required_and_idempotent(self):
        cid, pid = self.initial()
        response = self.client.post(f"/api/proposals/{pid}/accept", json={"base_version": 0,
            "confirmed": True, "acknowledge_synthetic": False, "idempotency_key": "confirm-key"})
        self.assertEqual(response.status_code, 422)
        first = self.confirm(pid)
        second = self.confirm(pid)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.get_json(), second.get_json())
        self.assertEqual(len(self.client.get(f"/api/cases/{cid}").get_json()["versions"]), 1)

    def test_conflict_is_atomic_and_old_versions_cannot_be_updated(self):
        cid, pid = self.initial()
        self.confirm(pid)
        p1, p2 = self.relay(cid), self.relay(cid)
        self.assertEqual(self.confirm(p1, 1, "first-change-key").status_code, 200)
        self.assertEqual(self.confirm(p2, 1, "second-change-key").status_code, 409)
        data = self.client.get(f"/api/cases/{cid}").get_json()
        self.assertEqual([v["version"] for v in data["versions"]], [1, 2])
        self.assertEqual(data["versions"][0]["model"]["policies"], ["C", "R", "E"])
        self.assertEqual(data["versions"][1]["model"]["policies"], ["C", "R", "E_prime"])
        with sqlite3.connect(self.db) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("UPDATE versions SET model_json='{}'")

    def test_idempotency_key_cannot_identify_a_different_acceptance(self):
        cid, pid = self.initial()
        self.confirm(pid, key="shared-key-123")
        changed = self.relay(cid)
        response = self.confirm(changed, 1, "shared-key-123")
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.get_json()["error"]["code"], "idempotency_conflict")

    def test_restore_creates_history_instead_of_deleting_it(self):
        cid, pid = self.initial()
        self.confirm(pid)
        self.confirm(self.relay(cid), 1, "relay-confirmation")
        response = self.client.post(f"/api/cases/{cid}/proposals", json={"base_version": 2,
            "kind": "restore", "text": "Restaurar la política anterior", "structured": {"version": 1}})
        restored = self.confirm(response.get_json()["proposal"]["id"], 2, "restore-confirmation").get_json()
        self.assertEqual(restored["version"]["version"], 3)
        self.assertEqual(restored["version"]["model"]["policies"], ["C", "R", "E"])
        self.assertEqual(len(self.client.get(f"/api/cases/{cid}").get_json()["versions"]), 3)

    def test_loopback_origin_and_json_guards(self):
        self.assertEqual(self.client.get("/api/cases", headers={"Host": "evil.example"}).status_code, 403)
        self.assertEqual(self.client.post("/api/cases", json={"text": "plantas"}, headers={"Origin": "https://evil.example"}).status_code, 403)
        self.assertEqual(self.client.post("/api/cases", data="text=plantas").status_code, 415)
        self.assertEqual(self.client.post("/api/cases", data='{"text":"plantas","text":"another"}', content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/cases", data='{"text":"plantas","x":NaN}', content_type="application/json").status_code, 400)
        self.assertEqual(self.client.post("/api/cases", data='{"text":"plantas","x":1.5}', content_type="application/json").status_code, 400)
        response = self.client.get("/api/capabilities")
        self.assertNotIn("Access-Control-Allow-Origin", response.headers)
        self.assertIn("frame-ancestors 'none'", response.headers["Content-Security-Policy"])

    def test_real_evaluation_is_bound_to_version_and_export_preserves_native(self):
        cid, pid = self.initial()
        self.confirm(pid)
        first = self.client.post(f"/api/cases/{cid}/evaluate", json={"version": 1}).get_json()
        self.assertEqual(first["job"]["status"], "completed", first)
        result = first["evaluation"]
        self.assertTrue(result["verification"]["valid"])
        self.assertEqual(result["canonical_results"]["policies"]["E"]["pvs"]["value"], "5/6")
        self.assertIsNone(result["rc01_receipt"])
        self.confirm(self.relay(cid), 1, "relay-confirmation")
        later = self.client.post(f"/api/cases/{cid}/evaluate", json={"version": 2}).get_json()["evaluation"]
        self.assertNotEqual(result["native_result"]["input_digest"], later["native_result"]["input_digest"])
        self.assertEqual(later["canonical_results"]["policies"]["E_prime"]["pvs"]["value"], "1/1")
        exported = self.client.get(f"/api/cases/{cid}/export").get_json()
        historical = [x for x in exported["dossier"]["evaluations"] if x["job"]["version"] == 1][0]
        self.assertEqual(historical["evaluation"]["native_result"], result["native_result"])
        self.assertEqual(json.loads(result["native_runs"]["robust"]["native_result_json"]), result["native_result"])

    def test_observation_requires_frozen_prediction_and_preserves_it(self):
        cid, pid = self.initial()
        self.confirm(pid)
        observation = {"base_version": 1, "policy_id": "R", "scenario_id": "HA", "day": 10,
                       "variable": "water_in_tray_liters", "value": "1", "unit": "L",
                       "observed_at": "2026-01-01T12:00:00+00:00", "source": "Synthetic test observation; no field data",
                       "idempotency_key": "observation-fixture"}
        self.assertEqual(self.client.post(f"/api/cases/{cid}/observations", json=observation).status_code, 422)
        before = self.client.post(f"/api/cases/{cid}/evaluate", json={"version": 1}).get_json()
        accepted = self.client.post(f"/api/cases/{cid}/observations", json=observation)
        self.assertEqual(accepted.status_code, 201, accepted.get_json())
        value = accepted.get_json()
        self.assertEqual(value["observation"]["prediction_job_id"], before["job"]["id"])
        self.assertEqual(value["observation"]["comparison"]["delta_exact"], "-1/1")
        self.assertEqual(value["observation"]["comparison"]["temporal_relation"], "RETROSPECTIVE_COMPARISON_NOT_PROSPECTIVE_VALIDATION")
        self.assertEqual(value["case"]["status"], "review_required")
        again = self.client.post(f"/api/cases/{cid}/observations", json=observation)
        self.assertEqual(again.get_json(), value)
        self.assertEqual(self.client.get(f'/api/jobs/{before["job"]["id"]}').get_json(), before)
        revised = self.client.post(f"/api/cases/{cid}/evaluate", json={"version": 2}).get_json()["evaluation"]
        self.assertEqual(revised["recommendation_status"], "SUSPENDED_PENDING_MODEL_REVIEW")


if __name__ == "__main__":
    unittest.main()
