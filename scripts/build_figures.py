from pathlib import Path
import sys,json
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,pandas as pd,matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from kalshi_engine.client import ROOT
from kalshi_engine.probability import calibrate
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':'#12283f','text.color':'#12283f','axes.titleweight':'bold','figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white'})
navy='#173852';teal='#087f83';orange='#c66631';grey='#8797a5';register=[]
def save(fig,name,caption):
 fig.tight_layout();n=len(register)+1
 for ext in ['png','svg','pdf']:fig.savefig(ROOT/f'outputs/figures/{name}.{ext}',dpi=180,bbox_inches='tight')
 plt.close(fig);register.append(dict(number=n,file=f'outputs/figures/{name}.png',caption=caption))
def read(name):return json.loads((ROOT/name).read_text())
coverage=pd.read_csv(ROOT/'outputs/tables/coverage.csv');f=read('data/processed/forecast-features.json');pred=read('outputs/tables/frozen-predictions.json');labels={(x['event'],x['hour']):x['winner'] for x in read('data/processed/outcomes.json')};result=read('outputs/probability-results.json')
noon=[e for e in f if e['hour']==12]
fig,ax=plt.subplots(figsize=(7,2.7));d=coverage[coverage.hour==12];a=d.assign(ok=d.status=='accepted').pivot(index='series',columns='date',values='ok').astype(int)
ax.imshow(a,aspect='auto',cmap=matplotlib.colors.ListedColormap(['#d8a68a',teal]),vmin=0,vmax=1);ax.set_yticks(range(3),['Chicago','Miami','New York']);ix=np.arange(0,len(a.columns),15);ax.set_xticks(ix,[a.columns[i][5:] for i in ix]);ax.set_xlabel('Event date (2026; month-day)');ax.set_title('Complete noon quote panels');save(fig,'01_coverage','Coverage of complete six-contract panels at 12:00 local time; peach indicates an excluded event.')
q=pd.read_csv(ROOT/'outputs/tables/historical-quotes.csv');q=q[(q.local_hour==12)&q.event.isin([e['event'] for e in noon])]
fig,ax=plt.subplots(figsize=(7,4));ax.hist(q.spread*100,bins=np.arange(-.25,20.75,.5),color=teal);ax.set(xlabel='Quoted YES spread (cents)',ylabel='Contract observations',title='Historical spread distribution at noon');save(fig,'02_spreads','Historical spreads from accepted noon events. Candle-close quotes have no accompanying depth or fill guarantee.')
h=pd.read_csv(ROOT/'outputs/tables/historical-coherence.csv');fig,ax=plt.subplots(figsize=(7,4));
for side,color in [('yes',teal),('no',orange)]:
 z=h[h.side==side];ax.scatter(z.gross_gap*100,z.net_gap_scenario*100,s=15,alpha=.45,label=side.upper()+' basket',c=color)
ax.axhline(0,color=navy,lw=1);ax.axvline(0,color=navy,lw=1);ax.set(xlabel='Gross quote-only gap (cents per basket)',ylabel='Gap after current fee scenario (cents)',title='Conditional basket discrepancies and fees');ax.legend();save(fig,'03_coherence','Conditional integer-resolution basket gaps from hourly quotes; current fee scenarios do not establish historical execution or contractual arbitrage.')
fig,axs=plt.subplots(1,2,figsize=(7,3.6));scores=result['scores'];
for ax,metric,title in zip(axs,['log_loss','brier'],['Log loss (nats)','Brier score']):
 vals=[next(x[metric] for x in scores if x['hour']==12 and x['phase']=='test' and x['model']==m) for m in ['baseline','candidate']]
 ax.bar(['Market baseline','Calibration candidate'],vals,color=[teal,grey]);ax.tick_params(axis='x',labelsize=8);ax.set_ylabel(title);ax.set_title('Held-out noon events');
 for j,v in enumerate(vals):ax.text(j,v+.008,f'{v:.4f}',ha='center',fontsize=9)
save(fig,'04_scores','Held-out scores for the market-derived baseline and the rejected calibration candidate. Lower is better; validation selected the baseline.')
fig,ax=plt.subplots(figsize=(5.7,4.6));reliability=[]
for key,label,color in [('p','Baseline',teal),('candidate_p','Candidate',orange)]:
 records=[]
 for e in pred:
  if e['hour']==12 and e['phase']=='test':records.extend((p,int(j==labels[(e['event'],12)])) for j,p in enumerate(e[key]))
 ar=np.array(records);xs=[];ys=[];sizes=[]
 for lo in np.arange(0,1,.1):
  mask=(ar[:,0]>=lo)&(ar[:,0]<(lo+.1+1e-10 if lo>.89 else lo+.1))
  if mask.any():xs.append(ar[mask,0].mean());ys.append(ar[mask,1].mean());sizes.append(mask.sum())
 ax.plot(xs,ys,'o-',label=label,color=color);reliability.append(dict(model=label,predicted=xs,observed=ys,n=list(map(int,sizes))))
