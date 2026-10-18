"""Acquire bounded public data; no credentials, private endpoints or order methods."""
from pathlib import Path
import sys, json, argparse, concurrent.futures, datetime, time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kalshi_engine.client import PublicClient, ROOT, utcnow

SERIES=['KXHIGHNY','KXHIGHCHI','KXHIGHMIA']
def event_date(ticker):
    return datetime.datetime.strptime(ticker.split('-')[1],'%y%b%d').date()

def metadata():
    c=PublicClient(); out={}
    for s in SERIES:
        live=c.paginated('/markets',{'series_ticker':s,'status':'settled','limit':1000},'markets')
        old=c.get('/historical/markets',{'series_ticker':s,'limit':1000})
        rows=old.get('markets',[])
        # This is a bounded 90-day study, never a claim of full exchange history.
        if rows and min(event_date(m['event_ticker']) for m in rows)>datetime.date(2026,7,19) and old.get('cursor'):
            raise RuntimeError('Historical first page does not cover study window')
        allm={m['ticker']:m for m in rows+live}
        selected=[m for m in allm.values() if datetime.date(2026,7,19)<=event_date(m['event_ticker'])<=datetime.date(2026,10,16)]
        out[s]={'series':c.get('/series/'+s)['series'],'markets':sorted(selected,key=lambda m:m['ticker']),
                'open_markets':c.paginated('/markets',{'series_ticker':s,'status':'open','limit':100},'markets'),
                'fee_changes':c.get('/series/fee_changes',{'series_ticker':s,'show_historical':'true'})}
        print(s,'selected',len(selected),'events',len(set(m['event_ticker'] for m in selected)),flush=True)
    (ROOT/'data/processed/metadata.json').write_text(json.dumps(out,indent=2))
    return out

def candles():
    c=PublicClient(); data=json.loads((ROOT/'data/processed/metadata.json').read_text())
    allm=[m for v in data.values() for m in v['markets']]
    byweek={}
    for m in allm:
        d=event_date(m['event_ticker']); monday=d-datetime.timedelta(days=d.weekday())
        byweek.setdefault(str(monday),[]).append(m['ticker'])
    jobs=[]
    for week,tickers in sorted(byweek.items()):
        start=datetime.datetime.fromisoformat(week).replace(tzinfo=datetime.timezone.utc)
        # Endpoint caps potential grid size, not just returned nonempty candles.
        # 32 markets * 8 days * 24 hours = 6,144, below its 10,000 cap.
        for i in range(0,len(tickers),32):
            jobs.append(('/markets/candlesticks',{'market_tickers':','.join(tickers[i:i+32]),'start_ts':int(start.timestamp()),'end_ts':int((start+datetime.timedelta(days=8)).timestamp()),'period_interval':60},tickers[i:i+32]))
    result={}; errors=[]
    def get(j):
        path,params,tickers=j
        try: return tickers,c.get(path,params),None
        except Exception as e:return tickers,{},str(e)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        for tickers,b,err in ex.map(get,jobs):
            if err: errors.append({'tickers':tickers,'error':err}); print('BATCH ERROR',err,flush=True)
            for market in b.get('markets',[]):result[market['market_ticker']]=market.get('candlesticks',[])
            print('Candle batch',len(result),'markets',flush=True)
    missing=[m for m in allm if not result.get(m['ticker'])]
    # Historical routing is required for archived markets; record both probes.
    def old(m):
        d=event_date(m['event_ticker']); start=datetime.datetime.combine(d,datetime.time(),tzinfo=datetime.timezone.utc)
        params={'start_ts':int(start.timestamp()),'end_ts':int((start+datetime.timedelta(days=1)).timestamp()),'period_interval':60}
        try:return m['ticker'],c.get('/historical/markets/'+m['ticker']+'/candlesticks',params).get('candlesticks',[]),None
        except Exception as e:return m['ticker'],[],str(e)
    if missing:
        print('Historical fallback needed',len(missing),flush=True)
        with concurrent.futures.ThreadPoolExecutor(max_workers=6) as ex:
            for i,(t,b,err) in enumerate(ex.map(old,missing)):
                result[t]=b
                if err:errors.append({'ticker':t,'error':err})
                if i%30==0:print('Historical candles',i+1,'/',len(missing),flush=True)
    (ROOT/'data/processed/candles.json').write_text(json.dumps(result))
    (ROOT/'outputs/validation/acquisition-errors.json').write_text(json.dumps(errors,indent=2))
    print('CANDLES COMPLETE',len(result),sum(len(v) for v in result.values()),flush=True)

def books(rounds):
    c=PublicClient(); d=json.loads((ROOT/'data/processed/metadata.json').read_text()); tickers=[m['ticker'] for v in d.values() for m in v['open_markets']]
    rows=[]
    for i in range(rounds):
        start=utcnow()
        try:
            b=c.get('/markets/orderbooks',{'tickers':tickers},cache=False)
            rows.append({'round':i,'request_started':start,'response_received':utcnow(),'orderbooks':b['orderbooks'],'mode':'batch'})
        except Exception as e:
            print('Batch unavailable',str(e),'using documented individual GETs',flush=True)
            def one(t):
                st=utcnow()
                try:return {'ticker':t,'orderbook_fp':c.get('/markets/'+t+'/orderbook',cache=False)['orderbook_fp'],'request_started':st,'response_received':utcnow()}
                except Exception as ex:return {'ticker':t,'error':str(ex),'request_started':st,'response_received':utcnow()}
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:obs=list(ex.map(one,tickers))
            rows.append({'round':i,'request_started':start,'response_received':utcnow(),'orderbooks':obs,'mode':'individual'})
        print('Snapshot round',i+1,'/',rounds,flush=True)
        (ROOT/'data/processed/books.json').write_text(json.dumps(rows))
        if i<rounds-1: time.sleep(3)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['metadata','candles','books']);p.add_argument('--rounds',type=int,default=12);a=p.parse_args()
    {'metadata':metadata,'candles':candles,'books':lambda:books(a.rounds)}[a.stage]()
