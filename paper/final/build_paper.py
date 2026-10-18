"""Build paper exhibits from frozen outputs; no new data or model selection."""
from pathlib import Path
import ast, csv, hashlib, json, shutil, math
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
GEN=HERE/'generated'; FIG=HERE/'figures'; CODE=HERE/'code'
for d in [GEN,FIG,CODE]:d.mkdir(exist_ok=True)
def read(path):return json.loads((ROOT/path).read_text())
def csvread(path):return list(csv.DictReader((ROOT/path).open()))
def esc(s):
    s=str(s).replace('−','-').replace('–','--').replace('—','--')
    return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','\\':r'\textbackslash{}'}.get(c,c) for c in s)
def n(x,d=3):return f'{float(x):,.{d}f}'
def pct(x):return n(100*float(x),1)+r'\%'

freeze=read('protocol/model-freeze.json')
frozen_files=freeze['implementation_hashes']|{'data/processed/forecast-features.json':freeze['feature_hash'],'outputs/tables/frozen-predictions.json':freeze['prediction_hash'],'protocol/01_research_design.md':freeze['protocol_hash']}
for p,h in frozen_files.items():assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,p

TABLES=[]
def table(name,title,headers,rows,cols,notes='',size=10):
    TABLES.append({'id':name,'title':title,'rows':len(rows)})
    t=r'\begin{table}[htbp]\centering'+'\n'+rf'{{\fontsize{{{size}}}{{12}}\selectfont\renewcommand{{\arraystretch}}{{1.18}}\setlength{{\tabcolsep}}{{4pt}}'+'\n'
    t+=r'\begin{tabularx}{\linewidth}{@{}'+cols+r'@{}}\toprule\rowcolor{tablehead}'+'\n'
    t+=' & '.join(r'\textbf{'+h+'}' for h in headers)+r' \\ \midrule'+'\n'
    t+='\n'.join(' & '.join(map(str,row))+r' \\ \arrayrulecolor{tablerule}\hline' for row in rows)+'\n'
    t+=r'\arrayrulecolor{black}\bottomrule\end{tabularx}}'+'\n'+rf'\caption[{esc(title)}]{{{esc(title)}.}}\label{{tab:{name}}}'+'\n'
    if notes:t+=r'\vspace{2pt}{\centering\fontsize{9.3}{11.5}\selectfont '+notes+r'\par}'+'\n'
    t+=r'\end{table}'+'\n';(GEN/f'table-{name}.tex').write_text(t)
def longtable(name,title,headers,rows,cols,size=10,leading=12):
    TABLES.append({'id':name,'title':title,'rows':len(rows)})
    t=rf'{{\fontsize{{{size}}}{{{leading}}}\selectfont\renewcommand{{\arraystretch}}{{1.12}}\setlength{{\tabcolsep}}{{4pt}}'+'\n'
    t+=r'\begin{longtable}{@{}'+cols+r'@{}}'+'\n'
    head=r'\toprule\rowcolor{tablehead}'+' & '.join(r'\textbf{'+h+'}' for h in headers)+r' \\ \midrule'+'\n'
    t+=head+r'\endfirsthead'+'\n'+head+r'\endhead'+'\n'+r'\multicolumn{'+str(len(headers))+r'}{r}{\fontsize{9}{11}\selectfont\itshape Continued on the next page}\\\endfoot'+'\n'+r'\endlastfoot'+'\n'
    t+='\n'.join(' & '.join(row)+r' \\ \arrayrulecolor{tablerule}\hline' for row in rows)+'\n'
    t+=r'\arrayrulecolor{black}\bottomrule'+f'\n\\caption[{esc(title)}]{{{esc(title)}.}}\\label{{tab:{name}}}\\\\\n'+r'\end{longtable}}'+'\n'
    (GEN/f'{name}.tex').write_text(t)

abbr=csvread('paper/abbreviations.csv')+[
 {'abbreviation':'HTML','meaning':'Hypertext Markup Language'},
 {'abbreviation':'PDF','meaning':'Portable Document Format'},
 {'abbreviation':'USD','meaning':'United States dollar'}]
