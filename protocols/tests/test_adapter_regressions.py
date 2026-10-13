"""Author regression checks, complementary to the independent consumer/audit."""
import io
import unittest
from unittest.mock import patch

from genius_protocols import wire
from genius_protocols.server import Session, serve


def request(method, params, request_id=1):
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}


def initialized():
    session = Session()
    session.handle_request(request("genius.initialize", {
        "protocol_versions": ["genius-protocols/1.0"], "required_capabilities": []}))
    return session


class AdapterRegressions(unittest.TestCase):
    def test_candidate_syntax_precedes_number_type_without_verifier(self):
        session = initialized()
        candidates = [(b'{"a":1,"a":2}', "CANDIDATE_SYNTAX"),
                      (b'{"a":1,', "CANDIDATE_SYNTAX"),
                      (b'{"a":1,"s":"\\ud800"}', "CANDIDATE_SYNTAX"),
                      (b'{"a":1}', "CANDIDATE_TYPE"),
                      (b'1' + b'0' * 100000, "CANDIDATE_TYPE")]
        with patch("genius_protocols.server.genius_kernel.verify_result") as verify:
            for candidate, expected in candidates:
                with self.subTest(candidate=candidate[:40]):
                    result = session.handle_request(request("genius.verify_result", {
                        "input": wire.byte_envelope(b'{}'),
                        "candidate": wire.byte_envelope(candidate)}))["result"]
                    self.assertEqual(result["report"], {
                        "valid": False, "status": "INVALID", "errors": [expected]})
            verify.assert_not_called()

    def test_input_is_passed_as_exact_bytes_with_no_hidden_limits(self):
        session = initialized()
        raw = b'\xff\x00not JSON\r\n'
        with patch("genius_protocols.server.genius_kernel.evaluate", return_value={}) as evaluate:
            reply = session.handle_request(request("genius.evaluate", {"input": wire.byte_envelope(raw)}))
            evaluate.assert_called_once_with(raw, limits={})
            self.assertEqual(reply["result"]["input"], wire.byte_envelope(raw))

    def test_no_execution_on_notifications_or_incomplete_eof(self):
        notification = {"jsonrpc": "2.0", "method": "genius.evaluate", "params": {}}
        with patch("genius_protocols.server.genius_kernel.evaluate") as evaluate:
            self.assertIsNone(initialized().handle_request(notification))
            sink = io.BytesIO()
            payload = wire.json_bytes(request("genius.evaluate", {}))
            self.assertEqual(serve(io.BytesIO(payload), sink), 2)
            self.assertEqual(sink.getvalue(), b"")
            evaluate.assert_not_called()

    def test_response_cap_replaces_whole_result_and_batch(self):
        session = initialized()
        with patch("genius_protocols.server.genius_kernel.evaluate", return_value={"large": "x" * 150}):
            req = request("genius.evaluate", {"input": wire.byte_envelope(b"{}")}, "a")
            with patch.object(wire, "MAX_RESPONSE_BYTES", 100):
                result = session.handle_request(req)
                self.assertEqual(result["error"]["code"], -32003)
                self.assertNotIn("result", result)
            with patch.object(wire, "MAX_RESPONSE_BYTES", 600):
                batch = session.handle_payload(wire.json_bytes([req, {**req, "id": "b"}]))
                self.assertEqual([r["id"] for r in batch], ["a", "b"])
                self.assertEqual([r["error"]["code"] for r in batch], [-32003, -32003])


if __name__ == "__main__":
    unittest.main()

