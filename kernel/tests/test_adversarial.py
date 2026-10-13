"""Independent adversarial F2 audit cases; input fixtures only are shared.

Expected values below are direct finite counterexamples to the normative
contract, not a second execution of the implementation as its own oracle.
"""
from copy import deepcopy
import hashlib
import json
from fractions import Fraction
from itertools import product
import unittest

from fixtures import small, raw, query, add_function, add_resources
from genius_kernel import evaluate, verify_result, verify_decisive_certificate


def policies(result):
    return {p['policy']: p for p in result['policies']}


def codes(result):
    return {d['code'] for d in result['diagnostics']}


def cell_value(cell):
    return cell.get('value') if cell['state'] == 'DEFINED' else None


class AdversarialAudit(unittest.TestCase):
    def run_input(self, data):
        result = evaluate(raw(data))
        self.assertEqual(result['execution']['status'], 'COMPLETE')
        return result

    def test_strict_json_numbers_duplicate_keys_unicode_and_unknown_fields(self):
        d = small()
        b = raw(d)
        mutations = [
            b.replace(b'"horizon":"1"', b'"horizon":1'),
            b.replace(b'"horizon":"1"', b'"horizon":true'),
            b.replace(b'"horizon":"1"', b'"horizon":NaN'),
            b.replace(b'"horizon":"1"', b'"horizon":"1","horizon":"1"'),
            b.replace(b'Formal test only.', b'\\ud800'),
            b.replace(b'"format":', b'"unexpected":null,"format":'),
            b'\xff', b'[]', b'{',
        ]
        for bad in mutations:
            with self.subTest(bad=bad[:80]):
                r = evaluate(bad)
                self.assertEqual(r['presentation'], 'INVALID')
                self.assertEqual(r['policies'], [])
                self.assertEqual(r['decision']['state'], 'BLOCKED')

    def test_invalid_unreached_rows_are_not_ignored(self):
        for table, row in [
            ('measurements', {'t': '0', 'x': 'unknown', 'index': 'f0', 'raw': '0/1'}),
            ('measurements', {'t': '0', 'x': 'x0', 'index': 'f0', 'raw': '2/2'}),
        ]:
            d = small()
            add_function(d, {(0, 'x0'): ['0/1'], (1, 'x_p_r_1'): ['1/1']})
            d['functional'][table].append(row)
            self.assertEqual(self.run_input(d)['presentation'], 'INVALID')
        d = small()
        d['model']['states'].append('unreached')
        d['model']['transitions'].append({'t': '0', 'x': 'unreached', 'a': 'act_p',
            'outcomes': [{'branch': 'z', 'u': 'u_r', 'next_x': 'absent', 'y': 'y'}]})
        self.assertEqual(self.run_input(d)['presentation'], 'INVALID')

    def test_partial_causal_local_semantics_can_refute_unknown_scope(self):
        d = small({'p': [['o', 'a', 'a'], ['o', 'b', 'b']]})
        d['model']['transitions'] = [r for r in d['model']['transitions'] if r['x'] != 'x_p_s_1']
        d['semantics']['task'][0]['value'] = '0'
        d['constraints'] = [{'id': 'all', 'kind': 'task_all', 'scope': 'LEAVES', 'basis': ['A']}]
        r = self.run_input(d)
        self.assertEqual(r['presentation'], 'UNRESOLVED')
        p = policies(r)['p']
        evidence = {tuple(row['query']['path']): row for row in p['evidence']}
        self.assertEqual(evidence[()]['verdict']['state'], 'BLOCKED')
        self.assertEqual(cell_value(evidence[('r',)]['verdict'])['value'], '0')
        self.assertEqual(cell_value(evidence[('r', 'step')]['verdict'])['value'], '0')
        self.assertEqual(p['hard'][0]['scope']['state'], 'BLOCKED')
        self.assertEqual(cell_value(p['hard'][0]['value']), '0')
        self.assertEqual(p['functional']['reduction']['state'], 'BLOCKED')
        self.assertEqual(r['decision']['value']['coverage'], 'RELATIVE')

    def test_bad_reference_still_invalid_when_tree_is_partial(self):
        d = small({'p': [['o', 'a', 'a'], ['o', 'b', 'b']]})
        d['model']['transitions'] = [r for r in d['model']['transitions'] if r['x'] != 'x_p_s_1']
        d['composition']['rows'].append({'query': query('p', ['never']), 'values': []})
        r = self.run_input(d)
        self.assertEqual(r['presentation'], 'INVALID')
        self.assertIn('UNKNOWN_REFERENCE', codes(r))

    def test_tabulated_inadmissible_action_survives(self):
        d = small()
        d['model']['admissible'][0]['actions'] = []
        r = self.run_input(d)
        p = policies(r)['p']
        self.assertEqual(cell_value(p['causal']['nodes'][0]['action']), 'act_p')
        self.assertEqual(p['causal']['complete']['state'], 'OUTSIDE_DOMAIN')
        self.assertEqual(p['causal']['leaves'], [])
        self.assertIn('ACTION_NOT_ADMISSIBLE', codes(r))

    def test_law_extra_branch_is_math_failure_not_structural_unknown_reference(self):
        d = small()
        d['law']['rows'][0]['weights'].append({'branch': 'phantom', 'mass': '0/1'})
        r = self.run_input(d)
        self.assertEqual(r['presentation'], 'VALID')
        self.assertIn('LAW_INVALID', codes(r))
        self.assertNotIn('UNKNOWN_REFERENCE', codes(r))
        p = policies(r)['p']
        self.assertEqual(p['probability']['pvs']['state'], 'BLOCKED')
        self.assertEqual(cell_value(p['evidence'][0]['verdict'])['value'], '1')

    def test_null_subtree_missing_law_allowed_but_supplied_bad_row_rejected(self):
        d = small({'p': [['o', 'a', 'a'], ['o', 'b', 'b']]})
        for row in d['law']['rows']:
            if row['query']['path'] == []:
                row['weights'] = [{'branch': 'r', 'mass': '1/1'}, {'branch': 's', 'mass': '0/1'}]
        d['law']['rows'] = [row for row in d['law']['rows'] if row['query']['path'] != ['s']]
        d['semantics']['task'] = [row for row in d['semantics']['task'] if row['state'] != 'sem_p_s']
        r = self.run_input(d)
        p = policies(r)['p']
        self.assertEqual(cell_value(p['probability']['pvs']), '1/1')
        self.assertEqual(cell_value(p['probability']['vector']), {'success': '1/1', 'failure': '0/1', 'undecided': '0/1'})
        self.assertEqual(len(p['causal']['leaves']), 2)
        self.assertEqual(len(cell_value(p['probability']['partition'])['undecided']), 1)
        d['law']['rows'].append({'query': query('p', ['s']), 'weights': [{'branch': 'step', 'mass': '0/1'}]})
        p = policies(self.run_input(d))['p']
        self.assertEqual(p['probability']['pvs']['state'], 'BLOCKED')
        self.assertTrue(all(m['mass']['state'] == 'BLOCKED' for m in p['probability']['masses']))

    def calibration_cross_policy(self):
        d = small({'p': [['o', 'a']], 'q': [['o', 'b']]})
        add_function(d, {(0, 'x0'): ['0/1'], (1, 'x_p_r_1'): ['1/1'], (1, 'x_q_r_1'): ['2/1']})
        d['functional']['indices'][0]['calibration'] = [
            {'raw': '0/1', 'value': '0/1'}, {'raw': '1/1', 'value': '2/1'}, {'raw': '2/1', 'value': '1/1'}]
        return d

    def test_shared_calibration_checks_union_B0_and_keeps_numeric_profiles(self):
        r = self.run_input(self.calibration_cross_policy())
        self.assertEqual(r['decision']['value']['B'], [])
        for p in r['policies']:
            self.assertEqual(p['functional']['terminal']['state'], 'BLOCKED')
            self.assertTrue(all(row['profile']['state'] == 'DEFINED' for row in p['functional']['points']))

    def test_missing_fourth_criterion_changes_B0_but_hard_failure_does_not(self):
        d = self.calibration_cross_policy()
        d['semantics']['task'] = [r for r in d['semantics']['task'] if r['state'] != 'sem_q_r']
        r = self.run_input(d)
        self.assertEqual(r['decision']['value']['B'], ['p'])
        self.assertEqual(r['decision']['value']['coverage'], 'RELATIVE')
        d = self.calibration_cross_policy()
        add_resources(d, {'fuel': ['d']}, {('p', (), 'd'): '0/1', ('p', ('r',), 'd'): '0/1',
                                         ('q', (), 'd'): '20/1', ('q', ('r',), 'd'): '20/1'})
        r = self.run_input(d)
        self.assertEqual(r['decision']['value']['failed'], ['q'])
        self.assertEqual(r['decision']['value']['B'], [])

    def test_shared_order_transport_cross_policy_pair(self):
        d = small({'p': [['o', 'a']], 'q': [['o', 'b']]}, recipe={'kind': 'hold', 'length': '0'})
        d['generative']['common_order'].append(['a', 'b'])
        r = self.run_input(d)
        self.assertEqual(r['decision']['value']['B'], [])
        self.assertIn('GEN_ORDER_TRANSPORT', codes(r))
        self.assertTrue(all(p['generative']['cag']['state'] == 'BLOCKED' for p in r['policies']))

    def test_invalid_order_on_unreached_identity_invalidates_component(self):
        d = small()
        d['generative']['native_ids'].append('unreached')
        r = self.run_input(d)
        self.assertEqual(r['presentation'], 'VALID')
        self.assertIn('GEN_ORDER_INVALID', codes(r))
        self.assertEqual(policies(r)['p']['generative']['cag']['state'], 'BLOCKED')

    def test_horizon_zero_root_is_only_leaf_probability_one_and_no_future_witness(self):
        d = small({'p': [['o']]}, recipe={'kind': 'hold', 'length': '100000000000000000000'})
        d['model']['actions'] = []
        d['model']['observations'] = []
        d['model']['exogenous'] = []
        d['selection'] = {'mode': 'unique'}
        r = self.run_input(d)
        p = policies(r)['p']
        self.assertEqual(p['causal']['leaves'], [query('p')])
        self.assertEqual(cell_value(p['probability']['pvs']), '1/1')
        self.assertEqual(cell_value(p['generative']['cag']), ['o'])
        self.assertEqual(cell_value(p['generative']['additional']), [])
        self.assertEqual(p['generative']['witnesses'], [])
        self.assertEqual(cell_value(r['decision']['value']['selection']), 'p')
        self.assertEqual(r['integration']['state'], 'DEFINED')

    def test_relative_frontier_never_selects_even_unique_and_priority(self):
        for mode in ({'mode': 'unique'}, {'mode': 'priority', 'order': ['p'], 'basis': ['A']}):
            d = small()
            d['composition']['views'] = []
            d['selection'] = mode
            r = self.run_input(d)
            self.assertEqual(r['decision']['value']['frontier'], ['p'])
            self.assertEqual(r['decision']['value']['coverage'], 'RELATIVE')
            self.assertEqual(r['decision']['value']['selection']['state'], 'OUTSIDE_DOMAIN')

    def test_declared_operational_zero_limits_do_not_claim_mathematical_absence(self):
        for limit in ['max_nodes', 'max_operations', 'max_seconds', 'max_input_bytes', 'max_integer_digits']:
            r = evaluate(raw(small()), {limit: 0})
            self.assertEqual(r['execution']['status'], 'LIMITED', limit)
            self.assertEqual(r['decision']['state'], 'BLOCKED')
            self.assertEqual(r['integration']['state'], 'BLOCKED')

    def test_exhaustive_two_leaf_semantic_labels_and_two_laws(self):
        # 3^2 partial truth assignments times two laws, including a null leaf.
        # The oracle is a three-bin weighted count over the declared leaves.
        for labels in product(('0', '1', None), repeat=2):
            for weights in ((Fraction(1, 2), Fraction(1, 2)), (Fraction(1), Fraction(0))):
                with self.subTest(labels=labels, weights=weights):
                    d = small({'p': [['o', 'a'], ['o', 'b']]})
                    d['semantics']['task'] = [{'state': f'sem_p_{branch}', 'value': label}
                        for branch, label in zip(('r', 's'), labels) if label is not None]
                    d['law']['rows'][0]['weights'] = [{'branch': branch,
                        'mass': f'{w.numerator}/{w.denominator}'} for branch, w in zip(('r', 's'), weights)]
                    d['constraints'] = [{'id': 'all', 'kind': 'task_all', 'scope': 'LEAVES', 'basis': ['A']}]
                    r = self.run_input(d)
                    p = policies(r)['p']
                    totals = {name: sum((w for label, w in zip(labels, weights) if label == bit), Fraction(0))
                              for name, bit in [('success', '1'), ('failure', '0'), ('undecided', None)]}
                    expected = {name: f'{v.numerator}/{v.denominator}' for name, v in totals.items()}
                    self.assertEqual(cell_value(p['probability']['vector']), expected)
                    self.assertEqual(cell_value(p['probability']['pvs']),
                                     expected['success'] if totals['undecided'] == 0 else None)
                    root = p['evidence'][0]['verdict']
                    self.assertEqual(cell_value(root)['value'] if cell_value(root) else None,
                                     labels[0] if labels[0] == labels[1] else None)
                    hard_expected = '0' if '0' in labels else None if None in labels else '1'
                    self.assertEqual(cell_value(p['hard'][0]['value']), hard_expected)

    def test_finite_temporal_recipe_metamorphic_enumeration(self):
        # Every two-step pair of traces over three identities: 3^4 = 81.
        # Relations tested independently: hold0=att; hold1/acc subset att;
        # robust subset possible; holdL has no future candidate when L>=H.
        ids = ['o', 'a', 'b']
        order = [[a, b] for i, a in enumerate(ids) for b in ids[i:]]
        for suffix in product(ids, repeat=4):
            runs = [['o', *suffix[:2]], ['o', *suffix[2:]]]
            results = {}
            for label, recipe, mode in [
                ('att_possible', {'kind': 'att'}, 'possible'),
                ('att_robust', {'kind': 'att'}, 'robust'),
                ('hold0', {'kind': 'hold', 'length': '0'}, 'possible'),
                ('hold1', {'kind': 'hold', 'length': '1'}, 'possible'),
                ('hold2', {'kind': 'hold', 'length': '2'}, 'possible'),
                ('acc', {'kind': 'acc'}, 'possible'),
            ]:
                d = small({'p': runs}, recipe=recipe, mode=mode)
                domain = set(d['generative']['native_ids'])
                for side in ('native_order', 'common_order'):
                    d['generative'][side] = [p for p in order if set(p) <= domain]
                r = self.run_input(d)
                self.assertEqual(r['integration']['state'], 'DEFINED', (suffix, label))
                results[label] = set(cell_value(policies(r)['p']['generative']['cag']))
            self.assertEqual(results['hold0'], results['att_possible'])
            self.assertLessEqual(results['hold1'], results['att_possible'])
            self.assertLessEqual(results['acc'], results['att_possible'])
            self.assertLessEqual(results['att_robust'], results['att_possible'])
            self.assertEqual(results['hold2'], {'o'})