longtable('abbreviations','Abbreviations',['Abbreviation','Meaning'],[[esc(x['abbreviation']),esc(x['meaning'])] for x in sorted(abbr,key=lambda x:x['abbreviation'].lower())],r'L{27mm}L{134mm}')

syms=[
 (r'i,j','Contract or outcome index','index'),(r'e','Daily city event','index'),(r'd','Calendar date','index'),(r'\ell','Price level or enumerated fill','index'),
 (r'\omega','Contract resolution state','state'),(r'\Omega','Set of included resolution states','set'),(r'A_i','Event specified by contract i','set'),
 (r'X_i,X_i^N','YES and NO terminal payoffs','USD / contract'),(r'\mathbf1\{\cdot\}','Indicator of a true condition','0 or 1'),
 (r'a_i^Y,a_i^N','Best YES and NO asks','USD / contract'),(r'b_i^Y,b_i^N','Best YES and NO bids','USD / contract'),
 (r's_i,m_i','Quoted spread and midpoint','USD / contract'),(r'\widetilde m_i','Depth-weighted midpoint','USD / contract'),
 (r'D_i^b,D_i^a','Displayed quantity at the best bid and ask','contracts'),(r'I_i','Snapshot depth imbalance','unitless'),
 (r'q_i,q_{i\ell}','Total acquired quantity and quantity per fill','contracts'),(r'p_{i\ell}','Acquisition price at level or fill ell','USD / contract'),
 (r'C_i(q_i)','Purchase cost excluding fees','USD'),(r'f_i^{\rm raw}','Unrounded model fee for an order','USD'),(r'F_i(q_i)','Total fee after rounding and rebates','USD'),
 (r'M_i','Series fee multiplier','unitless'),(r'u_\ell,t_\ell','Signed fill revenue and rounded trade fee','USD'),(r'\delta','Target balance precision','USD'),
 (r'r_\ell,R_\ell','Balance rounding and accumulator rebate','USD'),(r'H_\ell','Carried rounding accumulator','USD'),
 (r'\lceil x\rceil_h,\lfloor x\rfloor_h','Round x up or down to a multiple of h','same as x'),
 (r'\Pi(\omega;\mathbf q)','Portfolio net payoff in a state','USD'),(r'\mathbf A','State-by-position payoff matrix','USD / contract'),
 (r'\mathbf c,\mathbf d','Unit acquisition costs and displayed depth caps','USD / contract; contracts'),(r'B,g','Budget and lowest statewise net payoff','USD'),
 (r'p_{ei},\widehat p_{ei}','Baseline and model probability for an outcome','probability'),(r'\epsilon','Positive midpoint floor (0.0001)','USD / contract'),
 (r'T','Probability calibration temperature','unitless'),(r'y_e','Observed winning outcome for event e','index'),
 (r'N,D,n_d','Events, dates and accepted events on date d','counts'),(r'L_{\log},L_B','Mean logarithmic loss and Brier score','nats; unitless'),
 (r'\widehat V_i(q)','Model-based expected net payoff','USD'),(r'\overline\Delta','Equal-date paired score difference','score units'),
 (r'K,\rho','Basket legs and per-leg fill probability','count; probability'),(r'J_i','Synthetic indicator that leg i fills','0 or 1'),
 (r'\eta','Additional entry cost per filled synthetic leg','USD / contract')]
longtable('symbols','Mathematical symbols',['Symbol','Meaning','Units'],[['$'+a+'$',esc(b),esc(c)] for a,b,c in syms],r'L{30mm}L{96mm}L{32mm}',9.4,11.1)

