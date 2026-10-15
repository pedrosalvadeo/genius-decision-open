"""Generate fixtures once, before scoring. Existing files are never overwritten."""
import hashlib
import json
from pathlib import Path
import random


def make_cases(seed, split):
    rng = random.Random(seed)
    cases = []
    kinds = ['steady','short','long','recurrent','shift','storage','sensors','mixed']
    for index, kind in enumerate(kinds):
        for load in ('sparse','busy'):
            duration = rng.choice([5,10,15,20])
            spacing = rng.choice([35,45,55]) if load=='sparse' else rng.choice([5,10,15])
            offset = rng.choice([0,5,10,15])
            arrivals = sorted(offset+t+rng.choice([0,0,5]) for t in range(0,600,spacing))
            failures, storage, sensors = [], [], []
            if kind=='short': failures = [[0,rng.choice([25,35,45,55])]]
            if kind=='long': failures = [[0,rng.choice([225,275,325,375])]]
            if kind=='recurrent': failures = [[0,rng.choice([125,145,165])],[300,rng.choice([445,475,505])]]
            if kind=='shift': failures = [[0,rng.choice([35,55,75])],[200,rng.choice([385,425,465])],[550,590]]
            if kind=='storage': storage = [[rng.choice([35,45,55]),rng.choice([155,175,195])]]
            if kind=='sensors': sensors = [[0,rng.choice([45,75,85])],[225,265]]
            if kind=='mixed':
                failures = [[0,rng.choice([185,235,285])],[400,455]]
                storage = [[300,355]]
                sensors = [[505,545]]
            cases.append(dict(id=f'{split}-{index:02}-{kind}-{load}',horizon=1200,duration=duration,
                              arrivals=arrivals,failures=failures,storage=storage,sensors=sensors))
    return cases


def identity(case):
    return hashlib.sha256(json.dumps({k:v for k,v in case.items() if k!='id'},sort_keys=True).encode()).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    previous = root.parent/'regulation'
    old = {identity(case) for name in ('training','evaluation') for case in json.loads((previous/(name+'.json')).read_text())}
    train, evaluation = make_cases(2026101502,'train'),make_cases(2026101503,'eval')
    train_ids, eval_ids = {identity(c) for c in train},{identity(c) for c in evaluation}
    assert not train_ids & eval_ids and not old & (train_ids|eval_ids)
    for name, value in (('training',train),('evaluation',evaluation)):
        with (root/(name+'.json')).open('x') as stream:
            stream.write(json.dumps(value,indent=2)+'\n')


if __name__=='__main__':
    main()
