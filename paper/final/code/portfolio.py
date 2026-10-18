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
