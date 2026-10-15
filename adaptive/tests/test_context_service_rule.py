"""The service port preserves the previously published operator v1 rule."""
import random
import unittest
from genius_adaptive import contextual
from observers import strategies


class RuleParity(unittest.TestCase):
    def test_each_prefix_matches_frozen_operator_including_regime_changes(self):
        rng=random.Random(17)
        sequences=[[50]*40,[10,100]*20,[1]*12+[1000]*28,[0,1000000]*20,
                   [rng.randrange(10000) for _ in range(40)]]
        for values in sequences:
            plan=dict(baseline=50,max_underprediction=50,warmup_count=10,scored_count=30)
            history=[]
            for value in values:
                self.assertEqual(contextual.predict(history,plan),strategies.predict(history,plan))
                history.append(dict(**contextual.predict(history,plan),value=value))
            report=contextual.report(history,plan)
            self.assertEqual(report['comparison']['adaptive']['count'],30)


if __name__=='__main__':unittest.main()
