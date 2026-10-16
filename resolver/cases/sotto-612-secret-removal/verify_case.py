"""Read-only structural checks for the Sotto #612 documentation package.

Usage: python3 verify_case.py PATH_TO_SOTTO_CHECKOUT
These checks do not execute Rust or certify translation meaning.
"""
import importlib.machinery
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT = Path(sys.argv.pop(1)).resolve()
HEADINGS = {
    "README.md": "Removing secrets",
    "README.es.md": "Eliminar secretos",
    "README.fr.md": "Supprimer des secrets",
    "README.de.md": "Geheimnisse entfernen",
    "README.pt-BR.md": "Remover segredos",
}
loader = importlib.machinery.SourceFileLoader("readme_i18n", str(ROOT / "scripts/check-readme-i18n"))
spec = importlib.util.spec_from_loader(loader.name, loader)
checker = importlib.util.module_from_spec(spec)
loader.exec_module(checker)


def section(name):
    text = (ROOT / name).read_text(encoding="utf-8")
    marker = "### " + HEADINGS[name] + "\n"
    if marker not in text:
        raise AssertionError(f"{name}: missing removal guide")
    return text.split(marker, 1)[1].split("\n### ", 1)[0]


class RemovalGuideTests(unittest.TestCase):
    def check_language(self, name):
        text = section(name)
        self.assertEqual(checker.fenced_blocks(text), [
            ("```sh", ("sotto --env staging rm DEMO_OBSOLETE_KEY",)),
            ("```sh", ("sotto login", "sotto --env staging push")),
            ("```sh", ("sotto login", "sotto --env staging pull")),
        ])
        for token in ("`staging`", "`DEMO_OBSOLETE_KEY`", "`--yes`", "`-y`",
                      "`TERM=dumb`", "`sotto get`", "`sotto ls`",
                      "`sotto history --help`", "`sotto rollback --help`",
                      "stdin", "stdout", "stderr", "CI"):
            self.assertIn(token, text)
        self.assertNotIn("\u2014", text)
        self.assertNotIn("\u2013", text)

    def test_english(self):
        self.check_language("README.md")

    def test_spanish(self):
        self.check_language("README.es.md")

    def test_french(self):
        self.check_language("README.fr.md")

    def test_german(self):
        self.check_language("README.de.md")

    def test_brazilian_portuguese(self):
        self.check_language("README.pt-BR.md")

    def test_english_scope_and_warnings(self):
        text = " ".join(section("README.md").split())
        for claim in (
            "remains local until you push", "log in and push the same environment",
            "No as the default", "declining or cancelling leaves the secret unchanged",
            "not an omitted-name picker or any required unlock prompt",
            "CI not being active", "In non-interactive use, a name is required",
            "A named removal does not ask for confirmation, even without `--yes`",
            "retains its version history", "not secure erasure",
            "does not revoke the credential at its external provider",
        ):
            self.assertIn(claim, text)

    def test_complete_readmes_remain_aligned(self):
        self.assertEqual(checker.check_root(ROOT), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
