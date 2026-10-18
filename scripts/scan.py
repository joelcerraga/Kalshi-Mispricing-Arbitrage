"""Read-only scanner. Default replays the recorded sample; --live makes public GETs."""
from pathlib import Path
import sys,json,argparse,datetime,collections
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kalshi_engine.client import ROOT,PublicClient,utcnow
from kalshi_engine.microstructure import Book,FeePolicy
from kalshi_engine.arbitrage import partition_audit,temperature_payoff_states,basket

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--series',default='KXHIGHNY');p.add_argument('--quantity',type=float,default=10);p.add_argument('--live',action='store_true');p.add_argument('--output');a=p.parse_args()
 if a.series not in ['KXHIGHNY','KXHIGHCHI','KXHIGHMIA']:p.error('This research adapter supports the three audited temperature series only.')
 started=utcnow()
 if a.live:
  c=PublicClient();series=c.get('/series/'+a.series,cache=False)['series'];r=c.get('/markets',{'series_ticker':a.series,'status':'open','limit':1000},cache=False)
  if r.get('cursor'):raise RuntimeError('Roster exceeds one page; refusing an incomplete scan')
  markets=r['markets'];tickers=[m['ticker'] for m in markets]
  if not tickers or len(tickers)>100:raise RuntimeError('Expected 1–100 markets in this adapter')
  b=c.get('/markets/orderbooks',{'tickers':tickers},cache=False)['orderbooks'];finished=utcnow()
 else:
  d=json.loads((ROOT/'data/processed/metadata.json').read_text())[a.series];series=d['series'];markets=d['open_markets']
  r=json.loads((ROOT/'data/processed/books.json').read_text())[-1];started=r['request_started'];finished=r['response_received'];b=r['orderbooks']
 books={x['ticker']:Book.from_payload(x) for x in b};policy=FeePolicy.from_series(series);groups=collections.defaultdict(list)
 for m in markets:groups[m['event_ticker']].append(m)
 span=(datetime.datetime.fromisoformat(finished)-datetime.datetime.fromisoformat(started)).total_seconds();rows=[]
 for event,ms in groups.items():
  audit=partition_audit(ms)
  if not audit['valid']:rows.append({'event':event,'status':'unsupported_partition','audit':audit});continue
  evbooks=[books[t] for t in audit['tickers']]
  scenarios={side:basket(evbooks,side,a.quantity,policy,partition_verified=True,exceptional=audit['exceptional_fair_value'],observation_span=span) for side in ['yes','no']}
  rows.append({'event':event,'audit':audit,'conditional_integer_basket_scenarios':scenarios,
               'ordinary_full_precision_yes_states':temperature_payoff_states(ms).tolist(),
               'execution_certificate':False,'reason':'No atomic exchange timestamp or fills; full settlement contingency set is unverified.'})
 out={'mode':'public REST observation' if a.live else 'recorded replay','series':a.series,'request_started':started,'response_received':finished,'quantity':a.quantity,'results':rows,'orders_submitted':0}
 dest=Path(a.output) if a.output else ROOT/'outputs/latest-scan.json';dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(json.dumps(out,indent=2));print(json.dumps(out,indent=2))
if __name__=='__main__':main()