eqs=read('paper/equations.json')
for e in eqs:
    expression=e['latex']
    if e['number']==7:expression=r'f_i^{\rm raw}=0.07M_i\sum_{\ell}q_{i\ell}p_{i\ell}(1-p_{i\ell}).'
    if e['number']==8:
        expression=r'\begin{aligned}t_\ell&=\lceil f_\ell^{\rm model}\rceil_{10^{-6}},\quad u_\ell=-p_\ell q_\ell,\\r_\ell&=(u_\ell-t_\ell)-\lfloor u_\ell-t_\ell\rfloor_\delta,\\R_\ell&=\min\{\lfloor H_{\ell-1}+r_\ell\rfloor_\delta,\lfloor t_\ell+r_\ell\rfloor_\delta\},\\H_\ell&=H_{\ell-1}+r_\ell-R_\ell,\quad f_\ell^{\rm net}=t_\ell+r_\ell-R_\ell.\end{aligned}'
    if e['number']==11:expression=r'\begin{aligned}\max_{\mathbf q,g}\;&g\\ \text{subject to }\;&\mathbf A\mathbf q-(\mathbf c^{\mathsf T}\mathbf q)\mathbf1\geq g\mathbf1,\\&0\leq\mathbf q\leq\mathbf d,\quad\mathbf c^{\mathsf T}\mathbf q\leq B,\quad g\geq0.\end{aligned}'
    t=r'\par\needspace{70pt}\begin{minipage}{\linewidth}'+'\n'+r'\begin{equation}'+expression+rf'\label{{eq:{e["number"]}}}'+r'\end{equation}'+'\n'+r'\eqcaption{'+esc(e['caption'])+'}\n'+r'\end{minipage}\par'+'\n'
    (GEN/f'equation-{e["number"]}.tex').write_text(t)

table('series','Empirical market universe',['City','Series','Historical dates','Events / contracts'],[
 ['New York',r'\texttt{KXHIGHNY}','19 July--16 October 2026','90 / 540'],
 ['Chicago',r'\texttt{KXHIGHCHI}','19 July--16 October 2026','90 / 540'],
 ['Miami',r'\texttt{KXHIGHMIA}','19 July--16 October 2026','90 / 540']],r'L{25mm}L{31mm}L{64mm}X',notes='Daily maximum-temperature events. Six contracts per event; 270 historical events and 1,620 contracts in total.')
table('sources','Acquisition routes and analytical roles',['Material','Public REST route','Analytical role'],[
 ['Market metadata',r'\texttt{/markets};\newline\texttt{/historical/markets}','Event membership, strikes, settled outcomes and rule text.'],
 ['Hourly candles',r'\texttt{/markets/candlesticks}; historical market candles','Completed-hour bid and ask summaries; no historical depth.'],
 ['Live books',r'\texttt{/markets/orderbooks}','Repeated fixed-point bids and quantities; request timing recorded.'],
 ['Fee metadata',r'\texttt{/series/\{series\}}; fee-change records','Series fee type and multiplier; dated historical applicability remains uncertified.']],r'L{27mm}L{63mm}X',notes=r'Base endpoint: \url{https://external-api.kalshi.com/trade-api/v2}. All research collection uses GET requests.')
coverage=pd.read_csv(ROOT/'outputs/tables/coverage.csv')
rows=[]
for phase,dates,planned in [('development','19 July--10 September',162),('validation','11--28 September',54),('test','29 September--16 October',54)]:
    vals=[len(coverage[(coverage.phase==phase)&(coverage.hour==h)&(coverage.status=='accepted')]) for h in [9,12,15]]
    rows.append([phase.capitalize(),dates,str(planned),*map(str,vals)])
rows.append(['Total','90 dates','270','267','268','265'])
table('coverage','Chronological samples and completed-hour coverage',['Sample','2026 dates','Planned','09:00','12:00','15:00'],rows,r'L{27mm}L{55mm}C{18mm}C{18mm}C{18mm}X',notes='Counts are complete six-contract event panels at city-local time. The noon specification is primary.',size=9.8)
table('contract-audit','Payoff partition and settlement audit',['Check','Historical','Live','Interpretation'],[
 ['Daily events','270','6','No mixing of city/date event membership.'],
 ['Integer partitions','270','6','Exactly one winning YES in the model restricted to integers.'],
 ['Exhaustive over full-precision probes','0','0','A conservative continuous-state audit retains an all-zero YES state.'],
 ['Observed single binary winner','270','Not settled','Historical scoring is conditional on this observed outcome universe.']],r'L{55mm}C{20mm}C{20mm}X',notes='Continuous-state incompleteness is a screening assumption, not evidence that a noninteger gap resolution actually occurred.')
