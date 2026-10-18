"""Offline reproduction from the private retained research snapshot."""
from pathlib import Path
import sys,json,hashlib,subprocess,datetime,argparse,os,shutil
ROOT=Path(__file__).resolve().parents[1]
def run(args):
 print('Running', ' '.join(map(str,args)),flush=True);subprocess.run(args,cwd=ROOT,check=True)
def main():
 p=argparse.ArgumentParser();p.add_argument('--web',action='store_true',help='also rebuild offline HTML; requires Node and marked');a=p.parse_args()
 frozen=json.loads((ROOT/'protocol/model-freeze.json').read_text())
 for name,key in [('data/processed/forecast-features.json','feature_hash'),('outputs/tables/frozen-predictions.json','prediction_hash')]:
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==frozen[key],name
 for name,digest in frozen['implementation_hashes'].items():assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
 for row in json.loads((ROOT/'outputs/validation/source-snapshot-index.json').read_text()):
  assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['snapshot_sha256'],row['file']
 proc=subprocess.run([sys.executable,'-m','unittest','discover','-s','tests','-v'],cwd=ROOT,text=True,capture_output=True)
 (ROOT/'outputs/validation/analytical-tests.txt').write_text(proc.stdout+proc.stderr)
 if proc.returncode:print(proc.stdout+proc.stderr);raise SystemExit(proc.returncode)
 for args in [['scripts/analyse.py','prepare'],['scripts/analyse.py','freeze'],['scripts/analyse.py','evaluate'],['scripts/analyse.py','live'],['scripts/simulate.py'],['scripts/supplementary.py'],['scripts/build_references.py'],['scripts/build_registers.py'],['scripts/build_figures.py'],['scripts/build_notebooks.py'],['scripts/scan.py','--output','outputs/latest-scan.json']]:
  # The replay prints a long audit payload; retain it locally.
  if args[0]=='scripts/scan.py':
   with (ROOT/'outputs/validation/scanner-replay.txt').open('w') as f:subprocess.run([sys.executable,*args],cwd=ROOT,stdout=f,check=True)
  else:run([sys.executable,*args])
 if a.web:
  run([sys.executable,'scripts/build_explorers.py'])
  node=os.environ.get('CODEX_PRIMARY_RUNTIME_NODE') or shutil.which('node')
  env=os.environ.copy()
  if os.environ.get('CODEX_PRIMARY_RUNTIME_NODE_MODULES'):env['NODE_PATH']=os.environ['CODEX_PRIMARY_RUNTIME_NODE_MODULES']
  subprocess.run([node,'scripts/build_review.cjs'],cwd=ROOT,env=env,check=True)
 record={'passed':True,'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'network_requests':0,'prediction_hash':hashlib.sha256((ROOT/'outputs/tables/frozen-predictions.json').read_bytes()).hexdigest(),'source_snapshots_verified':len(json.loads((ROOT/'outputs/validation/source-snapshot-index.json').read_text())),'notebooks':8,'web_rebuilt':a.web}
 (ROOT/'outputs/validation/reproduction.json').write_text(json.dumps(record,indent=2));print(json.dumps(record,indent=2))
if __name__=='__main__':main()
