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
