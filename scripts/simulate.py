"""Known-truth validation and explicitly synthetic non-atomic execution stresses."""
from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd
from kalshi_engine.client import ROOT
from kalshi_engine.microstructure import Book,FeePolicy,execution_fee
from kalshi_engine.arbitrage import basket

def run():
    rng=np.random.default_rng(20261017);rows=[]
    scenarios=['coherent','true_gap','fees_remove_gap','insufficient_depth','asynchronous','exceptional_settlement']
    for replication in range(500):
        p=rng.dirichlet(np.ones(6)*8);p=(p+.02)/(1+.12)
        for scenario in scenarios:
            a=p+.01 if scenario=='coherent' else p*(.995 if scenario=='fees_remove_gap' else .9)
            depth=5 if scenario=='insufficient_depth' else 100
            books=[Book.from_payload({'yes_dollars':[[str(max(0,float(x)-.01)),str(depth)]],
                                      'no_dollars':[[str(1-float(x)),str(depth)]]}) for x in a]
            result=basket(books,'yes',10,partition_verified=True,
                          exceptional=scenario=='exceptional_settlement',observation_span=5 if scenario=='asynchronous' else 0)
            expected=scenario=='true_gap'
            detected=result.get('strict_eligible',False)
            rows.append(dict(replication=replication,scenario=scenario,expected=expected,detected=detected,
                             correct=expected==detected,net_payoff=result.get('net_payoff')))
    df=pd.DataFrame(rows);df.to_csv(ROOT/'outputs/tables/synthetic-validation.csv',index=False)
    summary=df.groupby('scenario').agg(replications=('correct','size'),accuracy=('correct','mean'),eligible_rate=('detected','mean')).reset_index()
    summary.to_csv(ROOT/'outputs/tables/synthetic-summary.csv',index=False)
    # One six-leg ordinary-resolution basket costs 0.9 before fees. Independent
    # fill Bernoullis are a chosen stress mechanism, not estimated fill probabilities.
    rows=[]
    n=6;p=np.repeat(1/n,n);ask=np.repeat(.15,n);fee=.07*ask*(1-ask)
    draws=20000
    for fill_prob in [.5,.7,.85,.95,1]:
        fills=rng.random((draws,n))<fill_prob
        outcome=rng.integers(0,n,draws)
        for adverse_move in [0,.01,.03,.05]:
            # Rejected legs remain unfilled; held contracts are marked to terminal
            # payout. Added adverse movement is a per-filled-leg entry-cost stress.
            cost=fills@(ask+fee+adverse_move)
            payout=fills[np.arange(draws),outcome]
            pnl=payout-cost
            rows.append(dict(fill_probability=fill_prob,adverse_entry_cost=adverse_move,
                             all_leg_fill_rate=float(fills.all(axis=1).mean()),loss_rate=float((pnl<0).mean()),
                             mean_pnl=float(pnl.mean()),p05=float(np.quantile(pnl,.05)),draws=draws,
                             interpretation='synthetic independent leg fills; no empirical fill calibration'))
    pd.DataFrame(rows).to_csv(ROOT/'outputs/tables/execution-stress.csv',index=False)
    (ROOT/'outputs/synthetic-results.json').write_text(json.dumps({'scenarios':6,'replications_per_scenario':500,'scenario_evaluations':len(df),'all_checks_passed':bool(df.correct.all()),'stress_scenarios':len(rows),'draws_per_fill_setting':draws,'paired_draws_across_costs':True,'seed':20261017},indent=2))
    print(summary.to_string(index=False))

if __name__=='__main__':run()
