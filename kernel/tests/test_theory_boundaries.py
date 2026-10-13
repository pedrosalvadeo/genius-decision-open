"""Mathematical catalogue probes only; these do NOT promise FP1 wire extensions."""
import unittest
from fractions import Fraction


class TheoryBoundaryProbes(unittest.TestCase):
    def test_CF007_joint_successors_differ_despite_same_marginals(self):
        a={('U',0),('V',1)}; b={('U',1),('V',0)}
        self.assertEqual({x for x,y in a},{x for x,y in b})
        self.assertEqual({y for x,y in a},{y for x,y in b})
        self.assertNotEqual(a,b)

    def test_CF008_information_transport_square_does_not_commute(self):
        update_A=lambda i,y:y
        update_B=lambda i,y:0
        translate_observation=lambda y:'star'
        self.assertNotEqual(update_A(0,1), update_B(0,translate_observation(1)))

    def test_CF010_monotone_collapse_does_not_reflect_order(self):
        h={0:0,1:0}
        self.assertLessEqual(h[0],h[1])
        self.assertTrue(h[1]<=h[0]); self.assertFalse(1<=0)

    def test_CF018_no_consistent_historical_carrier_matching(self):
        a=[(1,0),(0,1)]; b=[(1,1),(0,0)]
        for t in (0,1): self.assertEqual(sorted(x[t] for x in a),sorted(x[t] for x in b))
        permutations=[(0,1),(1,0)]
        self.assertFalse(any(all(all(b[p[i]][t]>=a[i][t] for t in (0,1)) for i in (0,1)) for p in permutations))
        self.assertFalse(any(all(all(a[p[i]][t]>=b[i][t] for t in (0,1)) for i in (0,1)) for p in permutations))

    def test_CF019_unknown_matching_edge_is_not_absent(self):
        known={('b1','a1'):True,('b1','a2'):False,('b2','a1'):False,('b2','a2'):None}
        self.assertIsNone(known['b2','a2'])
        for final,exists in [(True,True),(False,False)]:
            graph=dict(known); graph['b2','a2']=final
            self.assertEqual(graph['b1','a1'] and graph['b2','a2'],exists)
            if not final: self.assertEqual({a for (b,a),v in graph.items() if b=='b2' and v},set())

    def test_CF023_equal_verdict_does_not_prove_meaning_fidelity(self):
        original={'u','v'}
        self.assertNotEqual({'u'},original)
        self.assertEqual({'u'}|{'v'},original)
        self.assertTrue(all({'u':1,'v':1}[s]==1 for s in original))
        missing=None
        self.assertIsNone(missing)

    def test_CF030_evidence_refinement_requires_old_values_preserved(self):
        first={'e1':1}; refined={'e1':1,'e2':1}; changed={'e1':0,'e2':1}
        self.assertTrue(all(refined[k]==v for k,v in first.items()))
        self.assertFalse(all(changed[k]==v for k,v in first.items()))
        self.assertEqual(Fraction(1,2)+Fraction(1,2),1)

    def test_CF032_intersection_of_relations_not_of_frontiers(self):
        first={('a','a'),('b','b'),('a','b')}; second={('a','a'),('b','b'),('b','a')}
        robust=first&second
        self.assertEqual(robust,{('a','a'),('b','b')})
        self.assertEqual({'a'}&{'b'},set())
        self.assertFalse(any((a,b) in robust and (b,a) not in robust for a,b in [('a','b'),('b','a')]))

    def test_CF034_equivariant_selection_needs_stabilizer_fixed_point(self):
        swap={'a':'b','b':'a','c':'c'}
        self.assertEqual({x for x in ['a','b'] if swap[x]==x},set())
        self.assertEqual({x for x in ['a','b','c'] if swap[x]==x},{'c'})

    def test_CF036_exact_reader_without_certificate_admission_is_not_complete(self):
        sem={'p','q'}; task={'p':0,'q':0}; admitted=[]
        self.assertEqual({task[s] for s in sem},{0})
        self.assertNotEqual(len(sem),1)
        self.assertEqual(admitted,[])
        admitted.append({'A':sem,'value':0})
        self.assertTrue(sem<=admitted[0]['A']<=task.keys())
        self.assertTrue(all(task[s]==admitted[0]['value'] for s in admitted[0]['A']))
