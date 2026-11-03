"""Run separate FastAPI test suites in fresh interpreter processes.

Separate processes avoid fixture/lifespan cross-suite interference on some hosts.
Always report exact measured outcomes and timeouts; no false success.
"""
from pathlib import Path
import datetime as dt
import os
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parent
SUITES=[
 ('Round 1 scenario endpoints','tests/test_round1_demo.py'),
 ('Core backend + security','tests/test_core.py'),
 ('Hardware profile preparation','tests/test_onsite_preparation.py'),
 ('V8 event preparation','tests/test_v8_preparation.py'),
]

def main():
    lines=['ColdChain V8 Python test results (separate isolated suites)',
           'UTC: '+dt.datetime.now(dt.timezone.utc).isoformat(),
           'No physical ESP32 board, relay, alert delivery, or Windows BAT was exercised.','']
    total_failed=0; total_passed=0
    for label,path in SUITES:
        print('\n'+'='*56+'\n'+label+'\n'+'='*56,flush=True)
        start=time.monotonic()
        log=ROOT/'report'/('test_'+path.replace('tests/','').replace('.py','.log'))
        log.parent.mkdir(exist_ok=True)
        output=''
        try:
            with log.open('w',encoding='utf-8') as log_file:
                process=subprocess.Popen([sys.executable,'-m','pytest','-q',path],cwd=ROOT,
                                         stdout=log_file,stderr=subprocess.STDOUT,
                                         env={**os.environ,'PYTEST_DISABLE_PLUGIN_AUTOLOAD':'1',
                                              'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1',
                                              'MKL_NUM_THREADS':'1'})
                deadline=time.monotonic()+75
                timed_out=False
                while process.poll() is None and time.monotonic()<deadline:
                    time.sleep(.2)
                if process.poll() is None:
                    timed_out=True
                    process.kill()
                    try:process.wait(timeout=6)
                    except subprocess.TimeoutExpired:pass
            output=log.read_text(encoding='utf-8',errors='replace')
            if timed_out:output+='\n[TIMEOUT] Suite exceeded 75 seconds.'
            passed=not timed_out and process.returncode==0
        except OSError as exc:
            output='[RUNNER ERROR] '+str(exc)
            passed=False
        elapsed=time.monotonic()-start
        print(output,flush=True)
        status='PASS' if passed else 'FAIL'
        lines.extend([f'[{status}] {label} ({elapsed:.1f}s)', output.rstrip(),''])
        if passed:total_passed+=1
        else:total_failed+=1
    lines.append(f'Suite results: {total_passed}/{len(SUITES)} passed; {total_failed} failed.')
    report=ROOT/'report'/'LOCAL_TEST_RUN.txt'; report.parent.mkdir(exist_ok=True)
    report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print('\n'+lines[-1])
    print('Saved report:',report)
    return 1 if total_failed else 0
if __name__=='__main__':raise SystemExit(main())
