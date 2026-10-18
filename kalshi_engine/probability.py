"""Probability-simplex modelling and strictly chronological scoring helpers."""
import numpy as np
from scipy.optimize import minimize_scalar

def normalise(values,epsilon=1e-4):
    x=np.asarray(values,float)
    if x.ndim!=1 or not len(x) or not np.all(np.isfinite(x)) or np.any(x<0):raise ValueError('Invalid nonnegative scores')
    x=np.maximum(x,epsilon)
    return x/x.sum()

def calibrate(p,temperature=1):
    if not np.isfinite(temperature) or temperature<=0:raise ValueError('Invalid temperature')
    z=np.log(normalise(p,epsilon=1e-12))/temperature;z-=z.max()
    return normalise(np.exp(z),epsilon=0)

def scores(p,winner):
    p=normalise(p,epsilon=1e-12)
    if winner<0 or winner>=len(p):raise ValueError('Winner out of range')
    y=np.zeros(len(p));y[winner]=1
    return {'log_loss':float(-np.log(p[winner])),'brier':float(np.sum((p-y)**2))}

def fit_temperature(events):
    if not events:raise ValueError('No development events')
    loss=lambda logt:np.mean([scores(calibrate(e['p'],np.exp(logt)),e['winner'])['log_loss'] for e in events])
    result=minimize_scalar(loss,bounds=(np.log(.25),np.log(4)),method='bounded',options={'xatol':1e-10})
    if not result.success:raise RuntimeError('Calibration did not converge')
    return {'temperature':float(np.exp(result.x)),'development_log_loss':float(result.fun)}

def paired_block_interval(date_differences,draws=1999,block=3,seed=170026):
    """Moving-block bootstrap on date-aggregated paired losses, equal date weights."""
    x=np.asarray(date_differences,float);n=len(x)
    if n<block or not np.all(np.isfinite(x)):raise ValueError('Insufficient finite dates')
    rng=np.random.default_rng(seed);means=[]
    for _ in range(draws):
        starts=rng.integers(0,n-block+1,size=int(np.ceil(n/block)))
        idx=np.concatenate([np.arange(s,s+block) for s in starts])[:n]
        means.append(x[idx].mean())
    return dict(mean=float(x.mean()),lower=float(np.quantile(means,.025)),upper=float(np.quantile(means,.975)),
                dates=n,draws=draws,block_days=block)
