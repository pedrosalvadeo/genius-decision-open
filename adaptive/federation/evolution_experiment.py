"""Reproducible local evolutionary experiment with disclosed synthetic outcomes."""
import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile

from .core import Node, digest
from .experiment import observation
from .organism import Organism
from .network_protocol import generate, identity

CTX = dict(system='synthetic-sequence', variable='requirement', unit='declared_unit',
           regime='rising-sequence-v1', data_kind='synthetic')


class Fixture:
    def __init__(self, directory):
        keys=generate(); self.config=dict(node_id=identity(keys['public_key']),keys=keys)
        self.stamp=datetime(2026,10,16,12,tzinfo=timezone.utc)
        self.node=Node(directory,self.config['node_id'],lambda:self.stamp.isoformat())
        self.organism=Organism(self.node)

    def round(self, trial_id, index, target=None):
        start=datetime(2026,10,16,12,tzinfo=timezone.utc)+timedelta(hours=index)
        self.stamp=start
        expire=(start+timedelta(days=1)).isoformat()
        rows=[observation(CTX,'fixture:inputs',f'input-{index}-{i}',index*100+value,
            observed_at=(start-timedelta(minutes=3-i)).isoformat(),valid_until=expire)
            for i,value in enumerate((10,20,30))]
        self.node.ingest(rows)
        forecast=self.organism.predict(trial_id,(start+timedelta(minutes=1)).isoformat(),
                                       (start+timedelta(minutes=10)).isoformat())
        self.stamp=start+timedelta(minutes=2)
        target=observation(CTX,'fixture:outcomes',f'outcome-{index}',index*100+30 if target is None else target,
            observed_at=self.stamp.isoformat(),valid_until=expire)
        return forecast,self.organism.feedback(trial_id,target),target


def run():
    with tempfile.TemporaryDirectory(prefix='genius-genetics-') as temp:
        root=Path(temp); helpful=Fixture(root/'helpful'); harmful=Fixture(root/'harmful')
        trials={}
        for label,fixture in (('confirmed',helpful),('rejected',harmful)):
            fixture.organism.begin('generation-one',CTX)
            for index in range(8):
                # The second environment changes after nomination; the candidate must fail confirmation.
                target=index*100+10 if label=='rejected' and index>=4 else None
                _,trial,_=fixture.round('generation-one',index,target)
            trials[label]=trial
        packet=helpful.organism.heredity(helpful.config,'demonstration-birth')
        child=Organism(Node(root/'child','synthetic-child'),packet,helpful.node.node_id,'demonstration-birth')
        expression=child.begin('inherited-baseline',CTX)
        selected=trials['confirmed']['candidates'][trials['confirmed']['candidate']]
        inherited=expression['candidates'][expression['baseline']]
        checks=dict(variant_confirmed=trials['confirmed']['status']=='ADOPTED',
            degraded_variant_rejected=trials['rejected']['status']=='REJECTED',
            native_selection_verified=trials['confirmed']['confirmation_native']['verification']['valid'],
            child_inherits_selected_genes=inherited['genes']==selected['genes'],
            child_records_parent=digest(selected) in inherited['parents'],
            child_does_not_inherit_scores=child.status()['scored_outcomes']==0,
            no_life_probability_invented=child.status()['life_sustainment_probability'] is None)
        if not all(checks.values()): raise RuntimeError('EVOLUTION_EXPERIMENT_FAILED')
        return dict(format='genius-evolution-experiment/1',status='PASS',checks=checks,trials=trials,
            inherited_genome=inherited,child_status=child.status(),
            scope='LOCAL_SYNTHETIC_NON_BLIND_OPERATIONAL_PREDICTION',
            generalization='NOT_ESTABLISHED',wellbeing_effect='UNMEASURED',physical_actions=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args();result=run();args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x') as stream:json.dump(result,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(status=result['status'],checks=result['checks'])))


if __name__=='__main__':main()
