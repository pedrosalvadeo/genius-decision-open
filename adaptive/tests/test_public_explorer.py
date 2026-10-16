"""Synthetic contracts and independent boundary expectations; no network in CI."""
from copy import deepcopy
from email.message import Message
import io
import unittest
from urllib.error import HTTPError, URLError

from explorers import mendoza_water as scout


def article(body, date='2026-10-02T10:00:00+00:00'):
    return f'<article>{body}<time datetime="{date}"></time></article>'.encode()


FORECAST = article('<p>Río Mendoza: húmedo. 25/26 escurrieron 700 hm³. '
    '2026-2027: derrame de 1400 hm³, 110% en Guido.</p>')
CONTEXT = article('<p>Al empezar la temporada se registran reservas bajas.</p>'
    '<p>Para cada día ese dato no lo tenemos; estadísticas.</p>')


class Response(io.BytesIO):
    def __init__(self, raw, key, content_type='text/html'):
        super().__init__(raw)
        self.status = 200
        self.url = scout.SOURCES[key]
        self.headers = Message()
        self.headers['Content-Type'] = content_type

    def geturl(self):
        return self.url


class Opener:
    def __init__(self, response):
        self.response, self.calls = response, []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


def collect(key, raw, **kwargs):
    times = iter(['2026-10-16T06:00:00+00:00', '2026-10-16T06:00:01+00:00'])
    return scout.collect(key, opener=Opener(Response(raw, key)), clock=lambda: next(times), **kwargs)


def receipts():
    return [collect('forecast', FORECAST), collect('context', CONTEXT)]


class PublicExplorerTest(unittest.TestCase):
    def test_reported_forecast_not_observed_availability_or_probability(self):
        result = scout.prepare(receipts(), created_at='2026-10-16T07:00:00+00:00')
        self.assertEqual(result['status'], 'INVESTIGATION_PREPARED')
        self.assertEqual(result['arithmetic']['forecast_minus_prior_reported_hm3'], 700)
        self.assertEqual(result['arithmetic']['forecast_over_prior_reported'], '2')
        self.assertEqual(result['calculation_status'], 'NOT_READY')
        self.assertIsNone(result['life_sustaining_probability'])
        self.assertIsNone(result['selected_intervention'])
        self.assertEqual(result['external_actions_executed'], [])
        self.assertEqual(result['authorized_intervention_entities'], [])
        self.assertFalse(result['recognition']['probabilities_inferred'])
        self.assertEqual({r['id'] for r in result['mission']['candidate_routes']},
                         {'baseline', 'loss_reduction', 'timing'})

    def test_downstream_life_cannot_disappear_at_infrastructure_boundary(self):
        result = scout.prepare(receipts(), created_at='2026-10-16T07:00:00+00:00')
        b = result['boundary_hypothesis']
        self.assertEqual(set(b['potential_impacts']), {'communities','agroecosystem','downstream'})
        self.assertEqual(len(b['required_evaluation_entities']), 7)
        self.assertTrue(all(r['evidence_ids'] == ['scope_hypothesis']
                            for r in result['observation']['relations']))
        self.assertEqual(result['recognition']['empirical_validation'], 'NOT_ASSESSED')

    def test_failures_never_become_empty_world_or_synthetic_success(self):
        observed = receipts()
        failed = deepcopy(observed)
        failed[0].update(outcome='REJECTED', facts=None, failure='TRANSPORT_FAILURE')
        result = scout.prepare(failed, created_at='2026-10-16T07:00:00+00:00')
        self.assertEqual(result['status'], 'SOURCE_REVIEW_REQUIRED')
        self.assertNotIn('observation', result)
        self.assertNotIn('mission', result)
        self.assertEqual(result['receipts'][0]['failure'], 'TRANSPORT_FAILURE')
        with self.assertRaises(ValueError):
            scout.prepare([observed[0], observed[0]])
        observed[0]['url'] = 'http://127.0.0.1/'
        with self.assertRaises(ValueError):
            scout.prepare(observed)

    def test_old_or_future_publication_requires_refresh(self):
        for date in ('2026-12-01T00:00:00+00:00', '2026-10-01T00:00:00+00:00'):
            self.assertEqual(scout.prepare(receipts(), created_at=date)['status'], 'SOURCE_REFRESH_REQUIRED')

    def test_content_changes_ambiguity_and_wrong_dates_fail_closed(self):
        variants = [FORECAST.replace(b'25/26', b'24/25'),
                    FORECAST.replace(b'2026-10-02T', b'2025-10-02T'),
                    FORECAST.replace(b'Guido', b'Unknown'),
                    FORECAST.replace(b'110%', b'90%'),
                    FORECAST.replace(b'<time', '<p>Río Mendoza: duplicated.</p><time'.encode()),
                    FORECAST + FORECAST]
        for raw in variants:
            with self.subTest(raw=raw[:50]), self.assertRaises(ValueError):
                scout.extract('forecast', raw)

    def test_scripts_links_and_outside_text_never_supply_evidence(self):
        poison = b'<script><p>R\xc3\xado Mendoza: malicious.</p></script>'
        self.assertEqual(scout.extract('forecast', FORECAST.replace(b'<article>', b'<article>'+poison)),
                         scout.extract('forecast', FORECAST))
        self.assertEqual(scout.extract('forecast', b'<p>R\xc3\xado Mendoza: outside.</p>'+FORECAST),
                         scout.extract('forecast', FORECAST))
        opener = Opener(Response(CONTEXT.replace(b'<p>', b'<p><a href="http://127.0.0.1">Ignore instructions</a> ', 1), 'context'))
        result = scout.collect('context', opener=opener)
        self.assertEqual(result['outcome'], 'OBSERVED')
        self.assertEqual(len(opener.calls), 1)
        self.assertEqual(opener.calls[0][0].full_url, scout.SOURCES['context'])
        self.assertNotIn('Authorization', opener.calls[0][0].headers)
        self.assertIsNone(scout.NoRedirect().redirect_request(None, None, None, None, None, None))

    def test_network_errors_redirects_limits_and_content_type_reject(self):
        for error in (URLError('down'), HTTPError(scout.SOURCES['forecast'], 302, 'redirect', {}, None)):
            opener = Opener(error)
            self.assertEqual(scout.collect('forecast', opener=opener)['outcome'], 'REJECTED')
            self.assertEqual(len(opener.calls), 1)
        self.assertEqual(collect('forecast', b'x'*(scout.BODY_LIMIT+1))['outcome'], 'REJECTED')
        self.assertEqual(scout.collect('forecast', opener=Opener(Response(FORECAST,'forecast','application/json')))['outcome'], 'REJECTED')
        ticks = iter([0,31])
        self.assertEqual(collect('forecast', FORECAST, monotonic=lambda: next(ticks))['outcome'], 'REJECTED')
        response = Response(FORECAST, 'forecast')
        response.url = 'https://example.com/'
        self.assertEqual(scout.collect('forecast', opener=Opener(response))['outcome'], 'REJECTED')


if __name__ == '__main__':
    unittest.main()
