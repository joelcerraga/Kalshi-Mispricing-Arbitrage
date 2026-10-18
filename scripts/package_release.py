"""Create the reviewable GitHub release candidate with verified archive members."""
from pathlib import Path
import argparse
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def included(p,manifest):
    rel=p.relative_to(ROOT)
    if not p.is_file() or p==manifest:return False
    if any(x in {'.git','__pycache__','node_modules','.venv','.ipynb_checkpoints','public-reproduction'} for x in rel.parts):return False
    if 'private-archive' in rel.parts or p.name=='kalshi-permission-request.txt':return False
    return p.suffix not in {'.pyc','.partial','.zip','.log','.aux','.toc','.lof','.lot','.loe','.loc'}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--output',required=True);args=ap.parse_args()
    target=Path(args.output).resolve();target.parent.mkdir(parents=True,exist_ok=True)
    manifest=ROOT/'docs/release-manifest.json'
    paths=sorted(p for p in ROOT.rglob('*') if included(p,manifest))
    entries=[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    manifest.write_text(json.dumps({'stage':json.loads((ROOT/'docs/release-status.json').read_text())['stage'],'files':entries},indent=2))
    paths.append(manifest)
    staging=target.with_suffix('.zip.partial')
    with zipfile.ZipFile(staging,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in paths:z.write(p,Path(ROOT.name)/p.relative_to(ROOT))
    with zipfile.ZipFile(staging) as z:
        assert z.testzip() is None
        for item in entries:
            assert hashlib.sha256(z.read(ROOT.name+'/'+item['path'])).hexdigest()==item['sha256']
    staging.replace(target)
    print(json.dumps({'archive':str(target),'files':len(paths),'bytes':target.stat().st_size,'members_verified':True,'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))


if __name__=='__main__':main()