class AdversarialVerifierAudit(unittest.TestCase):
    def setUp(self):
        self.data = small({'p': [['o', 'a'], ['o', 'b']]})
        self.data['semantics']['states'].extend(['extra_yes', 'extra_no'])
        self.data['semantics']['task'].extend([{'state': 'extra_yes', 'value': '1'},
                                              {'state': 'extra_no', 'value': '0'}])
        self.raw = raw(self.data)
        self.result = evaluate(self.raw)
        self.assertEqual(self.result['integration']['state'], 'DEFINED')

    def test_verifier_accepts_valid_noncanonical_superset_certificates(self):
        supplied = deepcopy(self.result)
        certificate = supplied['policies'][0]['evidence'][0]['verdict']['value']
        certificate['A'].append('extra_yes')
        certificate['task_rows'].append({'state': 'extra_yes', 'value': '1'})
        envelope = {'input_digest': hashlib.sha256(self.raw).hexdigest(), 'certificate': certificate}
        check = verify_decisive_certificate(self.raw, envelope)
        self.assertTrue(check['valid'], check)
        check = verify_result(self.raw, supplied)
        self.assertTrue(check['valid'], check)

    def test_verifier_rejects_noncanonical_extra_zero_unknown_duplicate_and_wrong_rows(self):
        certificate = self.result['policies'][0]['evidence'][0]['verdict']['value']
        mutations = []
        c = deepcopy(certificate); c['A'].append('extra_no'); c['task_rows'].append({'state': 'extra_no', 'value': '0'}); mutations.append(c)
        c = deepcopy(certificate); c['A'].append('unknown'); c['task_rows'].append({'state': 'unknown', 'value': '1'}); mutations.append(c)
        c = deepcopy(certificate); c['A'].append(c['A'][0]); mutations.append(c)
        c = deepcopy(certificate); c['A'] = c['A'][:1]; c['task_rows'] = c['task_rows'][:1]; mutations.append(c)
        c = deepcopy(certificate); c['task_rows'][0]['value'] = '0'; mutations.append(c)
        c = deepcopy(certificate); c['read']['leaves'].pop(); c['read']['references'].pop(); mutations.append(c)
        c = deepcopy(certificate); c['read']['states'].pop(); mutations.append(c)
        for c in mutations:
            check = verify_decisive_certificate(self.raw, {'input_digest': self.result['input_digest'], 'certificate': c})
            self.assertFalse(check['valid'], (c, check))

    def test_result_verifier_rejects_forged_values_coverage_types_and_refs(self):
        mutations = []
        r = deepcopy(self.result); r['input_digest'] = '0' * 64; mutations.append(r)
        r = deepcopy(self.result); r['policies'][0]['causal']['nodes'].pop(); mutations.append(r)
        r = deepcopy(self.result); r['policies'][0]['probability']['pvs']['value'] = '0/1'; mutations.append(r)
        r = deepcopy(self.result); r['decision']['value']['frontier'] = []; mutations.append(r)
        r = deepcopy(self.result); r['decision']['value']['B'] = []; mutations.append(r)
        r = deepcopy(self.result); r['decision']['value']['pairs'][0]['weak'] = '0'; mutations.append(r)
        r = deepcopy(self.result); r['decision']['value']['pairs'][0]['weak'] = 1; mutations.append(r)
        r = deepcopy(self.result); r['decision']['value']['frontier'].append('p'); mutations.append(r)
        r = deepcopy(self.result); r['integration']['value']['assumptions'] = []; mutations.append(r)
        r = deepcopy(self.result); r['checks'][0]['support'] = [{'document': 'OUTPUT', 'pointer': '/checks/0'}]; mutations.append(r)
        r = deepcopy(self.result); r['checks'][0]['support'] = [{'document': 'INPUT', 'pointer': '/does_not_exist'}]; mutations.append(r)
        r = deepcopy(self.result); r['checks'][0]['outcome'] = 'FAIL'; mutations.append(r)
        r = deepcopy(self.result); r['checks'].append(deepcopy(r['checks'][0])); mutations.append(r)
        r = deepcopy(self.result); r['execution']['progress']['expanded_nodes'] = '999'; mutations.append(r)
        r = deepcopy(self.result); r['injected'] = 'extra'; mutations.append(r)
        for n, r in enumerate(mutations):
            check = verify_result(self.raw, r)
            self.assertFalse(check['valid'], (n, check))

    def test_generated_identifier_renaming_and_table_set_order_are_not_semantics(self):
        supplied = deepcopy(self.result)
        ids = [c['id'] for c in supplied['checks']] + [d['id'] for d in supplied['diagnostics']]
        ids.append(supplied['integration']['value']['id'])
        ids.extend(e['verdict']['value']['id'] for p in supplied['policies'] for e in p['evidence']
                   if e['verdict']['state'] == 'DEFINED')
        renamed = {s: f'AuditID.{n}' for n, s in enumerate(ids)}
        def transform(obj, path=()):
            if isinstance(obj, dict):
                return {k: transform(v, path + (k,)) for k, v in obj.items()}
            if isinstance(obj, list):
                vals = [transform(v, path + (str(n),)) for n, v in enumerate(obj)]
                # Preserve explicitly ordered causal words and identity traces.
                ordered = path[-1:] in [('path',), ('window',), ('outcomes',)] or path[-2:] == ('identities', 'value')
                return vals if ordered else list(reversed(vals))
            return renamed.get(obj, obj) if isinstance(obj, str) else obj
        supplied = transform(supplied)
        check = verify_result(self.raw, supplied)
        self.assertTrue(check['valid'], check)

    def test_changed_input_whitespace_changes_digest_and_missing_input_is_not_accepted(self):
        check = verify_result(self.raw + b'\n', self.result)
        self.assertFalse(check['valid'], check)
        check = verify_result(b'', self.result)
        self.assertFalse(check['valid'], check)

    def test_verifier_budget_exhaustion_is_incomplete_not_false_certificate_proof(self):
        check = verify_result(self.raw, self.result, {'max_operations': 0})
        self.assertIsNone(check['valid'], check)
        self.assertEqual(check['status'], 'INCOMPLETE')

    def test_valid_frontier_certificate_can_list_only_one_of_multiple_dominators(self):
        d = small({'a': [['o', 'g']], 'b': [['o', 'g']], 'c': [['o', 'g']]})
        add_function(d, {(0, 'x0'): ['0/1'], (1, 'x_a_r_1'): ['1/1'],
                         (1, 'x_b_r_1'): ['2/1'], (1, 'x_c_r_1'): ['3/1']})
        b = raw(d)
        supplied = evaluate(b)
        self.assertEqual(supplied['decision']['value']['frontier'], ['c'])
        rows = {r['policy']: r for r in supplied['decision']['value']['dominators']}
        self.assertEqual(set(rows['a']['by']), {'b', 'c'})
        rows['a']['by'] = ['b']
        check = verify_result(b, supplied)
        self.assertTrue(check['valid'], check)

    def test_causal_check_may_not_depend_on_later_probability_constructor(self):
        supplied = deepcopy(self.result)
        action = supplied['policies'][0]['causal']['nodes'][0]['action']
        check = next(c for c in supplied['checks'] if c['id'] == action['checks'][0])
        check['support'] = [{'document': 'OUTPUT', 'pointer': '/policies/0/probability/pvs'}]
        verdict = verify_result(self.raw, supplied)
        self.assertFalse(verdict['valid'], verdict)

    def test_reported_node_bound_may_not_contradict_reported_progress(self):
        supplied = deepcopy(self.result)
        supplied['execution']['limits'] = [{'name': 'max_nodes', 'bound': '0'}]
        verdict = verify_result(self.raw, supplied)
        self.assertFalse(verdict['valid'], verdict)

    def test_cell_can_cite_sound_existing_broader_scope_causal_check(self):
        supplied = deepcopy(self.result)
        p = supplied['policies'][0]
        p['causal']['nodes'][0]['action']['checks'] = p['causal']['complete']['checks'][:]
        verdict = verify_result(self.raw, supplied)
        self.assertTrue(verdict['valid'], verdict)

    def test_cell_can_retain_redundant_valid_input_prerequisite_proof(self):
        supplied = deepcopy(self.result)
        input_check = next(c['id'] for c in supplied['checks']
                           if c['rule'] == 'INPUT_TYPES' and c['outcome'] == 'PASS')
        supplied['policies'][0]['causal']['nodes'][0]['action']['checks'].append(input_check)
        verdict = verify_result(self.raw, supplied)
        self.assertTrue(verdict['valid'], verdict)

    def test_cell_extra_proof_may_not_come_from_later_probability_stage(self):
        supplied = deepcopy(self.result)
        p = supplied['policies'][0]
        p['causal']['nodes'][0]['action']['checks'].extend(p['probability']['pvs']['checks'])
        verdict = verify_result(self.raw, supplied)
        self.assertFalse(verdict['valid'], verdict)

    def test_independent_cag_and_welfare_cannot_accredit_each_other(self):
        for receiver, supplier in [('generative', 'welfare'), ('welfare', 'generative')]:
            supplied = deepcopy(self.result)
            p = supplied['policies'][0]
            cells = {'generative': p['generative']['cag'], 'welfare': p['welfare']['profile']}
            cells[receiver]['checks'].extend(cells[supplier]['checks'])
            verdict = verify_result(self.raw, supplied)
            self.assertFalse(verdict['valid'], (receiver, supplier, verdict))

    def test_law_mass_cannot_take_semantic_read_as_independent_constructor_proof(self):
        supplied = deepcopy(self.result)
        p = supplied['policies'][0]
        check_id = p['probability']['masses'][0]['mass']['checks'][0]
        check = next(c for c in supplied['checks'] if c['id'] == check_id)
        check['support'] = [{'document': 'OUTPUT', 'pointer': '/policies/0/evidence/0/sem'}]
        verdict = verify_result(self.raw, supplied)
        self.assertFalse(verdict['valid'], verdict)

    def test_semantic_partition_check_cannot_depend_on_later_pvs_despite_same_rule(self):
        supplied = deepcopy(self.result)
        p = supplied['policies'][0]
        check_id = p['probability']['partition']['checks'][0]
        check = next(c for c in supplied['checks'] if c['id'] == check_id)
        self.assertEqual(check['rule'], 'VPROB')
        check['support'] = [{'document': 'OUTPUT', 'pointer': '/policies/0/probability/pvs'}]
        verdict = verify_result(self.raw, supplied)
        self.assertFalse(verdict['valid'], verdict)


if __name__ == '__main__':
    unittest.main()
