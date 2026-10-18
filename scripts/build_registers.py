from pathlib import Path
import json,csv
ROOT=Path(__file__).resolve().parents[1]
eq=[
('Binary payoff',r'X_i(\omega)=\mathbf{1}\{\omega\in A_i\},\qquad X_i^{N}(\omega)=1-X_i(\omega)','A_i is the precisely defined event, not its abbreviated market title.'),
('Complementary order-book quotes',r'a_i^Y=1-b_i^N,\qquad a_i^N=1-b_i^Y','Prices in dollars per unit-payout contract.'),
('Quoted spread and midpoint',r's_i=a_i^Y-b_i^Y,\qquad m_i=(a_i^Y+b_i^Y)/2','A midpoint is a descriptive reference, not an available execution price.'),
('Displayed depth imbalance',r'I_i=(D_i^b-D_i^a)/(D_i^b+D_i^a)','Snapshot imbalance; distinct from order-flow imbalance measured across order events.'),
('Depth-weighted midpoint',r'\widetilde m_i=(a_i^Y D_i^b+b_i^Y D_i^a)/(D_i^b+D_i^a)','A descriptive weighting, not an estimated efficient-price model.'),
('Depth-aware acquisition cost',r'C_i(q)=\sum_{\ell}p_{i\ell}q_{i\ell},\qquad\sum_{\ell}q_{i\ell}=q','Use ascending asks and reject quantities exceeding displayed depth.'),
('Quadratic taker fee before rounding',r'f_i=0.07M_i\sum_{\ell}q_{i\ell}p_{i\ell}(1-p_{i\ell})','Current schedule scenario; actual fee adds fill-level rounding and order rebates.'),
('Fee and balance rounding',r'f_{\ell}^{net}=\lceil f_{\ell}^{model}\rceil_{10^{-6}}+r_{\ell}-R_{\ell}','r is balance-alignment rounding; R is the order-accumulator rebate. See code for the recurrence.'),
('Conditional probability coherence',r'\sum_i b_i^Y\leq1\leq\sum_i a_i^Y','Only for a verified mutually exclusive and exhaustive unit-payoff partition, before fees.'),
('Statewise net payoff',r'\Pi(\omega;\mathbf q)=\sum_i X_i(\omega)q_i-\sum_i[C_i(q_i)+F_i(q_i)]','A guarantee depends on covering every contractually possible payout state.'),
('Finite-state portfolio programme',r'\max_{\mathbf q,g}g\quad\mathrm{s.t.}\quad A\mathbf q-\mathbf c^T\mathbf q\,\mathbf1\geq g\mathbf1,\quad0\leq\mathbf q\leq\mathbf d,\quad\mathbf c^T\mathbf q\leq B','Continuous screening relaxation; recheck rounded sizes and exact costs after optimisation.'),
('Market-derived baseline',r'p_i=\max(m_i,\epsilon)/\sum_j\max(m_j,\epsilon)','Normalised reference on the observed single-winner event universe; epsilon = 0.0001.'),
('Probability temperature calibration',r'\widehat p_i(T)=\frac{\exp(\log p_i/T)}{\sum_j\exp(\log p_j/T)}','T is fitted on development outcomes; the model choice is made on validation loss.'),
('Multiclass logarithmic loss',r'L_{\log}=-\frac1N\sum_e\log\widehat p_{e,y_e}','Lower is better; natural logarithms give nats per event.'),
('Multiclass Brier score',r'L_B=\frac1N\sum_e\sum_i(\widehat p_{ei}-\mathbf1\{y_e=i\})^2','Sum across event outcomes; lower is better.'),
('Model-based expected edge',r'\widehat V_i(q)=q\widehat p_i-C_i(q)-F_i(q)','A probabilistic expected value, not a guaranteed payoff.'),
('Date-paired score difference',r'\overline\Delta=\frac1D\sum_d\frac1{n_d}\sum_{e\in d}(L_e^{model}-L_e^{base})','Negative favours the model. Moving-block bootstrap resamples paired calendar-date means.'),
('Synthetic complete-basket fill probability',r'\Pr(\mathrm{all\ legs\ fill})=\rho^K','Independent equal-probability fills are an illustrative stress assumption only.')]
(ROOT/'paper/equations.json').write_text(json.dumps([dict(number=i+1,caption=t,latex=x,note=n) for i,(t,x,n) in enumerate(eq)],indent=2))
syms=[('X_i','Contract payoff in dollars'),('omega','Resolution state'),('A_i','Event defined by contract i'),('b_i','Best bid'),('a_i','Best ask'),('s_i','Quoted spread'),('m_i','Midpoint'),('D_i^b, D_i^a','Displayed bid and ask quantity'),('I_i','Displayed depth imbalance'),('q_i','Contract quantity'),('p_i','Market-derived probability; p_i,l denotes fill price only when indexed by level'),('C_i','Purchase cost'),('F_i','Rounded fee'),('M_i','Series fee multiplier'),('Pi','Portfolio net payoff'),('A','State-by-contract payoff matrix'),('B','Cost budget'),('g','Worst-state net payoff'),('T','Calibration temperature'),('epsilon','Probability floor'),('y_e','Observed winning outcome'),('N','Number of events'),('D','Number of dates'),('Delta','Paired loss difference'),('rho','Synthetic per-leg fill probability'),('K','Number of basket legs')]
with (ROOT/'paper/mathematical-symbols.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['symbol','meaning']);w.writerows(syms)
abbr=[('API','Application programming interface'),('REST','Representational state transfer'),('HTTP','Hypertext Transfer Protocol'),('UTC','Coordinated Universal Time'),('NYC','New York City'),('NWS','National Weather Service'),('TWC','The Weather Company'),('OHLC','Open, high, low and close'),('VWAP','Volume-weighted average price'),('LP','Linear programming'),('CI','Confidence interval'),('CSV','Comma-separated values'),('JSON','JavaScript Object Notation'),('SHA-256','Secure Hash Algorithm, 256-bit'),('PnL','Profit and loss'),('FCM','Futures commission merchant')]
with (ROOT/'paper/abbreviations.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['abbreviation','meaning']);w.writerows(abbr)
print('Registered',len(eq),'equations,',len(syms),'symbols and',len(abbr),'abbreviations')
