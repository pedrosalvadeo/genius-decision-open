from copy import deepcopy
from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from federation import genetics
from federation.core import Node, digest
from federation.evolution_experiment import Fixture, CTX, run
from federation.experiment import observation
from federation.organism import Organism
from federation.network_protocol import sign


class GeneticsTests(unittest.TestCase):
    def test_alleles_mutation_recombination_and_protected_constitution(self):
        parent=genetics.founder('parent');variants=genetics.variants(parent,'birth')
        self.assertEqual(len(variants),4)
        for variant in variants:
            self.assertEqual(sum(parent['genes'][k]!=variant['genes'][k] for k in parent['genes']),1)
            self.assertEqual(variant['parents'],[digest(parent)])
            self.assertEqual(variant['constitution_sha256'],genetics.CONSTITUTION_HASH)
        mixed=genetics.recombine(variants[0],variants[-1],'mix')
        self.assertEqual(mixed['genes']['estimator'],variants[0]['genes']['estimator'])
        self.assertEqual(mixed['genes']['window'],variants[-1]['genes']['window'])
        self.assertEqual(mixed['generation'],2)
        for change in ({'constitution_sha256':'0'*64},{'genes':{'estimator':'exec','window':5}},
                       {'genes':{'estimator':'last_value','window':True}},{'code':'arbitrary'}):
            invalid={**deepcopy(parent),**change}
            with self.assertRaises(ValueError):genetics.validate(invalid)

    def test_expression_changes_behavior_and_keeps_simultaneous_events_together(self):
        parent=genetics.founder('parent')
        evidence=[dict(hash=str(i),event=str(i),observed_at=str(i),value=v) for i,v in enumerate((2,4,20))]
        self.assertEqual(genetics.express(parent,evidence)['estimate'],4)
        self.assertEqual(genetics.express(genetics.mutate(parent,'estimator','mean_floor','m'),evidence)['estimate'],8)
        self.assertEqual(genetics.express(genetics.mutate(parent,'estimator','last_value','l'),evidence)['estimate'],20)
        same=[{**r,'observed_at':'same'} for r in evidence]*3
        self.assertEqual(genetics.express(parent,same)['evidence_count'],9)


