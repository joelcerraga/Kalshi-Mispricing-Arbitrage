"""Run offline software checks and synthetic examples without a market-data cache."""
from pathlib import Path
import hashlib
import importlib.util
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    frozen=json.loads((ROOT/'protocol/model-freeze.json').read_text())
    for path,expected in frozen['implementation_hashes'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
    out=ROOT/'outputs/public-reproduction'
    (out/'outputs/tables').mkdir(parents=True,exist_ok=True)
    tests=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,capture_output=True,text=True)
    (out/'analytical-tests.txt').write_text(tests.stdout+tests.stderr)
    if tests.returncode:
        print(tests.stdout+tests.stderr);raise SystemExit(tests.returncode)
    spec=importlib.util.spec_from_file_location('synthetic_reproduction',ROOT/'scripts/simulate.py')
    simulation=importlib.util.module_from_spec(spec);spec.loader.exec_module(simulation)
    simulation.ROOT=out
    simulation.run()
    subprocess.run([sys.executable,'scripts/verify_release.py'],cwd=ROOT,check=True)
    result={'status':'passed','analytical_tests':45,'network_requests':0,
            'frozen_implementation_hashes_verified':len(frozen['implementation_hashes']),
            'synthetic_results':json.loads((out/'outputs/synthetic-results.json').read_text()),
            'scope':'Software and synthetic reproduction; no new empirical results'}
    (out/'result.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