table('fees','Illustrative fee arithmetic',['Scenario','Purchase cost','Fee','Total outlay'],[
 [r'One contract at \$0.50; direct precision',r'\$0.5000',r'\$0.0175',r'\$0.5175'],
 [r'One contract at \$0.50; cent precision',r'\$0.5000',r'\$0.0200',r'\$0.5200'],
 [r'Six one-contract legs at \$0.15; raw fee',r'\$0.90000',r'\$0.05355',r'\$0.95355']],r'L{77mm}C{27mm}C{26mm}X',notes='Constructed examples with fee multiplier one. The last row is the raw-fee synthetic experiment, without fill-level balance rounding.')
h=pd.read_csv(ROOT/'outputs/tables/historical-coherence.csv'); rows=[]
for side in ['yes','no']:
    z=h[h.side==side];rows.append([side.upper(),str(len(z)),str((z.gross_gap>1e-8).sum()),str((z.net_gap_scenario>1e-8).sum()),n(100*z.gross_gap.max(),2),n(100*z.net_gap_scenario.max(),2)])
table('historical','Historical conditional basket discrepancies',['Basket','Checks','Gross positive','Net positive','Max gross (cents)','Max net (cents)'],rows,r'L{19mm}C{17mm}C{29mm}C{26mm}C{34mm}X',notes='One contract per leg; 268 events per side. Net values use the current direct-member rounding scenario. No historical fill or depth is asserted.',size=9.4)
prob=read('outputs/probability-results.json'); rows=[]
for ph in ['development','validation','test']:
    for m in ['baseline','candidate']:
        s=next(x for x in prob['scores'] if x['hour']==12 and x['phase']==ph and x['model']==m)
        rows.append([ph.capitalize(),'Baseline' if m=='baseline' else 'Candidate',n(s['log_loss'],6),n(s['brier'],6)])
table('scores','Primary probability scores at noon',['Sample','Probability vector','Log loss (nats)','Brier score'],rows,r'L{37mm}L{44mm}C{40mm}X',notes=r'Candidate $T=1.034401$; validation selected $T=1$, so the selected model equals the baseline. Lower scores are better.')
rows=[]
for metric in ['log_loss','brier']:
    for block in [1,3,5]:
        z=next(x for x in prob['paired_intervals'] if x['hour']==12 and x['model']=='candidate' and x['metric']==metric and x['block_days']==block)
        rows.append(['Log loss' if metric=='log_loss' else 'Brier',str(block),n(z['mean'],6),'$['+n(z['lower'],6)+r',\ '+n(z['upper'],6)+']$'])
table('intervals','Paired date-block sensitivity for the rejected candidate',['Metric','Block days','Mean difference',r'95\% interval'],rows,r'L{30mm}C{24mm}C{42mm}X',notes='Candidate minus baseline, equal weight per date; 18 dates and 1,999 draws. Three days is primary. These are supplementary comparisons, not a revised selection rule.')
rows=[]
for hour in [9,12,15]:
    a=next(x for x in prob['scores'] if x['hour']==hour and x['model']=='baseline' and x['phase']=='test')
    b=next(x for x in prob['scores'] if x['hour']==hour and x['model']=='candidate' and x['phase']=='test')
    count=next(x['n'] for x in prob['counts'] if x['hour']==hour and x['model']=='baseline' and x['phase']=='test')
    rows.append([f'{hour:02d}:00',str(count),n(a['log_loss'],6),n(b['log_loss'],6),n(a['brier'],6),n(b['brier'],6)])