ax.plot([0,1],[0,1],'--',color=grey);ax.set(xlim=(0,1),ylim=(0,1),xlabel='Mean predicted probability',ylabel='Observed YES frequency',title='Descriptive reliability on later dates');ax.legend();save(fig,'05_reliability','Pooled reliability bins on held-out events. Contracts within an event are dependent; this curve is descriptive, not an independent-bin significance test.')
(ROOT/'outputs/tables/reliability.json').write_text(json.dumps(reliability,indent=2))
live=pd.read_csv(ROOT/'outputs/tables/live-microstructure.csv');last=live[live['round']==live['round'].max()];ticker=last.loc[(last.midpoint-.5).abs().idxmin(),'ticker'];cost=pd.read_csv(ROOT/'outputs/tables/depth-costs.csv');z=cost[(cost.ticker==ticker)&(cost['round']==cost['round'].max())&cost.fillable]
fig,ax=plt.subplots(figsize=(7,4));ax.plot(z.quantity,z.vwap*100,'o-',label='Ask sweep',color=teal);ax.plot(z.quantity,z.total_cost/z.quantity*100,'s--',label='Including fees',color=orange);ax.set(xlabel='Contracts purchased',ylabel='Average cost (cents per contract)',title=ticker);ax.legend();save(fig,'06_depth_cost','Displayed-depth purchase costs for the final snapshot whose midpoint is nearest 0.50; the selection rule is descriptive and does not use future returns.')
fig,ax=plt.subplots(figsize=(7,4));points=pd.read_csv(ROOT/'outputs/tables/imbalance-diagnostics.csv');ax.scatter(points.imbalance,points.next_mid_change*100,color=teal,s=14,alpha=.2);ax.axhline(0,color=grey);ax.set(xlabel='Displayed depth imbalance',ylabel='Next observed midpoint change (cents)',title='Short-session microstructure diagnostic');save(fig,'07_imbalance','Snapshot imbalance and the next observed midpoint change in the brief live session; these are not order-flow events or independent trading trials.')
fig,ax=plt.subplots(figsize=(7,4));syn=pd.read_csv(ROOT/'outputs/tables/synthetic-summary.csv');ax.barh([s.replace('_',' ') for s in syn.scenario],syn.eligible_rate,color=[teal if x=='true_gap' else grey for x in syn.scenario]);ax.set(xlim=(0,1.04),xlabel='Fraction eligible under synthetic assumptions',title='Known-truth structural checks');save(fig,'08_synthetic','Six synthetic mechanisms, 500 replications each. Passing known-truth tests verifies selected logic, not real-market profitability.')
stress=pd.read_csv(ROOT/'outputs/tables/execution-stress.csv');fig,ax=plt.subplots(figsize=(7,4))
for a,c in [(0,teal),(.03,orange),(.05,navy)]:
 z=stress[np.isclose(stress.adverse_entry_cost,a)];ax.plot(z.fill_probability,z.loss_rate,'o-',label=f'{a*100:.0f} cent extra entry cost / leg',color=c)
ax.set(xlabel='Assumed fill probability per leg',ylabel='Simulated probability of loss',title='Non-atomic basket execution');ax.legend(fontsize=8);save(fig,'09_execution_stress','Synthetic independent leg-fill stresses. A positive expected payoff can coexist with losses when an incomplete basket remains exposed.')
fig,ax=plt.subplots(figsize=(7,3.8));ci=[x for x in result['paired_intervals'] if x['hour']==12 and x['model']=='candidate' and x['metric']=='log_loss'];ys=np.arange(len(ci));means=[x['mean'] for x in ci];ax.errorbar(means,ys,xerr=[[x['mean']-x['lower'] for x in ci],[x['upper']-x['mean'] for x in ci]],fmt='o',color=teal,capsize=4);ax.set_yticks(ys,[f"{x['block_days']}-day blocks" for x in ci]);ax.axvline(0,color=grey,ls='--');ax.set(xlabel='Candidate minus baseline log loss (nats)',title='Exploratory candidate comparison');save(fig,'10_block_sensitivity','Paired date-block confidence intervals for the rejected candidate on later dates; negative differences favour the candidate. The selected method is the baseline itself.')
(ROOT/'paper/figures.json').write_text(json.dumps(register,indent=2))
print('Built',len(register),'figures; depth example:',ticker)
