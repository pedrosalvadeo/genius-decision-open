"""Static documentation contract; never executes commands from the guides."""
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(sys.argv.pop(1)).resolve()
BASELINE = json.loads(Path(__file__).with_name('baseline-contract.json').read_text())
CLIENTS = ('claude-code', 'cursor', 'codex', 'gemini-cli', 'rho')
EXPECTED = '''### Recall notes

`possible fix:` is the next different command that passed after the failure;
`confirmed fix:` means the failing command passed after that candidate in at least two episodes.
The note names who last ran the candidate (an agent or a terminal), so evidence
can cross agents sharing the same local store.
This is observed history, not proof of cause; check whether it applies here.
Set `MEMORYWHALE_HOOK_FEEDBACK=0` in the hook's environment to silence notes, not capture.
See the [0.20.0 release notes](../../docs/releases/0.20.0.md).'''


def read(client):
    return (ROOT / 'integrations' / client / 'README.md').read_text()


def section(text, heading):
    match = re.search(r'^' + re.escape(heading) + r'\n.*?(?=^#{1,3} |\Z)', text, re.M | re.S)
    return match.group(0).rstrip() if match else ''


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


class RecallGuideTests(unittest.TestCase):
    def test_common_wording(self):
        for client in CLIENTS[:-1]:
            with self.subTest(client=client):
                self.assertEqual(section(read(client), '### Recall notes'), EXPECTED)

    def test_short_sections(self):
        for client in CLIENTS:
            with self.subTest(client=client):
                lines = section(read(client), '### Recall notes').splitlines()
                self.assertGreater(len(lines), 1)
                self.assertLess(len(lines), 10)

    def test_rho_exception(self):
        self.assertIn('Rho capture does not emit recall notes;', section(read('rho'), '### Recall notes'))

    def test_release_links(self):
        for client in CLIENTS:
            with self.subTest(client=client):
                text = section(read(client), '### Recall notes')
                self.assertIn('](../../docs/releases/0.20.0.md)', text)
                self.assertTrue((ROOT / 'integrations' / client / '../../docs/releases/0.20.0.md').is_file())

    def test_no_stale_certainty(self):
        for client in CLIENTS:
            text = re.sub(r'\s+', ' ', read(client))
            with self.subTest(client=client):
                self.assertNotIn('fix that worked last time', text)
                self.assertNotIn('an error that a later command fixed before', text)

    def test_eight_top_headings_unchanged(self):
        for client in CLIENTS:
            headings = re.findall(r'^## .+$', read(client), re.M)
            with self.subTest(client=client):
                self.assertEqual(len(headings), 8)
                self.assertEqual(headings, BASELINE[client]['headings'])

    def test_command_blocks_unchanged(self):
        for client in CLIENTS:
            blocks = re.findall(r'^```[^\n]*\n.*?^```\s*$', read(client), re.M | re.S)
            with self.subTest(client=client):
                self.assertEqual([digest(b) for b in blocks], BASELINE[client]['code_blocks'])

    def test_status_claims_unchanged(self):
        for client in CLIENTS:
            with self.subTest(client=client):
                self.assertEqual(digest(section(read(client), '## Status')), BASELINE[client]['status'])

    def test_codex_unknown_exit_limit_kept(self):
        text = read('codex')
        self.assertIn('Codex rows are stored with an unknown exit', text)
        self.assertIn('note does not fire for Codex', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