table('timing','Later-period sensitivity to observation time',['Local time','$N$','Base log loss','Candidate log loss','Base Brier','Candidate Brier'],rows,r'L{23mm}C{11mm}C{32mm}C{35mm}C{28mm}X',notes='The noon-fitted candidate is transferred unchanged. Different accepted panels and information horizons prevent a causal interpretation of cross-hour differences.',size=9.4)
rows=[]
for city,series in [('Chicago','KXHIGHCHI'),('Miami','KXHIGHMIA'),('New York','KXHIGHNY')]:
    a=next(x for x in prob['city_scores'] if x['series']==series and x['model']=='baseline'); b=next(x for x in prob['city_scores'] if x['series']==series and x['model']=='candidate')
    count=len(coverage[(coverage.series==series)&(coverage.hour==12)&(coverage.phase=='test')&(coverage.status=='accepted')])
    rows.append([city,str(count),n(a['log_loss'],6),n(b['log_loss'],6),n(a['brier'],6),n(b['brier'],6)])
table('cities','Later-period scores by city',['City','$N$','Base log loss','Candidate log loss','Base Brier','Candidate Brier'],rows,r'L{23mm}C{11mm}C{32mm}C{35mm}C{28mm}X',notes='All cities use the same fitted temperature and chronological split; no city-specific refitting.',size=9.4)
table('live','Recorded live-pilot audit',['Object','Count or estimate','Meaning'],[
 ['Batch responses / duration','20 / 166.12 s','One short collection session on 17 October 2026.'],
 ['Individual books','720','36 contracts across 6 events, observed 20 times.'],
 ['Two-sided / one-sided books','406 / 314','Spread summaries use the two-sided subset.'],
 ['Median spread','1.00 cent','Displayed spread, not an executed transaction cost.'],
 ['Median request span','5.307 s','HTTP collection span, not exchange latency.'],
 ['Complete basket-side-size checks','378 of 720','Enough displayed depth; none has a positive net gap.'],
 ['Checks rejected for depth','342 of 720','At least one leg cannot supply the required size.'],
 ['Statewise portfolio checks','46','Complete two-sided event observations; no positive solution.']],r'L{64mm}L{33mm}X',notes='The 720 individual books and 720 basket checks are different denominators. Basket checks use two sides and three quantities per event per round.',size=9.6)
syn=csvread('outputs/tables/synthetic-summary.csv')
names={'asynchronous':'Asynchronous observation','coherent':'Coherent prices','exceptional_settlement':'Exceptional settlement','fees_remove_gap':'Fees remove the gap','insufficient_depth':'Insufficient depth','true_gap':'True supplied-state gap'}
table('synthetic','Known-truth synthetic screening checks',['Mechanism','Checks','Correct','Eligible'],[[names[x['scenario']],x['replications'],pct(x['accuracy']),pct(x['eligible_rate'])] for x in syn],r'L{82mm}C{24mm}C{27mm}X',notes='500 probability draws are paired across six mechanisms: 3,000 scenario evaluations, not 3,000 independent markets.')
stress=pd.read_csv(ROOT/'outputs/tables/execution-stress.csv');rows=[]
for rho in [.5,.7,.85,.95,1]:
    a=stress[(stress.fill_probability==rho)&(stress.adverse_entry_cost==0)].iloc[0];b=stress[(stress.fill_probability==rho)&(stress.adverse_entry_cost==.01)].iloc[0]
    rows.append([n(rho,2),pct(a.all_leg_fill_rate),pct(a.loss_rate),n(a.mean_pnl,4),pct(b.loss_rate),n(b.mean_pnl,4)])
