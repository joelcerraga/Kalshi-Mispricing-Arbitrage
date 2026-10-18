"""Public GET-only Kalshi client with immutable, timestamped source snapshots."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError
import hashlib, json, time, threading

BASE = "https://external-api.kalshi.com/trade-api/v2"
ROOT = Path(__file__).resolve().parents[1]
_LOCK = threading.Lock()

def utcnow():
    return datetime.now(timezone.utc).isoformat()

class PublicClient:
    def __init__(self, root=ROOT, base=BASE, timeout=30):
        self.root, self.base, self.timeout = Path(root), base, timeout
        (self.root / 'data/raw').mkdir(parents=True, exist_ok=True)

    def get(self, path, params=None, *, cache=True):
        if not path.startswith('/') or any(x in path for x in ('portfolio', 'orders', 'api_keys')):
            raise ValueError('Public research endpoints only')
        url = self.base + path
        if params:
            url += '?' + urlencode({k:v for k,v in params.items() if v is not None}, doseq=True)
        return self.download(url, cache=cache)

    def download(self, url, *, cache=True):
        key = hashlib.sha256(url.encode()).hexdigest()[:24]
        target = self.root / 'data/raw' / (key + '.json')
        if cache and target.exists():
            return json.loads(target.read_text())['body']
        for attempt in range(4):
            started = utcnow(); t0 = time.monotonic()
            try:
                req = Request(url, headers={'User-Agent':'KalshiMicrostructureResearch/0.1 (public read-only research)'})
                with urlopen(req, timeout=self.timeout) as r:
                    raw = r.read(); status = r.status
                    headers = {k:v for k,v in r.headers.items() if k.lower() in ('date','age','content-type','etag','cache-control')}
                try: body = json.loads(raw)
                except (ValueError, UnicodeError): body = raw.decode('utf-8',errors='replace')
                finished = utcnow()
                record = dict(url=url,request_started_utc=started,response_received_utc=finished,
                              elapsed_seconds=round(time.monotonic()-t0,6),http_status=status,
                              headers=headers,sha256=hashlib.sha256(raw).hexdigest(),body=body)
                if not cache: target = target.with_name(key+'-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')+'.json')
                target.write_text(json.dumps(record,ensure_ascii=False,indent=2))
                with _LOCK:
                    with (self.root/'data/raw/manifest.jsonl').open('a') as f:
                        f.write(json.dumps({k:v for k,v in record.items() if k!='body'} | {'file':str(target.relative_to(self.root))})+'\n')
                return body
            except (HTTPError,URLError,TimeoutError) as e:
                code=getattr(e,'code',None)
                if code is not None and code not in (429,500,502,503,504):
                    raise
                if attempt==3: raise
                time.sleep(min(2**attempt,8))

    def paginated(self, path, params, field, max_pages=30):
        out=[]; cursor=None; seen=set()
        for _ in range(max_pages):
            data=self.get(path,params | {'cursor':cursor})
            out.extend(data[field]); cursor=data.get('cursor')
            if not cursor: return out
            if cursor in seen: raise ValueError('Repeated pagination cursor')
            seen.add(cursor)
        raise RuntimeError('Pagination limit reached: refusing silent truncation')
