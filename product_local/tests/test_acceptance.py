"""Behavioral conformance through the public CLI from fresh local dossiers.

Expected answers below are fixed rational examples and received contract rules.
No production module or Kernel is imported to manufacture expected answers.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from independent_client import audit_chain, audit_response, ConsumerRejected

ROOT = Path(__file__).resolve().parents[1]
R1 = Path(os.environ.get("GENIUS_R1_BASELINE", ROOT.parent / "baseline/R1")).resolve()
R0 = Path(os.environ.get("GENIUS_R0_BASELINE", ROOT.parent / "baseline/received_baseline/R0")).resolve()
SPEC = {"identity": "synthetic-register-p", "unit": "h_contractual", "period": "synthetic-week-1",
        "population": "synthetic-assignments-p", "method": "stipulated-contract-credit/1"}
PERMISSIONS = {"access":"ALLOWED", "use":"ALLOWED", "basis":"Synthetic test fixture authorized for conformance only."}
CAUSES = ["DERIVABLE", "YA_DISPONIBLE", "IRRELEVANTE_DEMOSTRADO", "DATO_EXTERNO",
          "DEFINICION_MODELO", "PREFERENCIA", "CAPACIDAD_AUSENTE", "COMPUTO_PENDIENTE", "DISENO_ESTUDIO"]


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def known(value):
    return {"state":"PV_KNOWN", "value":value, "unit":"h_contractual", "basis":["synthetic stipulation"]}


def unknown():
    return {"state":"PV_UNKNOWN", "reasons":["Credit not supplied in fixture"], "obligation_refs":["O"]}


def obligation(cause="DERIVABLE", identifier="O", query="Q"):
    return {"id":identifier, "revision":1, "query_ref":query, "affected_claims":[query],
            "primary_cause":cause, "secondary_causes":[],
            "classification_basis":[{"evidence":"Synthetic fixture", "mechanism":cause}],
            "provenance":[{"kind":"SYNTHETIC_STIPULATION", "reason":"Conformance fixture; no empirical claim"}],
            "input_spec":{"object":"synthetic register", "field":"component", "type":"exact rational", "unit":"h_contractual",
                          "period":"synthetic-week-1", "population":"synthetic-assignments-p", "method":"stipulated-contract-credit/1",
                          "state":"UNKNOWN", "reason":"Requires stated operation or dependency"},
            "derivation_rule":{"kind":"NO_DERIVATION", "reason":"Only explicit operation may produce a witness"},
            "dependencies":[], "owner":{"role":"test-custodian", "task":"Supply compatible fixture only", "assigned_person":"UNKNOWN"},
            "permitted_use":["formal synthetic conformance"], "prohibited_inferences":["human utility", "empirical truth", "authorization to act"],
            "status":"OPEN", "closure":{"predicate":"EXACT_QUERY_RESULT_RECEIVED", "witness_refs":[],
                                           "verifier":"local contract executor", "verified":False},
            "reopen":{"condition":"Pertinent query, rule, source or scope change", "affected_refs":[query]},
            "next_action":"Evaluate scoped operation or return explicit dependency", "budget_ref":"request.budget", "attempts":[]}


class Fixture:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.request = {"format":"genius-local-request/0.1.0", "request_id":"synthetic-request", "revision":1,
                        "supersedes":None, "queries":[], "artifacts":[], "obligations":[],
                        "budget":{"max_operations":64, "max_certificates":2, "certificate_timeout_seconds":60},
                        "operations":[], "novelty":{"reason":"New synthetic conformance dossier", "changed_refs":[]}}

    def artifact(self, identifier, content, kind="SYNTHETIC_STIPULATION", permissions=None):
        raw = content if isinstance(content, bytes) else canonical(content)
        path = self.directory / (identifier + ".json")
        path.write_bytes(raw)
        meta = {"id":identifier, "role":"conformance evidence", "path":path.name, "sha256":sha(raw),
                "evidence_kind":kind, "permissions":deepcopy(permissions or PERMISSIONS)}
        self.request["artifacts"].append(meta)
        return meta

    def query(self, scope, kind="component", norm=None, target=None, identifier="Q"):
        query = {"id":identifier, "revision":1, "kind":kind, "target_spec":deepcopy(target or SPEC), "scope":scope,
                 "norm":norm if norm is not None else {"state":"PV_NOT_APPLICABLE", "reasons":["No policy selection requested"], "scope":"component query"},
                 "artifact_refs":[a["id"] for a in self.request["artifacts"]], "obligation_refs":["O"]}
        self.request["queries"].append(query)
        self.request["obligations"].append(obligation(query=identifier))
        return query

    def operation(self, kind, parameters, query="Q"):
        self.request["operations"].append({"id":"OP" + str(len(self.request["operations"]) + 1), "query_ref":query,
                                           "kind":kind, "obligation_refs":["O"], "parameters":parameters})

    def assessment(self, artifact, query, source_spec=None):
        source_spec = deepcopy(source_spec or SPEC)
        if not any(a["id"] == "metadata" for a in self.request["artifacts"]):
            self.artifact("metadata", source_spec)
            query["artifact_refs"].append("metadata")
        return {"assessment_id":"A1", "revision":1, "query_ref":query["id"], "claim":query["id"],
                "intended_use":"formal synthetic conformance", "target_spec":deepcopy(query["target_spec"]),
                "source_ref":artifact["id"], "source_locator":artifact["path"], "source_version":"synthetic/1",
                "source_digest":artifact["sha256"], "observed_or_received_at":"2026-10-03", "relevant_period":source_spec["period"],
                "access_and_permissions":deepcopy(artifact["permissions"]), "evidence_kind":artifact["evidence_kind"],
                "transformation_chain":[], "axes":{axis:{"status":"MATCH", "source_value":source_spec[axis],
                    "target_value":query["target_spec"][axis], "basis":{"artifact_ref":"metadata", "pointer":"/"+axis},
                    "affected_claims":[query["id"]]} for axis in SPEC}, "conflicts":[], "verdict":"PENDING",
                "owner":{"role":"test-custodian", "task":"Review source", "assigned_person":"UNKNOWN"},
                "closure":{"verified":False, "predicate":"Five axes and permissions resolved", "witness_refs":[], "verifier":"local executor"},
                "reopen":{"condition":"Source or query change", "affected_refs":[query["id"]]}}

    def save(self):
        path = self.directory / "request.json"
        path.write_bytes(canonical(self.request))
        return path


def make_hours(directory, credits=("13/2", "15/2"), target="14/1"):
    fixture = Fixture(directory)
    source = fixture.artifact("hours", {"assignments":[{"id":"assignment-"+str(i), "credit_hours":known(value) if isinstance(value,str) else value}
                                                   for i,value in enumerate(credits)], "target_hours":known(target) if isinstance(target,str) else target})
    query = fixture.query({"operator":"CONTRACT_HOURS/1", "purpose":"FORMAL_CONDITIONAL"})
    fixture.operation("DERIVE_HOURS", {"artifact_ref":"hours", "rule_id":"CONTRACT_HOURS/1", "assessment":fixture.assessment(source,query)})
    return fixture


def make_fdq(directory, family="historical", kind="selector", certificate_mutation=None):
    fixture = Fixture(directory)
    folder = ROOT / "examples/fdq" / family
    input_raw = (folder / "input.json").read_bytes()
    result_raw = (folder / "original_result.json").read_bytes()
    certificate = json.loads((folder / "certificate.json").read_bytes())
    if certificate_mutation:
        certificate = json.loads((ROOT / "examples/fdq" / (certificate_mutation+".json")).read_bytes())
    certificate["query"] = {"frontier":kind == "frontier", "selector":kind == "selector"}
    certificate["claim"] = {kind:certificate["claim"][kind]}
    fixture.artifact("input", input_raw)
    fixture.artifact("result", result_raw)
    fixture.artifact("certificate", certificate)
    base = json.loads(input_raw)
    scope = {"profile":"FDQ_FINITE_PATCH/0.1.0", "input_sha256":sha(input_raw), "original_result_sha256":sha(result_raw),
             "domain_sha256":sha(canonical(certificate["domain"])), "target":sorted(p["id"] for p in base["policies"]),
             "horizon":"1", "scenarios":sorted(s["id"] for s in base["scenarios"]), "query_flags":certificate["query"],
             "real_domain_membership":"NOT_ESTABLISHED"}
    descriptor = {"identity":"FP1_INPUT_SHA256:"+sha(input_raw), "unit":"policy_id_set" if kind=="frontier" else "policy_id",
                  "period":"H="+base["meta"]["horizon"], "population":"DECLARED_PI:"+canonical(scope["target"]).decode(),
                  "method":"FDQ_FINITE_PATCH/0.1.0"}
    fixture.query(scope, kind, base["selection"],target=descriptor)
    fixture.request["obligations"][0]["primary_cause"] = "COMPUTO_PENDIENTE"
    fixture.operation("CERTIFY_FDQ", {"input_ref":"input", "result_ref":"result", "certificate_ref":"certificate"})
    return fixture


def add_external_query(fixture):
    query = fixture.query({"purpose":"Required external fact in independent query"}, identifier="Q2")
    row = fixture.request["obligations"][-1]
    row.update(id="O2", primary_cause="DATO_EXTERNO")
    query["obligation_refs"] = ["O2"]
    fixture.request["operations"].append({"id":"OP2", "query_ref":"Q2", "kind":"REQUEST_INPUT", "obligation_refs":["O2"],
        "parameters":{"obligation_ref":"O2", "prompt":"Provide the applicable external fact or retain unknown.", "unknown_allowed":True}})


class PublicAcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="genius-r2-consumer-")
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.case = self.work / "case"

    def run_cli(self, fixture, expected_code=0, case=None, extra=(), action="run"):
        command = [sys.executable, "-B", "-m", "genius_local", action, "--request", str(fixture.save()),
                   "--case", str(case or self.case), "--r1", str(R1), "--baseline", str(R0), *extra]
        proc = subprocess.run(command, cwd=ROOT, capture_output=True, timeout=75)
        self.assertEqual(proc.returncode, expected_code, (proc.stdout.decode(), proc.stderr.decode()))
        output = json.loads(proc.stdout if proc.returncode == 0 else proc.stderr)
        return output

    def response(self, output):
        response = output.get("response", output)
        audit_response(response, self.case)
        return response

    def test_hours_exact_and_semantic_limit(self):
        fixture = make_hours(self.work / "inputs")
        response = self.response(self.run_cli(fixture))
        decision = response["decisions"][0]
        self.assertEqual(decision["state"], "PR_JUSTIFIED_RESULT")
        values = decision["answers"][0]["value"]
        self.assertEqual({key:cell["value"] for key,cell in values.items()},
                         {"assigned":"14/1","excess":"0/1","deficit":"0/1","oriented_overtime":"0/1","oriented_undertime":"0/1"})
        rendered = json.dumps(decision)
        self.assertIn("14/1", rendered)
        self.assertIn("0/1", rendered)
        self.assertIn("h_contractual", rendered)
        self.assertNotIn("physical_rest", rendered)

    def test_unknown_credit_is_not_zero(self):
        fixture = make_hours(self.work / "inputs", credits=("13/2", unknown()))
        response = self.response(self.run_cli(fixture))
        self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertIn("PV_UNKNOWN", json.dumps(response))

    def test_unknown_target_preserves_known_assigned_hours_as_partial(self):
        fixture = make_hours(self.work/"inputs",target=unknown())
        response = self.response(self.run_cli(fixture))
        decision = response["decisions"][0]
        self.assertEqual(decision["state"],"PR_PARTIAL")
        observed = decision["observed_values"][0]["value"]
        self.assertEqual(observed["assigned"]["value"], "14/1")
        for field in ("excess","deficit","oriented_overtime","oriented_undertime"):
            self.assertEqual(observed[field]["state"],"PV_UNKNOWN")
            self.assertNotIn("value",observed[field])
        self.assertNotEqual(response["closure"]["state"],"PC_ANSWERED_SCOPED")

    def test_integer_above_javascript_safe_range_is_exact(self):
        fixture = make_hours(self.work / "inputs", credits=("9007199254740993/1", "1/3"), target="0/1")
        response = self.response(self.run_cli(fixture))
        self.assertIn("27021597764222980/3", json.dumps(response["decisions"]))

    def test_contractual_deficit_and_orientation_are_exact(self):
        fixture = make_hours(self.work/"inputs",credits=("13/2","13/2"),target="15/1")
        response = self.response(self.run_cli(fixture))
        values = response["decisions"][0]["answers"][0]["value"]
        self.assertEqual({key:cell["value"] for key,cell in values.items()},
                         {"assigned":"13/1","excess":"0/1","deficit":"2/1","oriented_overtime":"0/1","oriented_undertime":"-2/1"})

    def test_source_each_axis_mismatch_is_not_admitted(self):
        for axis in SPEC:
            with self.subTest(axis=axis):
                fixture = make_hours(self.work / axis)
                assessment = fixture.request["operations"][0]["parameters"]["assessment"]
                spec = deepcopy(SPEC)
                spec[axis] = "different-" + axis
                path = fixture.directory / "metadata.json"
                path.write_bytes(canonical(spec))
                next(a for a in fixture.request["artifacts"] if a["id"] == "metadata")["sha256"] = sha(path.read_bytes())
                assessment["axes"][axis]["source_value"] = spec[axis]
                output = self.run_cli(fixture, case=self.work / ("case-"+axis))
                response = output.get("response", output)
                self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
                self.assertIn("SC_INCOMPATIBLE", json.dumps(output))

    def test_permission_unknown_blocks_source(self):
        fixture = make_hours(self.work / "inputs")
        fixture.request["artifacts"][0]["permissions"]["use"] = "UNKNOWN"
        fixture.request["operations"][0]["parameters"]["assessment"]["access_and_permissions"]["use"] = "UNKNOWN"
        response = self.response(self.run_cli(fixture))
        self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertIn("SC_ACCESS_BLOCKED", json.dumps(response))

    def test_conflicting_sources_retained_without_averaging(self):
        fixture = make_hours(self.work / "inputs")
        other = fixture.artifact("contradiction", {"claim":"Q", "value":"99/1", "unit":"h_contractual"})
        fixture.request["queries"][0]["artifact_refs"].append(other["id"])
        assessment = fixture.request["operations"][0]["parameters"]["assessment"]
        assessment["conflicts"] = [{"source_refs":["hours", "contradiction"], "condition":"Same scoped claim has incompatible values",
                                    "scope":"Q", "consequences":"Cannot substitute either as uncontested evidence", "owner":"test-custodian",
                                    "resolution":"UNRESOLVED", "rule":"No admitted precedence rule"}]
        response = self.response(self.run_cli(fixture))
        self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertIn("SC_UNRESOLVED", json.dumps(response))
        objects = audit_chain(self.case)["objects"]
        self.assertIn(fixture.request["artifacts"][0]["sha256"], objects)
        self.assertIn(other["sha256"], objects)

    def test_unknown_axis_cannot_be_voted_away_by_four_matches(self):
        fixture = make_hours(self.work / "inputs")
        axis = fixture.request["operations"][0]["parameters"]["assessment"]["axes"]["method"]
        axis["basis"] = {"state":"NOT_ACQUIRED", "reason":"No compatible method evidence received"}
        response = self.response(self.run_cli(fixture))
        self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertIn("SC_UNRESOLVED", json.dumps(response))

    def test_fdq_selector_is_external_conditional_and_bytes_intact(self):
        fixture = make_fdq(self.work / "inputs")
        raw_input = (fixture.directory / "input.json").read_bytes()
        raw_result = (fixture.directory / "result.json").read_bytes()
        response = self.response(self.run_cli(fixture))
        self.assertEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertIn("EV_CONDITIONAL", json.dumps(response["evidence"]))
        history = audit_chain(self.case)
        self.assertEqual(history["objects"][sha(raw_input)], raw_input)
        self.assertEqual(history["objects"][sha(raw_result)], raw_result)
        self.assertIn(b"OUTSIDE_DOMAIN", raw_result)
        self.assertIn(b"RELATIVE", raw_result)

    def test_frontier_can_answer_without_manufacturing_selector(self):
        for family in ("none", "unique"):
            with self.subTest(family=family):
                fixture = make_fdq(self.work/family, family=family,kind="frontier")
                response = self.run_cli(fixture,case=self.work/("case-"+family))
                self.assertEqual(response["decisions"][0]["state"], "PR_SET_OR_INCOMPARABLE")
                decision_text = json.dumps(response["decisions"][0])
                self.assertIn('"p"',decision_text)
                self.assertIn('"s"',decision_text)
                self.assertNotIn('"state": "DEFINED"',decision_text)

    def test_none_and_unique_selector_absence_is_answered_without_fabricated_winner(self):
        for family,cause in (("none","SELECTION_DISABLED"),("unique","SELECTION_NOT_UNIQUE")):
            with self.subTest(family=family):
                fixture = make_fdq(self.work/family,family=family,kind="selector")
                response = self.run_cli(fixture,case=self.work/("case-"+family))
                decision=response["decisions"][0]
                self.assertEqual(decision["state"],"PR_JUSTIFIED_RESULT")
                selector=decision["answers"][0]["value"]["value"]["selector"]
                self.assertEqual(selector,{"state":"OUTSIDE_DOMAIN","cause":cause})

    def test_infeasibility_requires_all_policy_resource_refutations(self):
        fixture = make_fdq(self.work/"inputs",family="infeasible",kind="frontier")
        response = self.response(self.run_cli(fixture))
        self.assertEqual(response["decisions"][0]["state"], "PR_PROVEN_INFEASIBLE")
        self.assertIn("EV_CONDITIONAL",json.dumps(response["evidence"]))
        self.assertEqual(fixture.request["queries"][0]["scope"]["target"],["p","q","s"])

    def test_invalid_fdq_certificates_do_not_become_decisions(self):
        for case, family in (("empty_family","historical"), ("omitted_feasible_policy","priority"),
                             ("false_claim","historical"), ("missing_hole_index","historical"),
                             ("missing_constraint","historical"), ("order_breaking_calibration","historical")):
            with self.subTest(case=case):
                fixture = make_fdq(self.work / case, family, certificate_mutation=case)
                output = self.run_cli(fixture, case=self.work / ("case-"+case))
                response = output.get("response", output)
                self.assertNotIn(response["decisions"][0]["state"], {"PR_JUSTIFIED_RESULT","PR_PROVEN_INFEASIBLE"})

    def test_changed_query_scope_cannot_borrow_fdq_certificate(self):
        fixture = make_fdq(self.work / "inputs")
        fixture.request["queries"][0]["scope"]["target"] = ["p"]
        response = self.response(self.run_cli(fixture))
        self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")

    def test_formal_fdq_cannot_be_relabelled_as_empirical_population(self):
        fixture=make_fdq(self.work/"inputs")
        fixture.request["queries"][0]["target_spec"]["population"]="actual living plants in Mendoza"
        response=self.response(self.run_cli(fixture))
        self.assertNotEqual(response["decisions"][0]["state"],"PR_JUSTIFIED_RESULT")
        self.assertIn("FDQ_TARGET_SPEC_BINDING",json.dumps(response))

    def test_budget_zero_is_not_infeasibility(self):
        fixture = make_hours(self.work / "inputs")
        fixture.request["budget"]["max_operations"] = 0
        response = self.response(self.run_cli(fixture))
        self.assertEqual(response["execution"]["state"], "PE_BUDGET_EXHAUSTED")
        self.assertEqual(response["closure"]["state"], "PC_BUDGET_EXHAUSTED")
        self.assertNotEqual(response["decisions"][0]["state"], "PR_PROVEN_INFEASIBLE")

    def test_exhaustion_preserves_completed_independent_query(self):
        fixture = make_hours(self.work / "inputs")
        add_external_query(fixture)
        fixture.request["budget"]["max_operations"] = 1
        response = self.response(self.run_cli(fixture))
        self.assertEqual(response["execution"]["state"], "PE_BUDGET_EXHAUSTED")
        self.assertEqual(response["closure"]["state"], "PC_BUDGET_EXHAUSTED")
        by_query = {decision["query_ref"]:decision for decision in response["decisions"]}
        self.assertEqual(by_query["Q"]["state"], "PR_JUSTIFIED_RESULT")
        self.assertEqual(by_query["Q"]["answers"][0]["value"]["assigned"]["value"], "14/1")
        self.assertNotIn(by_query["Q2"]["state"], {"PR_JUSTIFIED_RESULT", "PR_PROVEN_INFEASIBLE"})

    def test_cancellation_before_work_is_not_infeasibility(self):
        fixture = make_hours(self.work / "inputs")
        cancel_file = self.work / "cancel"
        cancel_file.write_text("cooperative cancellation requested")
        response = self.response(self.run_cli(fixture, extra=("--cancel-file",str(cancel_file))))
        self.assertEqual(response["closure"]["state"], "PC_CANCELLED")
        self.assertNotEqual(response["decisions"][0]["state"], "PR_PROVEN_INFEASIBLE")

    def test_restart_reads_same_history_and_detects_corruption(self):
        fixture = make_hours(self.work / "inputs")
        response = self.response(self.run_cli(fixture))
        before = audit_chain(self.case)
        proc = subprocess.run([sys.executable,"-B","-m","genius_local","inspect","--case",str(self.case)],
                              cwd=ROOT,capture_output=True,timeout=10)
        self.assertEqual(proc.returncode, 0, proc.stderr.decode())
        self.assertIn(before["chain"][-1]["sha256"], proc.stdout.decode())
        self.assertEqual(before["chain"],audit_chain(self.case)["chain"])
        source_digest = fixture.request["artifacts"][0]["sha256"]
        (self.case/"objects"/source_digest).write_bytes(b"accidental-corruption")
        with self.assertRaises(ConsumerRejected):
            audit_chain(self.case)
        proc = subprocess.run([sys.executable,"-B","-m","genius_local","verify","--case",str(self.case)],
                              cwd=ROOT,capture_output=True,timeout=10)
        self.assertNotEqual(proc.returncode,0)

    def test_continue_rejects_no_novelty_then_accepts_pertinent_new_input(self):
        fixture = make_hours(self.work / "inputs", credits=("13/2", unknown()))
        first = self.response(self.run_cli(fixture))
        old = audit_chain(self.case)
        head = old["chain"][-1]
        fixture.request.update(revision=2, supersedes={"revision":head["revision"],"sha256":head["sha256"]})
        fixture.request["novelty"] = {"reason":"Only a new turn, without new evidence", "changed_refs":[]}
        rejected = self.run_cli(fixture,expected_code=2,action="continue")
        self.assertNotIn("PR_JUSTIFIED_RESULT",json.dumps(rejected))
        after_rejection = audit_chain(self.case)
        # Attempts may be logged; no old object or committed revision may change.
        for obj, raw in old["objects"].items():
            self.assertEqual(after_rejection["objects"][obj],raw)
        head = after_rejection["chain"][-1]
        fixture.request["supersedes"] = {"revision":head["revision"],"sha256":head["sha256"]}
        hours_path = fixture.directory/"hours.json"
        hours = json.loads(hours_path.read_bytes())
        hours["assignments"][1]["credit_hours"] = known("15/2")
        hours_path.write_bytes(canonical(hours))
        new_sha = sha(hours_path.read_bytes())
        fixture.request["artifacts"][0]["sha256"] = new_sha
        fixture.request["operations"][0]["parameters"]["assessment"]["source_digest"] = new_sha
        fixture.request["novelty"] = {"reason":"Previously absent credit now supplied as explicit synthetic value", "changed_refs":["hours"]}
        response = self.response(self.run_cli(fixture,action="continue"))
        self.assertEqual(response["decisions"][0]["state"],"PR_JUSTIFIED_RESULT")
        self.assertIn("14/1",json.dumps(response["decisions"]))
        current = audit_chain(self.case)
        for obj, raw in old["objects"].items():
            self.assertEqual(current["objects"][obj],raw)

    def test_all_nine_causes_remain_distinct_dependencies(self):
        fixture = Fixture(self.work / "inputs")
        for index, cause in enumerate(CAUSES):
            identifier = "Q" + str(index)
            query = fixture.query({"purpose":"dependency-only"}, identifier=identifier)
            row = fixture.request["obligations"][-1]
            row.update(id="O" + str(index), primary_cause=cause)
            query["obligation_refs"] = [row["id"]]
        response = self.response(self.run_cli(fixture))
        self.assertTrue(all(d["state"] == "PR_DEPENDENCY" for d in response["decisions"]))
        history = json.dumps(audit_chain(self.case)["snapshots"])
        for cause in CAUSES:
            self.assertIn(cause, history)

    def test_d1_reuse_preserves_partial_and_original_bytes(self):
        fixture = Fixture(self.work / "inputs")
        partial_raw = b'{ "D1": {"state":"PV_UNKNOWN","reasons":["controlled omission"],"obligation_refs":["O"]} }\n'
        original_raw = b'{ "D1": {"state":"PV_KNOWN","value":"13/2","unit":"h_contractual","basis":["synthetic original"]} }\n'
        fixture.artifact("partial", partial_raw)
        source = fixture.artifact("original", original_raw)
        query = fixture.query({"operator":"REUSE/1", "artifact_ref":"original", "pointer":"/D1"})
        fixture.request["obligations"][0]["primary_cause"] = "YA_DISPONIBLE"
        fixture.operation("REUSE", {"artifact_ref":"original", "pointer":"/D1", "assessment":fixture.assessment(source,query)})
        response = self.response(self.run_cli(fixture))
        self.assertEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")
        self.assertIn("13/2", json.dumps(response["decisions"]))
        objects = audit_chain(self.case)["objects"]
        self.assertEqual(objects[sha(partial_raw)], partial_raw)
        self.assertEqual(objects[sha(original_raw)], original_raw)

    def test_d4_h13_h14_only_in_received_scope(self):
        for field in ("D4", "H13", "H14"):
            with self.subTest(field=field):
                fixture = Fixture(self.work / field)
                fixture.artifact("diagnosis", (R0 / "analysis/DOMAIN_EVIDENCE.md").read_bytes(), "RECEIVED_DERIVATION")
                fixture.query({"operator":"B01_RECEIVED_CLASSIFICATION/1", "field":field, "purpose":"RECEIVED_DIAGNOSIS_ONLY"})
                fixture.request["obligations"][0]["primary_cause"] = "IRRELEVANTE_DEMOSTRADO"
                fixture.operation("PROVE_IRRELEVANCE", {"artifact_ref":"diagnosis", "rule_id":"B01_RECEIVED_CLASSIFICATION/1", "field":field})
                output = self.run_cli(fixture, case=self.work / ("case-"+field))
                response = output.get("response",output)
                self.assertIn(response["decisions"][0]["state"], {"PR_JUSTIFIED_RESULT","PR_PARTIAL"})
                self.assertIn("RECEIVED_DIAGNOSIS_ONLY", json.dumps(response))
                fixture.request["queries"][0]["scope"]["purpose"] = "ALL_FUTURE_HOSPITAL_QUERIES"
                altered = self.run_cli(fixture, case=self.work / ("case-bad-"+field))
                response = altered.get("response", altered)
                self.assertNotEqual(response["decisions"][0]["state"], "PR_JUSTIFIED_RESULT")

    def test_external_facts_and_preference_remain_local_dependencies(self):
        for name, cause in (("consent","DATO_EXTERNO"), ("history","DATO_EXTERNO"),
                            ("identity","DATO_EXTERNO"), ("irrecoverable","DATO_EXTERNO"), ("preference","PREFERENCIA")):
            with self.subTest(name=name):
                fixture = Fixture(self.work / name)
                fixture.query({"purpose":"Missing "+name})
                fixture.request["obligations"][0]["primary_cause"] = cause
                fixture.operation("REQUEST_INPUT", {"obligation_ref":"O", "prompt":"Supply compatible "+name+" if known; otherwise retain unknown.", "unknown_allowed":True})
                response = self.run_cli(fixture, case=self.work / ("case-"+name))
                self.assertEqual(response["decisions"][0]["state"], "PR_DEPENDENCY")
                self.assertNotEqual(response["closure"]["state"], "PC_ANSWERED_SCOPED")

    def test_cag_origin_task_model_pending_not_invented_by_expansion(self):
        fixture = Fixture(self.work / "inputs")
        fixture.query({"purpose":"CAG origin and task pending model"})
        row = fixture.request["obligations"][0]
        row["primary_cause"] = "DEFINICION_MODELO"
        row["affected_claims"] = ["CAG", "origin-catalogue", "task"]
        fixture.operation("EXPAND_MODEL", {"reason":"Missing admitted identity, origin and task meaning", "affected_dependencies":["O"]})
        response = self.response(self.run_cli(fixture))
        self.assertEqual(response["decisions"][0]["state"], "PR_DEPENDENCY")
        self.assertNotEqual(response["closure"]["state"], "PC_ANSWERED_SCOPED")

    def test_arbitrary_empirical_predicate_cannot_be_closed_by_hours(self):
        fixture = make_hours(self.work/"inputs")
        fixture.request["obligations"][0]["closure"]["predicate"] = "Human utility and consent empirically proven"
        response = self.response(self.run_cli(fixture))
        row = response["obligations_ref"]["record"]["obligations"][0]
        self.assertFalse(row["closure"]["verified"])
        self.assertFalse(row["status"].startswith("CLOSED_"))
        self.assertNotEqual(response["closure"]["state"], "PC_ANSWERED_SCOPED")

    def test_open_model_dependency_prevents_descendant_closure(self):
        fixture = make_hours(self.work/"inputs")
        fixture.request["obligations"].append(obligation("DEFINICION_MODELO",identifier="M"))
        fixture.request["queries"][0]["obligation_refs"].append("M")
        fixture.request["obligations"][0]["dependencies"] = [{"ref":"M","revision":1,"role":"rule"}]
        response = self.response(self.run_cli(fixture))
        rows = {row["id"]:row for row in response["obligations_ref"]["record"]["obligations"]}
        self.assertFalse(rows["O"]["closure"]["verified"])
        self.assertFalse(rows["M"]["closure"]["verified"])
        self.assertNotEqual(response["closure"]["state"], "PC_ANSWERED_SCOPED")

    def test_reuse_received_result_precedes_recalculation_and_invalidates_on_new_bytes(self):
        fixture = make_hours(self.work/"inputs")
        self.response(self.run_cli(fixture))
        initial = audit_chain(self.case)
        head = initial["chain"][-1]
        fixture.request.update(revision=2,supersedes={"revision":head["revision"],"sha256":head["sha256"]})
        add_external_query(fixture)
        fixture.request["novelty"] = {"reason":"New independent external query", "changed_refs":["Q2"]}
        second = self.response(self.run_cli(fixture,action="continue"))
        evidence = next(row for row in second["evidence"] if row["query_ref"] == "Q")
        reuse = [row for row in evidence["records"] if row.get("type") == "LOCAL_RECEIPT_REUSE"]
        self.assertEqual(len(reuse),1)
        self.assertIs(reuse[0]["new_computation"],False)
        self.assertIn(reuse[0]["source_revision"], {row["sha256"] for row in initial["chain"]})
        latest = audit_chain(self.case)["chain"][-1]
        fixture.request.update(revision=3,supersedes={"revision":latest["revision"],"sha256":latest["sha256"]})
        path = fixture.directory/"hours.json"
        hours = json.loads(path.read_bytes()); hours["assignments"][1]["credit_hours"] = known("17/2")
        path.write_bytes(canonical(hours)); new_sha=sha(path.read_bytes())
        fixture.request["artifacts"][0]["sha256"] = new_sha
        fixture.request["operations"][0]["parameters"]["assessment"]["source_digest"] = new_sha
        fixture.request["novelty"] = {"reason":"Changed credit invalidates old answer", "changed_refs":["hours"]}
        third = self.response(self.run_cli(fixture,action="continue"))
        evidence = next(row for row in third["evidence"] if row["query_ref"] == "Q")
        self.assertFalse(any(row.get("type") == "LOCAL_RECEIPT_REUSE" for row in evidence["records"]))
        decision = next(row for row in third["decisions"] if row["query_ref"] == "Q")
        self.assertEqual(decision["answers"][0]["value"]["assigned"]["value"], "15/1")

    def test_unknown_version_and_forged_caller_closure_are_rejected(self):
        for name in ("version", "closure", "extra_members"):
            with self.subTest(name=name):
                fixture = make_hours(self.work / name)
                if name == "version":
                    fixture.request["format"] = "genius-local-request/9.9.9"
                elif name == "closure":
                    fixture.request["obligations"][0]["closure"]["verified"] = True
                else:
                    fixture.request["operations"][0]["parameters"]["members_ref"] = "unadmitted-extension"
                output = self.run_cli(fixture, expected_code=2, case=self.work / ("case-"+name))
                self.assertNotIn("PR_JUSTIFIED_RESULT", json.dumps(output))

    def test_client_detects_overclaim_and_unknown_zero(self):
        fixture = make_hours(self.work / "inputs")
        response = self.response(self.run_cli(fixture))
        mutations = []
        bad = deepcopy(response); bad["quality"]["score"] = "1/1"; mutations.append(bad)
        bad = deepcopy(response); bad["decisions"][0]["state"] = "PR_PROVEN_INFEASIBLE"; mutations.append(bad)
        bad = deepcopy(response); bad["decisions"][0]["query_ref"] = "nonexistent-query"; mutations.append(bad)
        bad = deepcopy(response); bad["decisions"][0]["value"] = {**unknown(), "value":"0/1"}; mutations.append(bad)
        bad = deepcopy(response); bad["format"] = "genius-product-response/9.9.9"; mutations.append(bad)
        for bad in mutations:
            with self.assertRaises(ConsumerRejected):
                audit_response(bad, self.case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
