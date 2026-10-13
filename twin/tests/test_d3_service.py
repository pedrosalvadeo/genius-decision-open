"""D3 service boundaries; evaluator doubles are not mathematical evidence."""
from copy import deepcopy
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from genius_twin.app import create_app
from genius_twin import registry
from genius_twin.__main__ import exclusive_database


def stub_result(model):
    return {"canonical_results": {"profile": model["profile"], "marker": "TEST_DOUBLE"},
            "native_result": {"marker": "TEST_DOUBLE"}, "verification": {"valid": True}}


class D3ServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "db.sqlite3"
        self.app = create_app(self.path, testing=True, evaluator=stub_result)
        self.client = self.app.test_client()
        self.service = self.app.extensions["twin_service"]
        self.model = registry.example("stockflow_care")["model"]

    def tearDown(self):
        self.temp.cleanup()

    def case(self):
        response = self.client.post("/api/cases", json={"text": "Plantas y cuidado configurado", "profile": registry.STOCKFLOW})
        self.assertEqual(response.status_code, 201)
        return response.get_json()

    def proposal(self, cid, model=None, base=0):
        response = self.client.post(f"/api/cases/{cid}/proposals", json={"base_version": base,
            "kind": "declared_model", "text": "Premisas declaradas para análisis", "structured": {"model": model or self.model}})
        self.assertEqual(response.status_code, 201, response.get_json())
        return response.get_json()["proposal"]["id"]

    def accept(self, pid, base=0, key="declared-confirmation"):
        return self.client.post(f"/api/proposals/{pid}/accept", json={"base_version": base,
            "confirmed": True, "acknowledge_declared": True, "idempotency_key": key})

    def confirmed(self):
        created = self.case()
        cid = created["case"]["id"]
        response = self.accept(self.proposal(cid))
        self.assertEqual(response.status_code, 200, response.get_json())
        return cid

    def test_explicit_general_draft_never_becomes_semillero(self):
        created = self.case()
        self.assertIsNone(created["proposal"])
        self.assertEqual(created["case"]["profile"], registry.STOCKFLOW)
        self.assertEqual(created["case"]["current_version"], 0)
        self.assertEqual(created["obligations"][0]["cause"], "MODELO_PENDIENTE")
        cid = created["case"]["id"]
        payload = {"base_version": 0, "draft_revision": 0, "text": "Plan incompleto", "model": {"profile": registry.STOCKFLOW}}
        saved = self.client.patch(f"/api/cases/{cid}/draft", json=payload)
        self.assertEqual(saved.status_code, 200)
        self.assertEqual(saved.get_json()["draft"]["state"], "DRAFT_NOT_ADMITTED")
        self.assertEqual(self.client.patch(f"/api/cases/{cid}/draft", json=payload).status_code, 409)
        reopened = create_app(self.path, testing=True, evaluator=stub_result).test_client().get(f"/api/cases/{cid}").get_json()
        self.assertEqual(reopened["draft"]["model"], payload["model"])
        self.assertEqual(reopened["versions"], [])

    def test_declared_confirmation_is_specific_and_atomic(self):
        cid = self.case()["case"]["id"]
        first, second = self.proposal(cid), self.proposal(cid)
        wrong = self.client.post(f"/api/proposals/{first}/accept", json={"base_version": 0,
            "confirmed": True, "acknowledge_synthetic": True, "idempotency_key": "wrong-recognition"})
        self.assertEqual(wrong.status_code, 422)
        received = self.accept(first)
        self.assertEqual(received.status_code, 200)
        self.assertEqual(self.accept(first).get_json(), received.get_json())
        self.assertEqual(self.accept(second, key="second-confirmation").status_code, 409)
        version = received.get_json()["version"]
        self.assertEqual(received.get_json()["case"]["obligations"], [])
        self.assertFalse(version["metadata"]["synthetic"])
        self.assertEqual(version["metadata"]["evidence_origin"], "USER_DECLARED_MODEL")

    def test_invalid_complete_model_does_not_enter_history(self):
        cid = self.case()["case"]["id"]
        response = self.client.post(f"/api/cases/{cid}/proposals", json={"base_version": 0,
            "kind": "declared_model", "text": "Falta el modelo", "structured": {"model": {"profile": registry.STOCKFLOW}}})
        self.assertEqual(response.status_code, 400)
        state = self.client.get(f"/api/cases/{cid}").get_json()
        self.assertEqual(state["proposals"], [])
        self.assertEqual(state["versions"], [])

    def test_execution_identity_prevents_stale_cache(self):
        cid = self.confirmed()
        first = self.service.evaluate(cid, {"version": 1})
        repeat = self.service.evaluate(cid, {"version": 1})
        self.assertEqual(first["job"]["id"], repeat["job"]["id"])
        self.service.execution_context = {"runner_revision": "changed-for-test"}
        changed = self.service.evaluate(cid, {"version": 1})
        self.assertNotEqual(first["job"]["id"], changed["job"]["id"])
        self.assertNotEqual(first["job"]["execution_key"], changed["job"]["execution_key"])
        self.assertEqual(first, self.service.read_job(first["job"]["id"]))
        self.assertEqual(changed["evaluation"]["admission"], "DECLARED_MODEL_ONLY")

    def test_recovery_explicit_and_timeout_is_not_negative_result(self):
        cid = self.confirmed()
        with self.service.store.transaction() as conn:
            conn.execute("INSERT INTO jobs(id,case_id,version,status,created_at) VALUES('orphan',?,1,'running','2026-01-01T00:00:00+00:00')", (cid,))
        other = create_app(self.path, testing=True, evaluator=stub_result)
        self.assertEqual(other.extensions["twin_service"].read_job("orphan")["job"]["status"], "running")
        self.assertEqual(self.service.recover_jobs()["recovered_jobs"], 1)
        self.assertIsNone(self.service.read_job("orphan")["evaluation"])
        def timeout(model):
            raise TimeoutError("test")
        self.service.evaluator = timeout
        result = self.service.evaluate(cid, {"version": 1})
        self.assertEqual(result["job"]["status"], "failed")
        self.assertEqual(result["job"]["error"]["code"], "evaluation_timeout")
        self.assertIsNone(result["evaluation"])

    def test_restore_compare_export_and_whole_dossier_erasure(self):
        cid = self.confirmed()
        model = deepcopy(self.model)
        model["require_all_scenarios"] = not model["require_all_scenarios"]
        self.assertEqual(self.accept(self.proposal(cid, model, 1), 1, "changed-confirmation").status_code, 200)
        restored = self.client.post(f"/api/cases/{cid}/proposals", json={"base_version": 2,
            "kind": "restore", "text": "Restituir premisas iniciales", "structured": {"version": 1}}).get_json()
        self.assertEqual(self.accept(restored["proposal"]["id"], 2, "restore-confirmation").status_code, 200)
        compare = self.service.compare(cid, 1, 3)
        self.assertEqual(compare["model_changes"], [])
        exported = self.service.export(cid)
        self.assertEqual(len(exported["dossier"]["versions"]), 3)
        with sqlite3.connect(self.path) as conn:
            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute("DELETE FROM versions WHERE case_id=?", (cid,))
        self.assertEqual(self.client.delete(f"/api/cases/{cid}", json={"base_version": 2}).status_code, 409)
        self.assertEqual(self.client.delete(f"/api/cases/{cid}", json={"base_version": 3}).status_code, 200)
        for table in ("cases", "versions", "proposals", "jobs", "drafts", "observations", "idempotency", "erasure_markers"):
            self.assertEqual(self.service.store.one(f"SELECT count(*) AS n FROM {table}")["n"], 0)

    def test_profiles_and_closed_example_lookup(self):
        self.assertEqual(len(self.client.get("/api/profiles").get_json()["profiles"]), 2)
        self.assertEqual(self.client.get("/api/examples/stockflow_care").get_json()["model"], self.model)
        self.assertEqual(self.client.get("/api/examples/not-a-file").status_code, 404)
        schema = self.client.get(f"/api/profiles/{registry.STOCKFLOW}/schema")
        self.assertEqual(schema.status_code, 200)

    def test_second_local_launcher_cannot_recover_a_live_store(self):
        cid = self.confirmed()
        with self.service.store.transaction() as conn:
            conn.execute("INSERT INTO jobs(id,case_id,version,status,created_at) VALUES('live',?,1,'running','2026-01-01T00:00:00+00:00')", (cid,))
        with exclusive_database(self.path):
            second = subprocess.run([sys.executable, "-m", "genius_twin", "--database", str(self.path), "--port", "18765"],
                                    capture_output=True, timeout=5)
            self.assertEqual(second.returncode, 2)
            self.assertIn("Ya existe un servidor", second.stderr.decode())
            self.assertEqual(self.service.read_job("live")["job"]["status"], "running")
        with exclusive_database(self.path):
            self.assertEqual(self.service.recover_jobs()["recovered_jobs"], 1)
        self.assertEqual(self.service.read_job("live")["job"]["status"], "interrupted")


if __name__ == "__main__":
    unittest.main()