class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.fixture=Fixture(self.root/'node')
        self.organism=self.fixture.organism

    def complete(self,trial_id='trial',harmful=False):
        self.organism.begin(trial_id,CTX)
        for i in range(8):
            _,trial,target=self.fixture.round(trial_id,i,i*100+10 if harmful and i>=4 else None)
        return trial,target

    def test_prospective_selection_uses_genius_and_changes_next_phenotype(self):
        trial,target=self.complete()
        self.assertEqual(trial['status'],'ADOPTED')
        self.assertTrue(trial['confirmation_native']['verification']['valid'])
        self.assertEqual(trial['confirmation_native']['decision']['selected'],'candidate')
        selected=trial['candidates'][trial['candidate']]
        self.assertEqual(selected['genes']['estimator'],'last_value')
        self.assertEqual(self.organism.feedback('trial',target),trial)
        following=self.organism.begin('next',CTX)
        self.assertEqual(following['baseline'],digest(selected))
        f,_,_=self.fixture.round('next',8)
        self.assertEqual(f['estimates'][f['expressed_genome']]['estimate'],830)
        self.assertIsNone(self.organism.status()['life_sustainment_probability'])

    def test_confirmation_rejects_training_winner_that_deteriorates(self):
        trial,_=self.complete(harmful=True)
        self.assertEqual(trial['status'],'REJECTED')
        self.assertEqual(self.organism.status()['adapted_contexts'],0)
        self.assertEqual(self.organism.status()['locally_confirmed_changes'],0)

    def test_adaptation_does_not_cross_contexts_or_units(self):
        self.complete();other={**CTX,'unit':'different_unit'}
        trial=self.organism.begin('other',other)
        self.assertEqual(trial['baseline'],self.organism.status()['founder_sha256'])

    def test_restart_frozen_values_and_immutable_outcome(self):
        self.organism.begin('trial',CTX);forecast,trial,target=self.fixture.round('trial',0)
        restarted=Organism(Node(self.fixture.node.directory,self.fixture.node.node_id,lambda:self.fixture.stamp.isoformat()))
        self.assertEqual(restarted.feedback('trial',target),trial)
        changed=deepcopy(target);changed['value']+=1
        with self.assertRaisesRegex(ValueError,'IMMUTABLE'):restarted.feedback('trial',changed)
        self.assertEqual(restarted.load()['trials']['trial']['rounds'][0]['estimates'],forecast['estimates'])

    def test_missing_data_suspend_evolution_and_do_not_become_zero(self):
        self.organism.begin('empty',CTX)
        result=self.organism.predict('empty',None,(self.fixture.stamp+timedelta(hours=1)).isoformat())
        self.assertEqual(result['status'],'EVIDENCE_REVIEW')
        self.assertIsNone(result['forecast']['estimate'])
        self.assertEqual(self.organism.status()['locally_confirmed_changes'],0)

    def test_conflicting_versions_block_all_genetic_predictors(self):
        stamp=self.fixture.stamp
        row=observation(CTX,'fixture','conflict',10,observed_at=(stamp-timedelta(minutes=1)).isoformat(),
            valid_until=(stamp+timedelta(days=1)).isoformat())
        self.fixture.node.ingest([row,{**deepcopy(row),'value':90}])
        self.organism.begin('conflict',CTX)
        result=self.organism.predict('conflict',None,(stamp+timedelta(hours=1)).isoformat())
        self.assertEqual(result['forecast']['status'],'CONFLICT_REVIEW')
        self.assertEqual(self.organism.load()['trials']['conflict']['rounds'],[])

    def test_no_improvement_does_not_force_a_mutation(self):
        self.organism.begin('constant',CTX)
        for i in range(4):
            self.fixture.stamp+=timedelta(hours=1);stamp=self.fixture.stamp
            self.fixture.node.ingest([observation(CTX,'input',f'x-{i}',10,
                observed_at=(stamp-timedelta(minutes=1)).isoformat(),valid_until=(stamp+timedelta(days=1)).isoformat())])
            self.organism.predict('constant',None,(stamp+timedelta(minutes=10)).isoformat())
            self.fixture.stamp+=timedelta(minutes=1)
            trial=self.organism.feedback('constant',observation(CTX,'target',f'y-{i}',10,
                observed_at=self.fixture.stamp.isoformat(),valid_until=(stamp+timedelta(days=1)).isoformat()))
        self.assertEqual(trial['status'],'NO_IMPROVEMENT')
        self.assertIsNone(trial['candidate']);self.assertEqual(self.organism.status()['locally_confirmed_changes'],0)

    def test_finite_trial_budget_and_terminal_generation_are_enforced(self):
        for i in range(4):
            self.organism.begin('empty-'+str(i),CTX)
            self.organism.predict('empty-'+str(i),None,(self.fixture.stamp+timedelta(hours=1)).isoformat())
        with self.assertRaisesRegex(ValueError,'BUDGET'):self.organism.begin('extra',CTX)
        parent=genetics.founder('g0')
        for i in range(genetics.MAX_GENERATION):parent=genetics.inherit(parent,'g'+str(i+1))
        self.assertEqual(genetics.variants(parent,'exhausted'),[])
        with self.assertRaises(ValueError):genetics.inherit(parent,'excess')

    def test_repeated_target_event_cannot_vote_twice(self):
        self.organism.begin('trial',CTX);_,_,target=self.fixture.round('trial',0)
        self.fixture.stamp+=timedelta(hours=1)
        self.organism.predict('trial',None,(self.fixture.stamp+timedelta(hours=1)).isoformat())
        replay=deepcopy(target);replay['observed_at']=(self.fixture.stamp+timedelta(minutes=1)).isoformat()
        self.fixture.stamp+=timedelta(minutes=2)
        with self.assertRaisesRegex(ValueError,'ALREADY_USED'):self.organism.feedback('trial',replay)

    def test_outcome_cannot_precede_prediction_and_inflight_window_is_locked(self):
        self.organism.begin('trial',CTX);_,_,target=self.fixture.round('trial',0)
        self.fixture.stamp+=timedelta(hours=1);end=(self.fixture.stamp+timedelta(hours=1)).isoformat()
        first=self.organism.predict('trial',None,end)
        self.assertEqual(self.organism.predict('trial',None,end),first)
        with self.assertRaisesRegex(ValueError,'UNSCORED'):self.organism.predict('trial',None,(self.fixture.stamp+timedelta(hours=2)).isoformat())
        old=deepcopy(target);old['source']['event']='new-label-same-past'
        with self.assertRaisesRegex(ValueError,'POSTERIOR'):self.organism.feedback('trial',old)

    def test_interrupted_native_comparison_can_resume_without_extra_outcome(self):
        self.organism.begin('trial',CTX)
        for i in range(3):self.fixture.round('trial',i)
        with patch('federation.organism.compare_native',side_effect=RuntimeError('interrupted')):
            with self.assertRaises(RuntimeError):self.fixture.round('trial',3)
        self.assertEqual(self.organism.status()['scored_outcomes'],4)
        self.fixture.stamp+=timedelta(hours=1)
        self.organism.predict('trial',None,(self.fixture.stamp+timedelta(hours=1)).isoformat())
        self.assertEqual(self.organism.status()['trials']['trial'],'CONFIRMATION')
        self.assertEqual(len(self.organism.load()['trials']['trial']['rounds']),5)

    def test_signed_inheritance_copies_traits_without_evidence_or_credentials(self):
        trial,_=self.complete();packet=self.organism.heredity(self.fixture.config,'birth')
        serialized=json.dumps(packet)
        self.assertNotIn(self.fixture.config['keys']['private_key'],serialized)
        self.assertNotIn('rounds',serialized);self.assertNotIn('target_sha256',serialized)
        child=Organism(Node(self.root/'child','child'),packet,self.fixture.node.node_id,'birth')
        self.assertEqual(child.status()['scored_outcomes'],0)
        self.assertEqual(child.status()['locally_confirmed_changes'],0)
        inherited=child.begin('inherited',CTX)['baseline']
        state=child.load();genome=state['adaptations'][digest(CTX)]['genome']
        self.assertEqual(inherited,digest(genome))
        self.assertEqual(genome['parents'],[trial['candidate']])
        self.assertEqual(genome['generation'],trial['candidates'][trial['candidate']]['generation']+1)
        self.assertEqual(child.status(),Organism(Node(self.root/'child','child'),packet,self.fixture.node.node_id,'birth').status())
        corrupt=deepcopy(packet);corrupt['payload']['founder']['genes']['window']=9
        with self.assertRaises(ValueError):Organism(Node(self.root/'bad','bad'),corrupt,self.fixture.node.node_id,'birth')
        with self.assertRaisesRegex(ValueError,'IDENTITY'):Organism(Node(self.root/'wrong','wrong'),packet,self.fixture.node.node_id,'other')

    def test_signed_packet_still_cannot_override_constitution(self):
        packet=self.organism.heredity(self.fixture.config,'birth')
        packet['payload']['founder']['constitution_sha256']='0'*64
        packet['signature']=sign(packet['payload'],self.fixture.config['keys']['private_key'])
        with self.assertRaisesRegex(ValueError,'CONSTITUTION'):Organism(Node(self.root/'bad','bad'),packet,self.fixture.node.node_id,'birth')

    def test_only_one_active_trial_and_no_hidden_budget_growth(self):
        first=self.organism.begin('trial',CTX)
        self.assertEqual(first,self.organism.begin('trial',CTX))
        with self.assertRaisesRegex(ValueError,'RUNNING'):self.organism.begin('second',CTX)
        with self.assertRaisesRegex(ValueError,'CONFLICT'):self.organism.begin('trial',{**CTX,'regime':'other'})
        with self.organism.lock():
            with self.assertRaises(BlockingIOError):self.organism.begin('locked',CTX)

    def test_full_synthetic_experiment_including_inheritance(self):
        result=run();self.assertEqual(result['status'],'PASS');self.assertTrue(all(result['checks'].values()))


if __name__=='__main__':unittest.main()
