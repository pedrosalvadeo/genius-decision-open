"""Independent consumer oracle; does not import any genius_views transformation.

Actual R2 invocations use its published CLI and stipulated hours inputs. Tests
named presentation_fixture modify a received response only to exercise the
renderer: they do not constitute a new formal result or empirical evidence.
The HTML oracle is specified in SEMANTIC_CONTRACT before implementation.
"""
from __future__ import annotations

import copy
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import unquote, urlsplit


ROOT = Path(__file__).resolve().parents[1]
R2 = ROOT.parent / "product_local"
EXAMPLES = R2 / "examples" / "hours"


def canonical(obj):
    return json.dumps(obj, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AssertionError("duplicate JSON key: " + key)
            result[key] = value
        return result
    def forbidden(value):
        raise AssertionError("float/nonfinite number in exact consumer: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_float=forbidden,
                      parse_constant=forbidden)


def leaves(value, pointer=""):
    if isinstance(value, dict) and value:
        for key in sorted(value):
            escaped = key.replace("~", "~0").replace("/", "~1")
            yield from leaves(value[key], pointer + "/" + escaped)
    elif isinstance(value, list) and value:
        for index, child in enumerate(value):
            yield from leaves(child, pointer + "/" + str(index))
    else:
        # Canonical encoding distinguishes false/0 and preserves empty types.
        yield pointer, canonical(value)


class VisibleOracle(HTMLParser):
    """Read visible table cells without importing a renderer/parser helper."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.pointer = None
        self.in_value = False
        self.chunks = []
        self.rows = {}
        self.links = []
        self.text = []
        self.csp = None

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag in {"script", "iframe", "object", "embed", "form", "base"}:
            raise AssertionError("active element: " + tag)
        if any(name.lower().startswith("on") for name in attributes):
            raise AssertionError("event handler in HTML")
        if "src" in attributes:
            raise AssertionError("resource acquisition in local HTML")
        if tag == "meta" and attributes.get("http-equiv", "").lower() == "content-security-policy":
            self.csp = attributes.get("content")
        if "href" in attributes:
            self.links.append(attributes["href"])
        if tag == "tr" and "data-pointer" in attributes:
            if self.pointer is not None:
                raise AssertionError("nested pointer row")
            self.pointer = attributes["data-pointer"]
        if tag == "td" and "json-value" in attributes.get("class", "").split():
            if self.pointer is None:
                raise AssertionError("JSON value without pointer")
            self.in_value = True
            self.chunks = []

    def handle_data(self, value):
        self.text.append(value)
        if self.in_value:
            self.chunks.append(value)

    def handle_endtag(self, tag):
        if tag == "td" and self.in_value:
            if self.pointer in self.rows:
                raise AssertionError("duplicate visible pointer: " + self.pointer)
            self.rows[self.pointer] = canonical(strict("".join(self.chunks)))
            self.in_value = False
        if tag == "tr":
            self.pointer = None


def tree_identity(directory):
    return {str(path.relative_to(directory)): digest(path.read_bytes())
            for path in directory.rglob("*") if path.is_file()}


def stored_payload(case):
    head = strict((case / "HEAD").read_bytes())["sha256"]
    revision = strict((case / "revisions" / head).read_bytes())
    assert digest((case / "revisions" / head).read_bytes()) == head
    return head, revision


def read_manifest(case, manifest):
    pieces = []
    for ref in manifest["chunks"]:
        raw = (case / "objects" / ref["sha256"]).read_bytes()
        assert digest(raw) == ref["sha256"] and len(raw) == ref["size"]
        pieces.append(raw)
    raw = b"".join(pieces)
    assert len(raw) == manifest["size"] and digest(raw) == manifest["sha256"]
    return strict(raw)


def store_object(case, value):
    raw = canonical(value)
    sha = digest(raw)
    (case / "objects" / sha).write_bytes(raw)
    return {"sha256": sha, "size": len(raw),
            "chunks": [{"sha256": sha, "size": len(raw), "path": "objects/" + sha}]}


def append_presentation_fixture(case, mutate):
    """Write explicit synthetic journal revision; never called an R2 execution."""
    head, revision = stored_payload(case)
    payload = copy.deepcopy(revision["payload"])
    response = read_manifest(case, payload["response_ref"])
    mutate(response, payload)
    if "response_ref" in payload:
        payload["response_ref"] = store_object(case, response)
    record = {"format": "genius-local-revision/0.1.0",
              "revision": revision["revision"] + 1, "parent": head,
              "objects": sorted(path.name for path in (case / "objects").iterdir()),
              "payload": payload}
    raw = canonical(record)
    sha = digest(raw)
    (case / "revisions" / sha).write_bytes(raw)
    (case / "HEAD").write_bytes(canonical({"format": "genius-local-head/0.1.0", "sha256": sha}))
    return response


class IndependentConsumerClient(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="genius-r3-independent-")
        self.addCleanup(self.tmp.cleanup)
        self.work = Path(self.tmp.name)
        self.env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1",
                        PYTHONPATH=os.pathsep.join((str(ROOT), str(R2))))
        self.sequence = 0

    def command(self, module, args):
        return subprocess.run([sys.executable, "-B", "-m", module, *map(str, args)],
                              cwd=ROOT, env=self.env, capture_output=True, timeout=65)

    def make_case(self, edit=None, cancel=False):
        self.sequence += 1
        inputs = self.work / ("inputs-" + str(self.sequence))
        shutil.copytree(EXAMPLES, inputs)
        request = strict((inputs / "request.json").read_bytes())
        hours = strict((inputs / "hours.json").read_bytes())
        if edit:
            edit(request, hours)
        (inputs / "hours.json").write_bytes(canonical(hours))
        for artifact in request["artifacts"]:
            artifact["sha256"] = digest((inputs / artifact["path"]).read_bytes())
        for operation in request["operations"]:
            assessment = operation.get("parameters", {}).get("assessment")
            if assessment and assessment["source_ref"] == "hours":
                assessment["source_digest"] = digest((inputs / "hours.json").read_bytes())
        (inputs / "request.json").write_bytes(canonical(request))
        case = self.work / ("case-" + str(self.sequence))
        args = ["run", "--request", inputs / "request.json", "--case", case,
                "--baseline", self.work, "--r1", self.work]
        if cancel:
            cancellation = self.work / "cancel"
            cancellation.write_text("test cancellation only")
            args += ["--cancel-file", cancellation]
        result = self.command("genius_local", args)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        response = strict(result.stdout)
        _, revision = stored_payload(case)
        self.assertEqual(read_manifest(case, revision["payload"]["response_ref"]), response)
        return case, response

    def export(self, case, expected, revision=None):
        self.sequence += 1
        output = self.work / ("export-" + str(self.sequence))
        before = tree_identity(case)
        args = ["render", "--case-dir", case, "--output-dir", output]
        if revision is not None:
            args += ["--revision", revision]
        result = self.command("genius_views", args)
        self.assertEqual(result.returncode, 0, (result.stdout.decode(), result.stderr.decode()))
        self.assertEqual(tree_identity(case), before, "renderer changed source dossier")
        source = strict((output / "source.json").read_bytes())
        app = strict((output / "app.json").read_bytes())
        agent = strict((output / "agent.json").read_bytes())
        for target, fmt in ((app, "application"), (agent, "agent")):
            self.assertEqual(target["format"], "genius-consumer-" + fmt + "/0.1.0")
            self.assertEqual(canonical(target["response"]), canonical(expected))
            self.assertEqual(target["response_sha256"], digest(canonical(expected)) if expected is not None else None)
            self.assertEqual(target["source_sha256"], digest(canonical(source)))
            self.assertIn("publication_state", target)
            self.assertIsInstance(target["presentation"], dict)
        oracle = VisibleOracle()
        oracle.feed((output / "human.html").read_text(encoding="utf-8"))
        oracle.close()
        self.assertEqual(oracle.rows, dict(leaves(expected if expected is not None else source)))
        self.assertIsNotNone(oracle.csp)
        self.assertIn("default-src 'none'", oracle.csp)
        for href in oracle.links:
            if href.startswith("#"):
                continue
            parsed = urlsplit(href)
            self.assertFalse(parsed.scheme or parsed.netloc or parsed.query, href)
            path = Path(unquote(parsed.path))
            self.assertFalse(path.is_absolute() or ".." in path.parts, href)
            resolved = (output / path).resolve()
            self.assertTrue(resolved.is_relative_to(output.resolve()), href)
            self.assertTrue(resolved.is_file(), href)
        if expected is not None:
            visible = " ".join(oracle.text).lower()
            for word in ("transporte", "ejecución", "evidencia", "decisión", "calidad"):
                self.assertIn(word, visible)
            for field in ("transport", "execution", "evidence", "decisions", "quality",
                          "obligations_ref", "closure", "permitted_use"):
                self.assertTrue(any(pointer.startswith("/" + field) for pointer in oracle.rows))
        return output, app, agent, source, oracle

    def reject(self, case, revision=None):
        self.sequence += 1
        output = self.work / ("rejected-" + str(self.sequence))
        args = ["render", "--case-dir", case, "--output-dir", output]
        if revision is not None:
            args += ["--revision", revision]
        result = self.command("genius_views", args)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists(), "failed export was promoted")
        return result

    def test_new_execution_exact_large_fraction_and_three_views(self):
        def edit(request, hours):
            hours["assignments"][0]["credit_hours"]["value"] = "9007199254740993/1"
            hours["assignments"][1]["credit_hours"]["value"] = "1/3"
            hours["target_hours"]["value"] = "0/1"
        case, response = self.make_case(edit)
        self.assertIn("27021597764222980/3", json.dumps(response))
        self.export(case, response)

    def test_new_execution_unknown_is_preserved_not_zero(self):
        def edit(request, hours):
            hours["target_hours"] = {"state": "PV_UNKNOWN", "reasons": ["No target supplied"], "obligation_refs": ["O"]}
        case, response = self.make_case(edit)
        self.assertEqual(response["decisions"][0]["state"], "PR_PARTIAL")
        _, app, _, _, _ = self.export(case, response)
        values = app["response"]["decisions"][0]["observed_values"][0]["value"]
        self.assertEqual(values["assigned"]["value"], "14/1")
        self.assertEqual(values["deficit"]["state"], "PV_UNKNOWN")
        self.assertNotIn("value", values["deficit"])

    def test_new_execution_budget_and_cancel_are_not_infeasible(self):
        for state in ("PE_BUDGET_EXHAUSTED", "PE_CANCELLED"):
            with self.subTest(state=state):
                edit = (lambda request, hours: request["budget"].update(max_operations=0)) if "BUDGET" in state else None
                case, response = self.make_case(edit, cancel=state == "PE_CANCELLED")
                self.assertEqual(response["execution"]["state"], state)
                self.assertNotEqual(response["decisions"][0]["state"], "PR_PROVEN_INFEASIBLE")
                self.export(case, response)

    def test_new_execution_pending_external_model_preference(self):
        for cause in ("DATO_EXTERNO", "DEFINICION_MODELO", "PREFERENCIA"):
            with self.subTest(cause=cause):
                def edit(request, hours):
                    request["obligations"][0]["primary_cause"] = cause
                    request["operations"] = [{"id": "PENDING", "kind": "REQUEST_INPUT", "query_ref": "Q", "obligation_refs": ["O"],
                                              "parameters": {"obligation_ref": "O", "prompt": "Indique el dato o conserve desconocido", "unknown_allowed": True}}]
                case, response = self.make_case(edit)
                self.assertEqual(response["decisions"][0]["state"], "PR_DEPENDENCY")
                self.export(case, response)

    def test_new_execution_untrusted_prose_is_only_visible_text(self):
        attack = '</td><script>alert(1)</script><a href="https://evil.invalid/">Go</a> \u202e / ~'
        def edit(request, hours):
            request["obligations"][0]["next_action"] = attack
            request["obligations"][0]["owner"]["task"] = attack
        case, response = self.make_case(edit)
        _, _, _, _, oracle = self.export(case, response)
        self.assertIn(canonical(attack), oracle.rows.values())

    def test_deterministic_export_and_existing_output_not_overwritten(self):
        case, response = self.make_case()
        one, *_ = self.export(case, response)
        two, *_ = self.export(case, response)
        self.assertEqual(tree_identity(one), tree_identity(two))
        before = tree_identity(one)
        result = self.command("genius_views", ["render", "--case-dir", case, "--output-dir", one])
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(tree_identity(one), before)

    def test_corrupt_absent_and_symlink_artifact_rejected(self):
        for mode in ("corrupt", "absent", "symlink"):
            with self.subTest(mode=mode):
                case, _ = self.make_case()
                _, revision = stored_payload(case)
                path = case / "objects" / revision["payload"]["response_ref"]["chunks"][0]["sha256"]
                original = path.read_bytes()
                if mode == "corrupt":
                    path.write_bytes(original + b" ")
                else:
                    path.unlink()
                    if mode == "symlink":
                        external = self.work / ("external-" + str(self.sequence))
                        external.write_bytes(original)
                        path.symlink_to(external)
                self.reject(case)

    def test_historical_unpublished_revision_is_not_fabricated(self):
        case, _ = self.make_case()
        _, app, _, _, _ = self.export(case, None, revision=1)
        self.assertIsNone(app["response"])
        self.reject(case, revision=999)

    def test_unknown_contract_version_rejected_presentation_fixture(self):
        case, _ = self.make_case()
        def mutate(response, payload):
            response["format"] = "genius-product-response/9.0.0"
        append_presentation_fixture(case, mutate)
        self.reject(case)

    def test_prior_answer_kept_when_execution_unknown_or_error_presentation_fixture(self):
        for state in ("PE_UNKNOWN", "PE_ERROR"):
            with self.subTest(state=state):
                case, original = self.make_case()
                inspected = self.command("genius_local", ["inspect", "--case", case])
                self.assertEqual(inspected.returncode, 0, inspected.stderr.decode())
                snapshot = strict(inspected.stdout)["latest"]
                snapshot["execution"] = {"state": state, "reason": "SYNTHETIC_PRESENTATION_FIXTURE", "progress": {}}
                snapshot["closure_reason"] = "SYNTHETIC_PRESENTATION_FIXTURE"
                # R2 builds the coherent fixture. The consumer transformation
                # and its helpers are never imported by this independent client.
                fixture_builder = (
                    "import json,sys; from genius_local.controller import _response; "
                    "s=json.load(sys.stdin); print(json.dumps(_response(s,s['response']['request_ref']),ensure_ascii=False))"
                )
                rebuilt = subprocess.run([sys.executable, "-B", "-c", fixture_builder],
                                         input=canonical(snapshot), capture_output=True,
                                         env=self.env, cwd=ROOT, timeout=10)
                self.assertEqual(rebuilt.returncode, 0, rebuilt.stderr.decode())
                coherent_response = strict(rebuilt.stdout)
                def mutate(response, payload):
                    response.clear()
                    response.update(coherent_response)
                    payload["execution"] = snapshot["execution"]
                    payload["closure_reason"] = snapshot["closure_reason"]
                expected = append_presentation_fixture(case, mutate)
                _, app, _, _, _ = self.export(case, expected)
                self.assertEqual(app["response"]["decisions"], original["decisions"])

    def test_forged_response_layer_states_rejected_presentation_fixture(self):
        # Display must reject changed conclusions unsupported by retained outcomes.
        states = ("PR_JUSTIFIED_RESULT", "PR_SET_OR_INCOMPARABLE", "PR_PROVEN_INFEASIBLE",
                  "PR_PARTIAL", "PR_DEPENDENCY", "PR_OUTSIDE_PROFILE", "PR_NOT_EVALUATED")
        for state in states:
            with self.subTest(state=state):
                case, _ = self.make_case()
                def mutate(response, payload):
                    decision = response["decisions"][0]
                    decision["state"] = state
                    decision["reason"] = "SYNTHETIC_PRESENTATION_FIXTURE"
                    if state == "PR_PROVEN_INFEASIBLE":
                        decision["coverage"] = "EXHAUSTIVE"
                        decision["witnesses"] = [{"fixture": "formal display only; no new certificate"}]
                append_presentation_fixture(case, mutate)
                self.reject(case)

    def test_global_quality_score_not_admitted_presentation_fixture(self):
        case, _ = self.make_case()
        def mutate(response, payload):
            response["quality"]["score"] = "1/1"
        append_presentation_fixture(case, mutate)
        self.reject(case)


if __name__ == "__main__":
    unittest.main(verbosity=2)
