"""Historical features, frozen forecasts, chronological scoring and live book audit."""
from pathlib import Path
import sys,json,hashlib,argparse,datetime,collections
from zoneinfo import ZoneInfo
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from kalshi_engine.client import ROOT,utcnow
from kalshi_engine.microstructure import Book,FeePolicy,sweep
from kalshi_engine.arbitrage import partition_audit,temperature_payoff_states,coherence,basket,statewise_portfolio
from kalshi_engine.probability import normalise,calibrate,fit_temperature,scores,paired_block_interval

def save(name,obj):
    (ROOT/name).parent.mkdir(parents=True,exist_ok=True)
    (ROOT/name).write_text(json.dumps(obj,indent=2,allow_nan=False))
def read(name):return json.loads((ROOT/name).read_text())
def digest(p):return hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
def edate(t):return datetime.datetime.strptime(t.split('-')[1],'%y%b%d').date().isoformat()
def phase(date):return 'development' if date<='2026-09-10' else ('validation' if date<='2026-09-28' else 'test')
def quote(c,side):
    x=c.get(side,{});v=x.get('close_dollars',x.get('close'))
    if v is None:return None
    if not isinstance(v,str):raise ValueError('Unknown quote schema: expected decimal-dollar string')
    return float(v)

def prepare():
    meta=read('data/processed/metadata.json');candles=read('data/processed/candles.json')
    features=[];labels=[];audit=[];quotes=[]
    for series,v in meta.items():
        groups=collections.defaultdict(list)
        for m in v['markets']:groups[m['event_ticker']].append(m)
        for event,ms in sorted(groups.items()):
            date=edate(event);pa=partition_audit(ms);lookup={m['ticker']:m for m in ms}
            tickers=pa.get('tickers',sorted(lookup));reason=None
            if not pa['valid']:reason='invalid_partition'
            outcomes=[lookup[t].get('result') for t in tickers]
            if any(x not in ('yes','no') for x in outcomes) or outcomes.count('yes')!=1:reason='non_unique_binary_resolution'
            zone='America/Chicago' if series=='KXHIGHCHI' else 'America/New_York'
            rules=' '.join(m.get('rules_primary','') for m in ms)
            source='Weather Company' if 'Weather Company' in rules else ('NWS' if 'National Weather Service' in rules else 'other')
            for hour in [9,12,15]:
                cutoff=int(datetime.datetime.fromisoformat(date).replace(hour=hour,tzinfo=ZoneInfo(zone)).timestamp())
                bids=[];asks=[];used=[];why=reason
                for t in tickers:
                    cs=[c for c in candles.get(t,[]) if c['end_period_ts']<=cutoff]
                    c=max(cs,key=lambda x:x['end_period_ts']) if cs else None
                    if c is None or c['end_period_ts']!=cutoff:why=why or 'missing_exact_completed_hour';break
                    b,a=quote(c,'yes_bid'),quote(c,'yes_ask')
                    if b is None or a is None or not 0<=b<=a<=1:why=why or 'invalid_or_missing_quote';break
                    bids.append(b);asks.append(a);used.append(c['end_period_ts'])
                    quotes.append(dict(event=event,series=series,date=date,local_hour=hour,ticker=t,bid=b,ask=a,spread=a-b,midpoint=(a+b)/2,end_period_ts=c['end_period_ts'],cutoff_ts=cutoff))
                audit.append(dict(event=event,series=series,date=date,hour=hour,phase=phase(date),status=why or 'accepted',source=source))
                if why:continue
                p=normalise((np.array(bids)+asks)/2)
                features.append(dict(event=event,series=series,date=date,hour=hour,phase=phase(date),tickers=tickers,cutoff_ts=cutoff,feature_timestamps=used,p=p.tolist(),bids=bids,asks=asks,source=source,exceptional=pa['exceptional_fair_value'],**coherence(bids,asks)))
                labels.append(dict(event=event,hour=hour,winner=outcomes.index('yes')))
    save('data/processed/forecast-features.json',features);save('data/processed/outcomes.json',labels)
    pd.DataFrame(audit).to_csv(ROOT/'outputs/tables/coverage.csv',index=False)
    pd.DataFrame(quotes).to_csv(ROOT/'outputs/tables/historical-quotes.csv',index=False)
    print(pd.DataFrame(audit).groupby(['hour','phase','status']).size().to_string())

