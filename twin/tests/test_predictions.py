"""Frozen field-case predictions stay tied to the committed worlds and contrast readings without editing them."""
from datetime import date
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from genius_twin.store import sha

SCRIPT = Path(__file__).parents[1] / 'cases' / 'predictions.py'
spec = importlib.util.spec_from_file_location('field_predictions', SCRIPT)
predictions = importlib.util.module_from_spec(spec)
spec.loader.exec_module(predictions)


class FrozenPredictionTests(unittest.TestCase):
    def test_committed_world_reproduces_each_frozen_prediction(self):
        for case in predictions.SETUP:
            with self.subTest(case=case):
                frozen = predictions.load(case)
                self.assertEqual(frozen['prediction_sha256'], sha({k: v for k, v in frozen.items() if k != 'prediction_sha256'}))
                self.assertEqual(predictions.compute(case, predictions.FROZEN_WORLD), {k: v for k, v in frozen.items() if k not in ('frozen_at', 'prediction_sha256')})
                # Later revisions of the world (life conditions, laws) keep the trajectories the prediction froze.
                self.assertEqual(predictions.compute(case)['predicted'], frozen['predicted'])

    def test_contrast_records_exact_deltas_and_keeps_the_prediction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(predictions.CASES / 'denver_water_2026', root / 'denver_water_2026')
            before = (root / 'denver_water_2026' / 'prediction.json').read_bytes()
            with patch.object(predictions, 'CASES', root):
                record = predictions.contrast('denver_water_2026', date(2026, 11, 12), '63.5', '2026-11-13T15:00:00+00:00', 'Synthetic test reading; no field data')
                self.assertEqual(record['step'], 1)
                self.assertEqual(record['temporal_relation'], 'PROSPECTIVE_REFERENCE')
                self.assertEqual(record['comparisons']['keep_ban']['scenarios']['dry'], {'predicted_exact': '131/2', 'delta_exact': '-2/1'})
                self.assertEqual(record['comparisons']['keep_ban']['nearest_scenarios'], ['dry', 'normal', 'wet'])
                with self.assertRaises(SystemExit):
                    predictions.contrast('denver_water_2026', date(2026, 11, 12), '63.5', '2026-11-13T15:00:00+00:00', 'Synthetic test reading; no field data')
                with self.assertRaises(SystemExit):
                    predictions.contrast('denver_water_2026', date(2026, 11, 30), '60', '2026-12-01T00:00:00+00:00', 'Synthetic, between steps')
            self.assertEqual((root / 'denver_water_2026' / 'prediction.json').read_bytes(), before)
            log = json.loads((root / 'denver_water_2026' / 'observations.json').read_text())
            self.assertEqual(len(log['observations']), 1)


if __name__ == '__main__':
    unittest.main()
