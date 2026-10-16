"""Three complementary partial twins, queried and composed over local peers."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile

from .core import digest, now
from .experiment import Process
from .world_example import example


def run():
    from genius_twin import registry, stockflow
    started=datetime.now(timezone.utc)
    views=example((started-timedelta(minutes=1)).isoformat(),(started+timedelta(hours=1)).isoformat())
    nodes=[]
    with tempfile.TemporaryDirectory(prefix='genius-partial-world-') as temp:
        try:
            for view in views:
                node=Process(Path(temp)/view['owner'],view['owner'])
                nodes.append(node)
                node.call('/observe-views',dict(records=[view]))
            for node in nodes:
                node.call('/peers',dict(peers=[p.descriptor() for p in nodes if p is not node]))
            def project(node,mode='connected'):
                return node.call('/project-world',dict(world_id='pumping-study',focus=['pump'],mode=mode))
            isolated={node.name:project(node,'isolated') for node in nodes}
            exchanges=[]
            # water receives energy but still lacks the affected community/model.
            exchanges.append(nodes[0].call('/sync-world',dict(node_id='energy')))
            two_views=project(nodes[0])
            exchanges.append(nodes[0].call('/sync-world',dict(node_id='community')))
            connected=project(nodes[0])
            if connected['model'] is None:
                raise RuntimeError('COMPOSITION_INCOMPLETE')
            model=connected['model']
            traces=stockflow.compute_trajectories(model)
            paths={p:[d['stocks']['delivered'] for d in traces[p]['available']['daily']] for p in traces}
            native=registry.evaluate(model)
            if not native['verification']['valid']:
                raise RuntimeError('NATIVE_VERIFICATION_FAILED')
            # A second participant receives and reconstructs the same composite.
            exchanges.append(nodes[2].call('/sync-world',dict(node_id='water')))
            second=project(nodes[2])
            duplicate=nodes[0].call('/sync-world',dict(node_id='community'))
            nodes[1].close()
            offline=nodes[0].call('/sync-world',dict(node_id='energy'))
            cached=project(nodes[0])
            original=nodes[0]
            original.close()
            restored=Process(original.state,original.name,original.credentials)
            nodes.append(restored)
            replay=project(restored)
            checks=dict(
                three_partial_models_incomplete=all(v['model'] is None for v in isolated.values()),
                two_views_still_incomplete=two_views['model'] is None,
                third_view_enables_calculation=connected['status']=='READY_FOR_REVIEW',
                shared_entities_not_duplicated=connected['coverage']['local_entity_mentions']==8 and connected['coverage']['unique_entities']==6,
                upstream_and_affected_in_scope=set(connected['boundary']['required_evaluation_entities'])=={'pump','reserve','delivered','energy','hours','community'},
                restored_route_matches_independent_oracle=paths['restore_supply']==['1/1','1/1','3/1','5/1'],
                waiting_route_matches_independent_oracle=paths['wait']==['1/1']*4,
                native_verified=native['verification']['valid'],
                second_node_reconstructs_same_model=second['model']==model,
                re_relay_does_not_add_views=duplicate['inserted']==0,
                disconnected_peer_keeps_cached_model=offline['status']=='UNAVAILABLE_OR_REJECTED' and cached['model']==model,
                restart_keeps_views_and_model=replay['view_hashes']==connected['view_hashes'] and replay['model']==model,
                probability_remains_unknown=model['law'] is None,
                unmodelled_physical_entity_remains_visible=connected['preparation']['scope_receipt']['review_required'])
            if not all(checks.values()):
                raise RuntimeError('WORLD_EXPERIMENT_CHECK_FAILED')
            return dict(format='genius-distributed-twin-experiment/1',status='PASS',started_at=started.isoformat(),completed_at=now(),
                checks=checks,views=views,isolated=isolated,two_views=two_views,connected=connected,
                exchanges=exchanges,duplicate=duplicate,offline=offline,trajectories=traces,
                native_verification=native['verification'],native_decision=native['canonical_results']['decision'],
                model_sha256=digest(model),
                source_sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))},
                scope='SYNTHETIC_DECLARED_IDENTITIES_AND_DYNAMICS_SAME_OPERATOR_LOOPBACK',
                physical_actions=False,empirical_validation='NOT_ASSESSED',life_sustainment_effect='UNMEASURED',
                state_cleanup='TEMPORARY_LAB_ONLY')
        finally:
            for node in nodes:node.close()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    if args.out.exists():parser.error('Output must not exist')
    report=run()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    with args.out.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps(dict(status=report['status'],checks=report['checks'],model_sha256=report['model_sha256'])))


if __name__=='__main__':main()