def freeze():
    f=read('data/processed/forecast-features.json');l={(x['event'],x['hour']):x['winner'] for x in read('data/processed/outcomes.json')}
    development=[e|{'winner':l[(e['event'],e['hour'])]} for e in f if e['hour']==12 and e['phase']=='development']
    validation=[e|{'winner':l[(e['event'],e['hour'])]} for e in f if e['hour']==12 and e['phase']=='validation']
    if len(development)<30 or not validation:raise RuntimeError('Insufficient model-development data')
    fit=fit_temperature(development);t=fit['temperature']
    loss=lambda temp:float(np.mean([scores(calibrate(e['p'],temp),e['winner'])['log_loss'] for e in validation]))
    baseline=loss(1);candidate=loss(t);chosen=t if candidate<baseline-1e-12 else 1.
    config=fit|dict(frozen_utc=utcnow(),chosen_temperature=chosen,validation_baseline_loss=baseline,validation_candidate_loss=candidate,development_events=len(development),validation_events=len(validation),feature_hash=digest('data/processed/forecast-features.json'),protocol_hash=digest('protocol/01_research_design.md'),selection='minimum validation multiclass log loss; baseline wins ties',eps=1e-4,temperature_bounds=[.25,4],test_scores_inspected=False)
    config['implementation_hashes']={p:digest(p) for p in ['kalshi_engine/probability.py','scripts/analyse.py','protocol/A01_api_and_contract_audit.md']}
    predictions=[e|{'calibrated_p':calibrate(e['p'],chosen).tolist(),'candidate_p':calibrate(e['p'],t).tolist()} for e in f]
    if (ROOT/'protocol/model-freeze.json').exists():
        old=read('protocol/model-freeze.json')
        if old['feature_hash']!=config['feature_hash'] or abs(old['chosen_temperature']-chosen)>1e-8:raise RuntimeError('Frozen design changed; add an amendment first')
        print('Existing model freeze verified');return
    save('outputs/tables/frozen-predictions.json',predictions)
    config['prediction_hash']=digest('outputs/tables/frozen-predictions.json')
    save('protocol/model-freeze.json',config);print(json.dumps(config,indent=2))

def evaluate():
    freeze=read('protocol/model-freeze.json');assert freeze['prediction_hash']==digest('outputs/tables/frozen-predictions.json')
    pred=read('outputs/tables/frozen-predictions.json');labels={(x['event'],x['hour']):x['winner'] for x in read('data/processed/outcomes.json')}
    rows=[];trades=[]
    for e in pred:
        w=labels[(e['event'],e['hour'])]
        for model,key in [('baseline','p'),('calibrated','calibrated_p'),('candidate','candidate_p')]:
            rows.append({k:e[k] for k in ('event','date','hour','series','phase','source')}|dict(model=model,**scores(e[key],w)))
        if e['hour']==12 and e['phase']=='test':
            edges=[]
            for j,p in enumerate(e['calibrated_p']):
                for side,a,prob in [('yes',e['asks'][j],p),('no',1-e['bids'][j],1-p)]:
                    cost=a+.07*a*(1-a);edges.append((prob-cost,j,side,a,cost))
            edge,j,side,a,cost=max(edges)
            if edge>.02:
                payout=float((j==w) if side=='yes' else (j!=w))
                trades.append(dict(event=e['event'],date=e['date'],series=e['series'],side=side,ticker=e['tickers'][j],model_edge=edge,ask=a,cost_scenario=cost,payout=payout,pnl_scenario=payout-cost,interpretation='hypothetical candle-ask diagnostic; no historical fills or depth; current raw fee scenario'))
    df=pd.DataFrame(rows);df.to_csv(ROOT/'outputs/tables/probability-scores.csv',index=False);save('outputs/tables/value-diagnostics.json',trades)
    result={'model':freeze,'scores':df.groupby(['hour','phase','model'])[['log_loss','brier']].mean().reset_index().to_dict('records'),'counts':df.groupby(['hour','phase','model']).size().reset_index(name='n').to_dict('records')}
    intervals=[]
    for hour in [9,12,15]:
        dd=df[(df.hour==hour)&(df.phase=='test')]
        for model in ['calibrated','candidate']:
            for metric in ['log_loss','brier']:
                wide=dd.pivot(index=['date','event'],columns='model',values=metric)
                diff=(wide[model]-wide.baseline).groupby(level='date').mean().sort_index()
                if len(diff)>=15:
                    for block in [1,3,5]:intervals.append(dict(hour=hour,model=model,metric=metric,**paired_block_interval(diff.values,block=block)))
    result['paired_intervals']=intervals
    result['city_scores']=df[(df.hour==12)&(df.phase=='test')].groupby(['series','model'])[['log_loss','brier']].mean().reset_index().to_dict('records')
    result['value_diagnostic']={'events':len(trades),'mean_pnl_scenario':float(np.mean([t['pnl_scenario'] for t in trades])) if trades else None,'total_pnl_scenario':sum(t['pnl_scenario'] for t in trades),'claims':'Not an executable backtest or verified historical fee calculation; exploratory 2-cent screen.'}
    save('outputs/probability-results.json',result)
    print(df[df.hour==12].groupby(['phase','model'])[['log_loss','brier']].mean().to_string())
    print('Primary intervals',[(x['metric'],x['mean'],x['lower'],x['upper']) for x in intervals if x['hour']==12 and x['model']=='calibrated' and x['block_days']==3])