table('stress','Synthetic six-leg execution stress',['Per-leg fill','All filled','Loss, base',r'Mean, base (\$)','Loss, +1c',r'Mean, +1c (\$)'],rows,r'C{23mm}C{25mm}C{26mm}C{29mm}C{26mm}X',notes=r'20,000 draws per fill setting, paired across entry-cost scenarios. +1c adds \$0.01 per filled leg while retaining the base raw fee. No empirical fill probability is estimated.',size=9.4)
table('validation','Research and presentation verification',['Layer','Check','Recorded result'],[
 ['Analytical tests','Books, costs, payoff states, probabilities and bootstrap helpers','45 tests passed'],
 ['Synthetic mechanisms','Six designed scenarios, paired probability draws','3,000 checks passed'],
 ['Notebook execution','Eight nbformat-4 notebooks','31 code cells executed'],
 ['Source provenance','Stored snapshot hashes verified during offline replay','521 snapshots verified'],
 ['Browser behaviour','Interactive controls, mathematical rendering, downloads and mobile width','24 checks passed'],
 ['Analytical freeze','Inputs, implementation and frozen probabilities','Unchanged during paper assembly']],r'L{31mm}L{88mm}X',notes='Verification establishes reproducibility and selected implementation properties; it does not certify market profitability or complete settlement-state coverage.')
milestones=read('protocol/milestones.json')
table('notebooks','Executed notebook sequence',['Notebook','Research stage','Code cells'],[[f'{i:02d}',esc(x['title'].split(' · ',1)[1]),str(x['executed_code_cells'])] for i,x in enumerate(milestones)],r'C{24mm}L{112mm}X',notes='Each notebook retains executed outputs. The HTML review groups them by milestone and provides individual downloads.')

# Existing publication figures retain their original analytical data.
short=['Completed-hour sample coverage','Historical quoted spreads','Gross and fee-adjusted basket gaps','Later-period probability scores','Descriptive probability reliability','Quantity-dependent acquisition costs','Snapshot imbalance and subsequent quotes','Synthetic screening mechanisms','Synthetic partial-execution stress','Date-block interval sensitivity']
figs=read('paper/figures.json')
for x,title in zip(figs,short):
    shutil.copy2(ROOT/Path(x['file']).with_suffix('.pdf'),FIG/f'figure-{x["number"]:02d}.pdf')
    x['short']=title

