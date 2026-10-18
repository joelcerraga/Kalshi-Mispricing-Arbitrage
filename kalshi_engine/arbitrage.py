"""Payoff feasibility, conditional basket costs and a bounded statewise optimiser."""
import numpy as np
from scipy.optimize import linprog
from .microstructure import sweep, FeePolicy

def temperature_interval(m):
    s=m.get('strike_type')
    if s=='less':return -np.inf,float(m['cap_strike'])-1
    if s=='greater':return float(m['floor_strike'])+1,np.inf
    if s=='between':return float(m['floor_strike']),float(m['cap_strike'])
    raise ValueError('Unsupported strike semantics')

def temperature_payoff_states(markets,integer_only=False):
    """Enumerate distinct payoff states using every boundary and intervening region.

    Full-precision GLOBALTEMPERATURE rules can leave gaps between integer-labelled
    buckets. The all-zero YES state must not be discarded merely because past
    reported outcomes happened to be integer-valued.
    """
    boundaries=sorted({float(m[k]) for m in markets for k in ('floor_strike','cap_strike') if m.get(k) is not None})
    if not boundaries:raise ValueError('No boundaries')
    probes=[boundaries[0]-1,boundaries[-1]+1]+boundaries+[(a+b)/2 for a,b in zip(boundaries,boundaries[1:])]
    if integer_only:probes=list(range(int(np.floor(boundaries[0]))-1,int(np.ceil(boundaries[-1]))+2))
    rows=[]
    for t in probes:
        row=[]
        for m in markets:
            s=m['strike_type']
            if s=='less':value=t<float(m['cap_strike'])
            elif s=='greater':value=t>float(m['floor_strike'])
            elif s=='between':value=float(m['floor_strike'])<=t<=float(m['cap_strike'])
            else:raise ValueError('Unknown strike')
            row.append(float(value))
        rows.append(row)
    return np.unique(np.asarray(rows),axis=0)

def partition_audit(markets):
    if not markets:return {'valid':False,'reason':'empty event'}
    if len({m['event_ticker'] for m in markets})!=1:return {'valid':False,'reason':'different events'}
    if any(m.get('market_type')!='binary' or float(m.get('notional_value_dollars',0))!=1 for m in markets):
        return {'valid':False,'reason':'non-standard payout'}
    try:ordered=sorted([(temperature_interval(m),m) for m in markets],key=lambda x:x[0][0])
    except (ValueError,KeyError):return {'valid':False,'reason':'unknown intervals'}
    intervals=[x[0] for x in ordered]
    valid=intervals[0][0]==-np.inf and intervals[-1][1]==np.inf
    valid=valid and all(lo<=hi for lo,hi in intervals)
    valid=valid and all(a[1]+1==b[0] for a,b in zip(intervals,intervals[1:]))
    finite=[x for pair in intervals for x in pair if np.isfinite(x)]
    valid=valid and all(x==int(x) for x in finite)
    rules=' '.join(m.get('rules_secondary','') for m in markets).lower()
    exceptional=('fair price' in rules or 'fair value' in rules)
    return dict(valid=bool(valid),reason='integer-temperature partition' if valid else 'gap, overlap or noninteger boundary',
                tickers=[x[1]['ticker'] for x in ordered],exceptional_fair_value=exceptional,
                full_precision_exhaustive=bool(np.all(temperature_payoff_states(markets).sum(axis=1)==1)),
                interpretation='ordinary integer-temperature resolution only; contract rules must match')

def coherence(bids,asks):
    b=np.asarray(bids,float);a=np.asarray(asks,float)
    valid=len(b)>0 and len(b)==len(a) and np.all(np.isfinite(b)) and np.all(np.isfinite(a)) and np.all((b>=0)&(a<=1)&(b<=a))
    if not valid:raise ValueError('Invalid quote intervals')
    return dict(sum_bids=float(b.sum()),sum_asks=float(a.sum()),
                feasible=bool(b.sum()<=1+1e-12 and a.sum()>=1-1e-12),
                midpoint_sum=float(((a+b)/2).sum()))

def basket(books,side,quantity,policy=FeePolicy(),*,partition_verified=False,exceptional=False,
           observation_span=0,max_span=2,fill_unit=None):
    if not partition_verified:return {'status':'blocked_unverified_partition'}
    if len(books)<2:return {'status':'blocked_incomplete_basket'}
    if any(b.metrics().get('crossed',False) for b in books):return {'status':'blocked_crossed_book'}
    costs=[sweep(b,side,quantity,policy,fill_unit) for b in books]
    if not all(x['fillable'] for x in costs):return {'status':'insufficient_depth','legs':costs}
    n=len(books); payout=float(quantity)*(1 if side=='yes' else n-1)
    cost=sum(x['total_cost'] for x in costs)
    profit=payout-cost
    gates=[]
    if observation_span>max_span:gates.append('non_simultaneous_observations')
    if exceptional:gates.append('exceptional_resolution')
    return dict(status='conditional_candidate' if profit>1e-9 else 'no_net_gap',
                ordinary_payout=payout,cost=cost,net_payoff=profit,
                exceptional_worst_payoff=-cost if exceptional else profit,
                reporting_blocks=gates,strict_eligible=profit>1e-9 and not gates,legs=costs)

def statewise_portfolio(payoffs,costs,depth,budget=100):
    """Continuous long-only screening LP. Fees must be included in unit costs.

    Solves max g s.t. A q - c'q >= g in each supplied state. It is a model
    screen, not a rounded, funded or synchronously executable order basket.
    """
    A=np.asarray(payoffs,float);c=np.asarray(costs,float);d=np.asarray(depth,float)
    if A.ndim!=2 or A.shape[1]!=len(c) or c.shape!=d.shape or not np.all(np.isfinite(A)) or not np.all(np.isfinite(c)) or not np.all(np.isfinite(d)) or np.any(c<0) or np.any(d<0) or budget<0:
        raise ValueError('Invalid payoff problem')
    B=np.column_stack((c[None,:]-A,np.ones(A.shape[0])))
    B=np.vstack((B,np.r_[c,0]));rhs=np.r_[np.zeros(A.shape[0]),budget]
    fit=linprog(np.r_[np.zeros(len(c)),-1],A_ub=B,b_ub=rhs,
                bounds=[(0,x) for x in d]+[(0,None)],method='highs')
    if not fit.success:raise RuntimeError(fit.message)
    q=fit.x[:-1]; profits=A@q-c@q
    if profits.min() < fit.x[-1]-1e-7:raise AssertionError('LP payoff validation failed')
    return dict(quantities=q.tolist(),cost=float(c@q),worst_profit=float(profits.min()),state_profits=profits.tolist())

def expected_edge(probability,total_cost,quantity=1,side='yes'):
    p=float(probability)
    if not 0<=p<=1 or quantity<=0:raise ValueError('Invalid probability or quantity')
    return quantity*(p if side=='yes' else 1-p)-total_cost