def live():
    meta=read('data/processed/metadata.json');rounds=read('data/processed/books.json')
    byevent=collections.defaultdict(list);seriesmap={};policies={}
    for s,v in meta.items():
        policies[s]=FeePolicy.from_series(v['series'])
        for m in v['open_markets']:byevent[m['event_ticker']].append(m);seriesmap[m['ticker']]=s
    rows=[];checks=[];depths=[];lp=[];raw_for_graph=[]
    for r in rounds:
        b={o['ticker']:Book.from_payload(o) for o in r['orderbooks'] if 'orderbook_fp' in o}
        span=(datetime.datetime.fromisoformat(r['response_received'])-datetime.datetime.fromisoformat(r['request_started'])).total_seconds()
        for ticker,book in b.items():
            rows.append(dict(round=r['round'],ticker=ticker,series=seriesmap[ticker],received=r['response_received'],response_span_seconds=span,**book.metrics()))
            if r['round']==len(rounds)-1:raw_for_graph.append({'ticker':ticker,'yes_bids':[[float(x),float(y)] for x,y in book.yes_bids],'yes_asks':[[float(x),float(y)] for x,y in book.asks('yes')]})
            for q in [1,10,50,100,250,500]:
                z=sweep(book,'yes',q,policies[seriesmap[ticker]])
                depths.append(dict(round=r['round'],ticker=ticker,quantity=q,**{k:v for k,v in z.items() if k not in ('fills','quantity')}))
        for event,ms in byevent.items():
            pa=partition_audit(ms);tickers=pa.get('tickers',[])
            if not pa['valid'] or any(t not in b for t in tickers):continue
            books=[b[t] for t in tickers];policy=policies[seriesmap[tickers[0]]]
            co=coherence([x.metrics()['bid'] for x in books],[x.metrics()['ask'] for x in books]) if all(x.metrics().get('two_sided') and not x.metrics().get('crossed',False) for x in books) else {}
            for side in ['yes','no']:
                for q in [1,10,100]:
                    z=basket(books,side,q,policy,partition_verified=pa['valid'],exceptional=pa['exceptional_fair_value'],observation_span=span)
                    checks.append(dict(round=r['round'],event=event,series=seriesmap[tickers[0]],side=side,quantity=q,response_span_seconds=span,**co,**{k:v for k,v in z.items() if k!='legs'}))
            if co:
                n=len(books);marketmap={m['ticker']:m for m in ms}
                yes_states=temperature_payoff_states([marketmap[t] for t in tickers])
                A=np.column_stack((yes_states,1-yes_states))
                offers=[book.asks(side)[0] for side in ['yes','no'] for book in books]
                prices=np.array([float(p) for p,q in offers]);depth=np.array([float(q) for p,q in offers])
                costs=prices+.07*float(policy.multiplier)*prices*(1-prices)
                result=statewise_portfolio(A,costs,depth,budget=100)
                q=np.floor(np.asarray(result['quantities'])*100)/100;actual=0.
                for j,z in enumerate(q):
                    if z>0:actual+=sweep(books[j%n],'yes' if j<n else 'no',str(z),policy)['total_cost']
                rechecked=float((A@q-actual).min())
                lp.append(dict(round=r['round'],event=event,lp_relaxation_profit=result['worst_profit'],rounded_rechecked_profit=rechecked,strict_eligible=False,reason='no exchange snapshot timestamp; exceptional fair-value provision'))
    df=pd.DataFrame(rows);df.to_csv(ROOT/'outputs/tables/live-microstructure.csv',index=False)
    pd.DataFrame(depths).to_csv(ROOT/'outputs/tables/depth-costs.csv',index=False)
    save('outputs/tables/basket-checks.json',checks);save('outputs/tables/statewise-lp.json',lp);save('outputs/tables/orderbook-graph-data.json',raw_for_graph)
    valid=df[df.two_sided==True]
    summary=dict(rounds=len(rounds),book_snapshots=len(rows),distinct_markets=int(df.ticker.nunique()),distinct_events=len(byevent),start=rounds[0]['request_started'],end=rounds[-1]['response_received'],median_spread=float(valid.spread.median()),median_response_seconds=float(df.response_span_seconds.median()),conditional_basket_candidates=sum(x['status']=='conditional_candidate' for x in checks),strict_basket_candidates=sum(x.get('strict_eligible',False) for x in checks),positive_lp_relaxations=sum(x['lp_relaxation_profit']>1e-8 for x in lp),positive_rechecked_lp=sum(x['rounded_rechecked_profit']>1e-8 for x in lp),interpretation='short live pilot; REST round-trip spans are observation uncertainty, not order execution latency')
    save('outputs/live-results.json',summary);print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['prepare','freeze','evaluate','live']);a=p.parse_args();globals()[a.stage]()
