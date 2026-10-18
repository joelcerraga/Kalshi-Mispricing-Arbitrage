"""Decimal order-book reconstruction and transparent execution-cost scenarios."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR

D=Decimal
ONE=D('1'); ZERO=D('0')

def decimal(x):
    z=D(str(x))
    if not z.is_finite(): raise ValueError('Non-finite numeric input')
    return z

def levels(rows):
    combined={}
    for p,q in rows or []:
        p,q=decimal(p),decimal(q)
        if not ZERO<=p<=ONE or q<0: raise ValueError('Invalid price or quantity')
        if q>0: combined[p]=combined.get(p,ZERO)+q
    return sorted(combined.items(),reverse=True)

@dataclass
class Book:
    yes_bids:list
    no_bids:list
    @classmethod
    def from_payload(cls,p):
        p=p.get('orderbook_fp',p)
        return cls(levels(p.get('yes_dollars')),levels(p.get('no_dollars')))
    def bids(self,side):
        if side not in ('yes','no'): raise ValueError('Unknown side')
        return self.yes_bids if side=='yes' else self.no_bids
    def asks(self,side):
        if side not in ('yes','no'): raise ValueError('Unknown side')
        return [(ONE-p,q) for p,q in self.bids('no' if side=='yes' else 'yes')]
    def metrics(self):
        bids,asks=self.bids('yes'),self.asks('yes')
        if not bids or not asks:return {'two_sided':False}
        b,qb=bids[0]; a,qa=asks[0]
        if b>a: return {'two_sided':True,'crossed':True}
        return dict(two_sided=True,crossed=False,bid=float(b),ask=float(a),spread=float(a-b),
                    midpoint=float((a+b)/2),bid_depth=float(qb),ask_depth=float(qa),
                    imbalance=float((qb-qa)/(qb+qa)),
                    weighted_midpoint=float((a*qb+b*qa)/(qb+qa)))

@dataclass(frozen=True)
class FeePolicy:
    coefficient:D=D('0.07')
    multiplier:D=D('1')
    balance_precision:D=D('0.0001')
    @classmethod
    def from_series(cls,metadata,**kw):
        if metadata.get('fee_type') not in ('quadratic','quadratic_with_maker_fees'):
            raise ValueError('Unverified fee type')
        if 'fee_multiplier' not in metadata: raise ValueError('Missing fee multiplier')
        m=decimal(metadata['fee_multiplier'])
        if m<0:raise ValueError('Negative fee multiplier')
        return cls(multiplier=m,**kw)

def ceil_grid(x,grid):return (x/grid).to_integral_value(rounding=ROUND_CEILING)*grid
def floor_grid(x,grid):return (x/grid).to_integral_value(rounding=ROUND_FLOOR)*grid

def execution_fee(fills,policy=FeePolicy()):
    """One order, enumerated fills, per-fill six-decimal fee and rounding accumulator.

    The caller specifies fill granularity. A price level is not necessarily one fill.
    Return is a scenario, never a reconstruction of undisclosed counterparties.
    """
    if policy.coefficient<0 or policy.multiplier<0 or policy.balance_precision<=0:raise ValueError('Invalid fee policy')
    accumulator=ZERO; total=ZERO
    for p,q in fills:
        p,q=decimal(p),decimal(q)
        if not ZERO<=p<=ONE or q<ZERO:raise ValueError('Invalid fill')
        raw=policy.coefficient*policy.multiplier*q*p*(ONE-p)
        trade=ceil_grid(raw,D('0.000001'))
        revenue=-p*q
        aligned=floor_grid(revenue-trade,policy.balance_precision)
        rounding=(revenue-trade)-aligned
        accumulator+=rounding
        eligible=floor_grid(accumulator,policy.balance_precision)
        cap=floor_grid(trade+rounding,policy.balance_precision)
        rebate=min(eligible,cap)
        total+=trade+rounding-rebate;accumulator-=rebate
    return total

def sweep(book,side,quantity,policy=FeePolicy(),fill_unit=None):
    q=decimal(quantity)
    if q<=0:raise ValueError('Quantity must be positive')
    rem=q; fills=[]
    for p,depth in book.asks(side):
        take=min(rem,depth)
        if take>0:fills.append((p,take));rem-=take
        if rem==0:break
    if rem>0:return {'fillable':False,'requested':float(q),'shortfall':float(rem)}
    fee_fills=fills
    if fill_unit is not None:
        unit=decimal(fill_unit)
        if unit<=0:raise ValueError('Invalid fill unit')
        fee_fills=[]
        for p,v in fills:
            while v>0:
                z=min(unit,v); fee_fills.append((p,z));v-=z
    cost=sum((p*v for p,v in fills),ZERO); fee=execution_fee(fee_fills,policy)
    return dict(fillable=True,quantity=float(q),purchase_cost=float(cost),fee=float(fee),
                total_cost=float(cost+fee),vwap=float(cost/q),
                slippage=float(cost/q-fills[0][0]),levels=len(fills),
                fills=[(float(p),float(v)) for p,v in fills])
