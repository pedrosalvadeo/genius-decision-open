"""Run stdlib tests and record exact public-API inputs/results for reproducibility.

From the handoff root:
    PYTHONPATH=kernel python kernel/tests/run_suite.py

This runner is test instrumentation, not kernel code. It records the byte input
actually passed to each public call and the actual return; no PASS is inferred
from case design or from an earlier run.
"""
from __future__ import annotations
import hashlib
import importlib
import json
import platform
import re
import shutil
import sys
import time
import unittest
from pathlib import Path

TESTS=Path(__file__).resolve().parent
ROOT=TESTS.parents[1]
ARTIFACTS=TESTS/'executed'
REPORT=TESTS/'TEST_RESULTS.json'


class RecordingResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.records=[]
        self.current=None
    def startTest(self,test):
        super().startTest(test)
        self.current={'test':test.id(),'status':'RUNNING','calls':[]}
        self.records.append(self.current)
    def addSuccess(self,test):
        super().addSuccess(test); self.current['status']='PASS'
    def addFailure(self,test,err):
        super().addFailure(test,err); self.current['status']='FAIL'
        self.current['error']=self._exc_info_to_string(err,test)
    def addError(self,test,err):
        super().addError(test,err); self.current['status']='ERROR'
        self.current['error']=self._exc_info_to_string(err,test)
    def addSubTest(self,test,subtest,err):
        super().addSubTest(test,subtest,err)
        if err is not None:
            self.current['status']='FAIL' if issubclass(err[0],test.failureException) else 'ERROR'
            self.current.setdefault('subtest_errors',[]).append(self._exc_info_to_string(err,test))
    def addSkip(self,test,reason):
        super().addSkip(test,reason); self.current['status']='SKIP'; self.current['reason']=reason


def dump(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=True,indent=2)+'\n',encoding='utf-8')


def main():
    sys.path.insert(0,str(ROOT/'kernel'))
    suite=unittest.defaultTestLoader.discover(str(TESTS))
    # A shared result instance also gives wrappers the currently running test.
    runner=unittest.TextTestRunner(verbosity=2,resultclass=RecordingResult)
    result=runner._makeResult()
    result.failfast=False; result.buffer=False
    if ARTIFACTS.exists(): shutil.rmtree(ARTIFACTS)
    ARTIFACTS.mkdir()
    def instrument(operation,fn):
        def invoke(b,*args,**kwargs):
            rec=result.current
            ordinal=len(rec['calls'])+1
            folder=ARTIFACTS/rec['test']/f'{ordinal:03}_{operation}'
            folder.mkdir(parents=True)
            (folder/'input.json').write_bytes(b)
            call={'operation':operation,'input_sha256':hashlib.sha256(b).hexdigest(),
                  'artifact':str(folder.relative_to(ROOT))}
            if args: dump(folder/'candidate.json',args[0])
            if kwargs.get('limits') is not None: dump(folder/'limits.json',kwargs['limits'])
            rec['calls'].append(call)
            try:
                answer=fn(b,*args,**kwargs)
            except Exception as exc:
                call['raised']=type(exc).__name__+': '+str(exc)
                raise
            dump(folder/('result.json' if operation=='evaluate' else 'verification.json'),answer)
            return answer
        return invoke
    for module in list(sys.modules.values()):
        filename=getattr(module,'__file__',None)
        if filename and Path(filename).resolve().parent==TESTS and Path(filename).name.startswith('test_'):
            for name in ['evaluate','verify_result','verify_decisive_certificate']:
                if hasattr(module,name): setattr(module,name,instrument(name,getattr(module,name)))
    start=time.monotonic()
    result.startTestRun()
    suite(result)
    result.stopTestRun()
    result.printErrors()
    elapsed=time.monotonic()-start
    index=json.loads((ROOT/'baseline/GENIUS_PHASE_1_HANDOFF/GENIUS_PROGRAM/conformance/CASE_INDEX.json').read_text())
    cases=[]
    for case in index['cases']:
        label=case['id'].replace('-','')
        matched=[r for r in result.records if re.search(r'\btest_'+label+r'_',r['test'])]
        cases.append({'case':case['id'],'scope':case['scope'],
                      'coverage':'FP1_PUBLIC_WIRE' if case['scope']=='FP1_FINITE_EXACT' else 'MATHEMATICAL_PROBE_ONLY_OUTSIDE_FP1',
                      'tests':[r['test'] for r in matched],
                      'status':'PASS' if matched and all(r['status']=='PASS' for r in matched) else ('UNMAPPED' if not matched else 'NOT_PASS')})
    report={'format':'GENIUS_F2_TEST_EXECUTION_V1','python':platform.python_version(),
            'command':'PYTHONPATH=kernel python kernel/tests/run_suite.py',
            'elapsed_seconds':round(elapsed,6),'tests_run':result.testsRun,
            'failures':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),
            'successful':result.wasSuccessful(),'case_coverage':cases,'tests':result.records}
    dump(REPORT,report)
    print(f'Ran {result.testsRun} tests in {elapsed:.3f}s: '+('OK' if result.wasSuccessful() else f'{len(result.failures)} failures, {len(result.errors)} errors'),file=sys.stderr)
    print(f'Execution record: {REPORT.relative_to(ROOT)}',file=sys.stderr)
    return 0 if result.wasSuccessful() else 1


if __name__=='__main__': raise SystemExit(main())
