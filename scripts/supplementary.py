from pathlib import Path
import sys,json,datetime,hashlib,collections,csv
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from kalshi_engine.client import ROOT
from kalshi_engine.microstructure import execution_fee,FeePolicy
from kalshi_engine.arbitrage import partition_audit,temperature_payoff_states

features=json.loads((ROOT/'data/processed/forecast-features.json').read_text())
rows=[]
for e in features:
 if e['hour']!=12:continue
 for side,asks,payout in [('yes',e['asks'],1),('no',[1-b for b in e['bids']],len(e['p'])-1)]:
  cost=sum(asks);fee=sum(float(execution_fee([(str(a),'1')])) for a in asks)
  rows.append(dict(event=e['event'],series=e['series'],date=e['date'],phase=e['phase'],source=e['source'],side=side,gross_gap=payout-cost,net_gap_scenario=payout-cost-fee,fee_scenario=fee,midpoint_sum=e['midpoint_sum'],interpretation='conditional integer-outcome basket; hourly quote-only, no depth; current fee scenario'))
pd.DataFrame(rows).to_csv(ROOT/'outputs/tables/historical-coherence.csv',index=False)
meta=json.loads((ROOT/'data/processed/metadata.json').read_text());audits=[]
for series,v in meta.items():
 events=collections.defaultdict(list)
 for m in v['markets']+v['open_markets']:events[m['event_ticker']].append(m)
 for event,ms in events.items():
  a=partition_audit(ms);Y=temperature_payoff_states(ms)
  audits.append(dict(event=event,series=series,integer_partition=a['valid'],full_precision_exhaustive=a['full_precision_exhaustive'],ordinary_payoff_states=len(Y),exceptional=a['exceptional_fair_value'],unique_binary_winner=sum(m.get('result')=='yes' for m in ms)==1))
pd.DataFrame(audits).to_csv(ROOT/'outputs/tables/contract-audit.csv',index=False)
live=pd.read_csv(ROOT/'outputs/tables/live-microstructure.csv');curves=[]
for ticker,g in live.groupby('ticker'):
 g=g.sort_values('round');g['next_mid_change']=g.midpoint.shift(-1)-g.midpoint
 curves.extend(g[['ticker','round','imbalance','next_mid_change']].dropna().to_dict('records'))
df=pd.DataFrame(curves);df.to_csv(ROOT/'outputs/tables/imbalance-diagnostics.csv',index=False)
# A regenerated index is derived from stored records, not a substitute HTTP source.
index=[]
for p in sorted((ROOT/'data/raw').glob('*.json')):
 o=json.loads(p.read_text());body=o['body']
 index.append(dict(file=str(p.relative_to(ROOT)),url=o['url'],request_started_utc=o['request_started_utc'],response_received_utc=o['response_received_utc'],snapshot_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),canonical_payload_sha256=hashlib.sha256(json.dumps(body,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),observed_wire_sha256=o['sha256']))
(ROOT/'outputs/validation/source-snapshot-index.json').write_text(json.dumps(index,indent=2))
old=[json.loads(x)['file'] for x in (ROOT/'data/raw/manifest.jsonl').read_text().splitlines()]
missing=sorted(set(x['file'] for x in index)-set(old))
summary={'historical_noon_events':len(rows)//2,'gross_positive_quote_baskets':sum(r['gross_gap']>1e-8 for r in rows),'net_positive_current_fee_scenario':sum(r['net_gap_scenario']>1e-8 for r in rows),'source_snapshots':len(index),'parallel_manifest_missing_entries':len(missing),'recovered_index_files':missing,'book_payload_hashes':len(set(x['canonical_payload_sha256'] for x in index if '/markets/orderbooks?' in x['url'])),'integer_partition_events':sum(x['integer_partition'] for x in audits),'continuous_partition_events':sum(x['full_precision_exhaustive'] for x in audits),'snapshot_imbalance_correlation':float(df[['imbalance','next_mid_change']].corr().iloc[0,1]) if df.next_mid_change.std()>0 else None,'interpretation':'Historical current-fee scenarios and short-session imbalance are descriptive; no fill or causal identification.'}
(ROOT/'outputs/supplementary-results.json').write_text(json.dumps(summary,indent=2,allow_nan=False))
print(json.dumps(summary,indent=2))
