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


    def test_living_twin_restarts_from_an_observed_step_and_keeps_the_prediction(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(predictions.CASES / 'lake_mead_2028', root / 'lake_mead_2028')
            before = (root / 'lake_mead_2028' / 'prediction.json').read_bytes()
            with patch.object(predictions, 'CASES', root):
                record = predictions.live('lake_mead_2028', date(2027, 3, 31), {'mead': '6025', 'powell': '5070'}, ['glen_release'],
                                          '2027-04-15T12:00:00-07:00', 'Synthetic test reading; no field data')
                self.assertEqual((record['step'], record['horizon']), (6, 10))
                self.assertEqual(record['predicted']['release_6']['most_probable'][:3], ['6025/1', '5524/1', '5127/1'])
                self.assertEqual(record['pvs'], {'release_6': '1/1', 'release_7': '1/1'})
                with self.assertRaises(SystemExit):
                    predictions.live('lake_mead_2028', date(2027, 3, 30), {'mead': '6025', 'powell': '5070'}, [], '2027-04-15T12:00:00-07:00', 'Off-calendar')
                with self.assertRaises(SystemExit):
                    predictions.live('lake_mead_2028', date(2027, 4, 30), {'mead': '6025'}, [], '2027-05-15T12:00:00-07:00', 'Missing Powell')
            self.assertEqual((root / 'lake_mead_2028' / 'prediction.json').read_bytes(), before)
            log = json.loads((root / 'lake_mead_2028' / 'living.json').read_text())
            self.assertEqual(len(log['restarts']), 1)

    def test_each_restart_brings_a_generation_of_the_living_population(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(predictions.CASES / 'denver_water_2026', root / 'denver_water_2026')
            founded = json.loads((root / 'denver_water_2026' / predictions.POPULATION).read_text())
            self.assertEqual(len(founded['generations']), 1)
            with patch.object(predictions, 'CASES', root):
                record = predictions.live('denver_water_2026', date(2026, 12, 15), {'storage': '60', 'outdoor': '0'}, [],
                                          '2026-12-16T12:00:00-07:00', 'Synthetic test reading; no field data')
                with self.assertRaises(SystemExit):
                    predictions.found_population('denver_water_2026')
            generation = record['population_generation']
            self.assertEqual((generation['generation'], generation['step']), (1, 2))
            self.assertTrue(generation['observation'].startswith('2026-12-15 · Synthetic'))
            alive = json.loads((root / 'denver_water_2026' / predictions.POPULATION).read_text())
            self.assertEqual(alive['generations'][-1], generation)
            self.assertEqual(alive['base_model_sha256'], founded['base_model_sha256'])

    def test_committed_populations_are_founded_on_the_frozen_models(self):
        from genius_twin import population
        for case in ('denver_water_2026', 'mendoza_potrerillos_2026', 'lake_mead_2027', 'us_blood_2026'):
            with self.subTest(case=case):
                alive = json.loads((predictions.CASES / case / predictions.POPULATION).read_text())
                name = predictions.FROZEN_WORLD if (predictions.CASES / case / predictions.FROZEN_WORLD).exists() else 'world.json'
                self.assertEqual(alive['base_model_sha256'], population._digest(predictions._model(case, name)))
                self.assertEqual(len(alive['generations']), 1)


if __name__ == '__main__':
    unittest.main()