# The two sparse microstructure panels use a shorter portrait-page aspect ratio.
# Their inputs, series and selection rule are unchanged from the research figures.
with plt.rc_context({'font.family':'DejaVu Sans','font.size':10,'axes.labelsize':10,
                     'axes.titlesize':11,'xtick.labelsize':9,'ytick.labelsize':9,
                     'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False}):
    live=pd.read_csv(ROOT/'outputs/tables/live-microstructure.csv')
    last=live[live['round']==live['round'].max()]
    selected=last.loc[(last.midpoint-.5).abs().idxmin(),'ticker']
    costs=pd.read_csv(ROOT/'outputs/tables/depth-costs.csv')
    z=costs[(costs.ticker==selected)&(costs['round']==costs['round'].max())&costs.fillable]
    fig,ax=plt.subplots(figsize=(7,2.75))
    ax.plot(z.quantity,z.vwap*100,'o-',label='Ask sweep',color='#087f83',ms=4)
    ax.plot(z.quantity,z.total_cost/z.quantity*100,'s--',label='Including fees',color='#c66631',ms=4)
    ax.set(xlabel='Contracts purchased',ylabel='Average cost (cents)',title=selected)
    ax.legend(fontsize=8);fig.tight_layout(pad=.6);fig.savefig(FIG/'figure-06.pdf');plt.close(fig)
    points=pd.read_csv(ROOT/'outputs/tables/imbalance-diagnostics.csv')
    fig,ax=plt.subplots(figsize=(7,2.75));ax.scatter(points.imbalance,points.next_mid_change*100,color='#087f83',s=14,alpha=.25)
    ax.axhline(0,color='#8797a5',lw=.8)
    ax.set(xlabel='Displayed depth imbalance',ylabel='Next midpoint change (cents)',title='Short-session microstructure diagnostic')
    fig.tight_layout(pad=.6);fig.savefig(FIG/'figure-07.pdf');plt.close(fig)

# Static counterparts of the interactive 3D views, generated from the same inputs.
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.labelsize':12,'xtick.labelsize':11,'ytick.labelsize':11,'pdf.fonttype':42,'axes.spines.top':False,'axes.spines.right':False})
teal='#087f83';navy='#173852';orange='#c66631'
books=read('data/processed/books.json');final=books[-1]['orderbooks']
def mid(o):return (max(float(x[0]) for x in o['orderbook_fp']['yes_dollars'])+1-max(float(x[0]) for x in o['orderbook_fp']['no_dollars']))/2
ticker=min((o for o in final if o['orderbook_fp']['yes_dollars'] and o['orderbook_fp']['no_dollars']),key=lambda o:abs(mid(o)-.5))['ticker']
from datetime import datetime
start=datetime.fromisoformat(books[0]['response_received'])
fig=plt.figure(figsize=(6.6,4.6));ax=fig.add_subplot(111,projection='3d')
for b in books:
    o=next(x for x in b['orderbooks'] if x['ticker']==ticker);levels=sorted((1-float(p),float(q)) for p,q in o['orderbook_fp']['no_dollars']);t=(datetime.fromisoformat(b['response_received'])-start).total_seconds()
    ax.plot([p for p,q in levels],[t]*len(levels),np.cumsum([q for p,q in levels]),color=teal,alpha=.75,lw=.9)
ax.set(xlabel='YES ask (USD)',ylabel='Elapsed time (s)',zlabel='Cumulative contracts');ax.view_init(24,-55);fig.subplots_adjust(left=.01,right=.91,bottom=.09,top=.99);fig.savefig(FIG/'figure-11.pdf');plt.close(fig)
figs.append({'number':11,'short':'Recorded order-book depth in three dimensions','caption':f'Recorded order-book depth for {ticker}. Each line is one REST observation; the surface between observations is not reconstructed.'})
pred=read('outputs/tables/frozen-predictions.json'); e=min((x for x in pred if x['hour']==12 and x['phase']=='test' and x['series']=='KXHIGHNY'),key=lambda x:x['date'])
ts=np.linspace(.25,4,45);p=np.array(e['p']);z=np.array([p**(1/t)/sum(p**(1/t)) for t in ts]);X,Y=np.meshgrid(np.arange(1,7),ts)
cmap=LinearSegmentedColormap.from_list('paper',['#f0f8f7','#4db6b2',navy])
fig=plt.figure(figsize=(6.6,4.6));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(X,Y,z,cmap=cmap,linewidth=0,alpha=.95);ax.set(xlabel='Outcome rank',ylabel='Temperature T',zlabel='Probability',zlim=(0,1));ax.view_init(25,-55);fig.subplots_adjust(left=.01,right=.91,bottom=.09,top=.99);fig.savefig(FIG/'figure-12.pdf');plt.close(fig)
figs.append({'number':12,'short':'Probability calibration sensitivity surface','caption':f'Calibration sensitivity for {e["event"]}, the first later-period New York event. T is varied for illustration; the selected research model remains T = 1.'})
ds=np.linspace(0,.15,41);rs=np.linspace(.5,1,41);K=6
def loss(discount,rho):
    ask=(1-discount)/K;cost=ask+.07*ask*(1-ask)
    return sum(math.comb(K,k)*rho**k*(1-rho)**(K-k)*(1 if k*cost>1+1e-12 else 1-k/K) for k in range(1,K+1))
X,Y=np.meshgrid(ds,rs);Z=np.array([[loss(d,r) for d in ds] for r in rs]);cm=LinearSegmentedColormap.from_list('loss',['#eaf5f4','#d6a786','#a9422c'])
fig=plt.figure(figsize=(6.6,4.6));ax=fig.add_subplot(111,projection='3d');ax.plot_surface(X,Y,Z,cmap=cm,linewidth=0);ax.set(xlabel='Gross discount',ylabel='Per-leg fill probability',zlabel='Probability of loss',zlim=(0,1));ax.view_init(25,-55);fig.subplots_adjust(left=.01,right=.91,bottom=.09,top=.99);fig.savefig(FIG/'figure-13.pdf');plt.close(fig)
figs.append({'number':13,'short':'Analytical synthetic loss-probability surface','caption':'Synthetic six-leg loss probability under independent fills, equally likely winning outcomes and raw quadratic fees. This analytical surface is not an empirical return forecast.'})
for x in figs:
    placement='H' if x['number']>=11 else 'htbp'
    t=r'\begin{figure}['+placement+r']\centering'+'\n'+rf'\includegraphics[width=\linewidth,height=87mm,keepaspectratio]{{figures/figure-{x["number"]:02d}.pdf}}'+'\n'+rf'\caption[{esc(x["short"])}]{{{esc(x["caption"])}}}\label{{fig:{x["number"]}}}'+'\n'+r'\end{figure}'+'\n'
    (GEN/f'figure-{x["number"]}.tex').write_text(t)

refs=read('references/references.json')+[{'id':'kalshi2026e','harvard':'Kalshi (2026e) Fee rounding. Available at: https://docs.kalshi.com/getting_started/fee_rounding (Accessed: 17 October 2026).','url':'https://docs.kalshi.com/getting_started/fee_rounding'}]
# Same-author/year suffixes follow title order in the paper bibliography.
for ref in refs:
    suffix={'kalshi2026a':'a','kalshi2026d':'b','kalshi2026e':'c','kalshi2026b':'d','kalshi2026c':'e'}.get(ref['id'])
    if suffix:ref['harvard']=ref['harvard'].replace('('+ref['id'][6:]+')','(2026'+suffix+')')
refs.sort(key=lambda r:r['harvard'].casefold())
import re
entries=[]
for r in refs:
    text=esc(r['harvard'])
    text=re.sub(r'https://[^ ]+',lambda m:r'\url{'+m.group(0).replace(r'\_','_')+'}',text)
    text=re.sub(r'doi: (.*)\.$',lambda m:'doi: '+r'\url{'+m.group(1)+'}.',text)
    entries.append(r'\needspace{44pt}\hypertarget{ref:'+r['id']+r'}{}\noindent\hangindent=15pt\hangafter=1 '+text+r'\par\vspace{3pt}')
(GEN/'references.tex').write_text(r'{\fontsize{10.5}{13.4}\selectfont\setlength{\parskip}{4pt}'+'\n'+'\n'.join(entries)+'\n}\n')
(HERE/'references.json').write_text(json.dumps(refs,indent=2,ensure_ascii=False))

codes=[('fee','kalshi_engine/microstructure.py','execution_fee','Fill rounding and rebate accumulator'),('portfolio','kalshi_engine/arbitrage.py','statewise_portfolio','Statewise portfolio screening'),('calibration','kalshi_engine/probability.py','fit_temperature','Development-only temperature fitting')]
for key,path,name,title in codes:
    source=(ROOT/path).read_text();node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=source.splitlines()[node.lineno-1:node.end_lineno];(CODE/f'{key}.py').write_text('\n'.join(lines)+'\n')
    (GEN/f'code-{key}.tex').write_text(r'\needspace{110pt}\VerbatimInput[fontsize=\fontsize{8.5}{10.3}\selectfont,breaklines=true,breakanywhere=true,frame=single,framesep=5pt,rulecolor=\color{tablerule}]{code/'+key+r'.py}'+'\n'+rf'\codecaption{{{key}}}{{{title}}}'+'\n')

(HERE/'paper-registers.json').write_text(json.dumps({'tables':TABLES,'figures':figs,'equations':eqs,'references':len(refs),'codes':[x[0] for x in codes],'frozen_files':frozen_files},indent=2,ensure_ascii=False))
print(json.dumps({'figures':len(figs),'tables':len(TABLES),'equations':len(eqs),'references':len(refs),'frozen_files_verified':len(frozen_files)},indent=2))
