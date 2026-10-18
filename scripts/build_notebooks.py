"""Create eight nbformat-4 notebooks and actually execute each in a fresh namespace."""
from pathlib import Path
import sys,json,contextlib,io,hashlib,datetime,platform,time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from kalshi_engine.client import ROOT
from kalshi_engine import presentation
SETUP="""from pathlib import Path
import sys, json
root = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'kalshi_engine/client.py').exists())
if str(root) not in sys.path: sys.path.insert(0, str(root))
import numpy as np
import pandas as pd
from kalshi_engine.client import ROOT
from kalshi_engine.presentation import show_table, show_figure, equation, read
from kalshi_engine.microstructure import Book, FeePolicy, sweep, execution_fee
from kalshi_engine.arbitrage import partition_audit, temperature_payoff_states, coherence, basket, statewise_portfolio
from kalshi_engine.probability import normalise, calibrate, scores, fit_temperature, paired_block_interval
print('Kalshi Microstructure Research | recorded public-data study | no order placement')
"""
def md(x):return ('markdown',x.strip())
def code(x):return ('code',x.strip())
books=[
('00_questions_contracts_and_design',[
md('''# 00 · Questions, contracts and research design

How can an engine distinguish a price discrepancy, a model-based expected return, and a payoff that is positive in every admissible state? These are separate questions. The project studies recurring New York, Chicago and Miami temperature contracts, using free REST access and a deliberately narrow, auditable event universe.

As Wolfers and Zitzewitz (2006) explain in *Interpreting prediction market prices as probabilities*, the probability interpretation of a contract price depends on market assumptions. Consequently the model uses a market-derived probability baseline, not an assertion that each quoted cent is the true event probability.'''),code(SETUP),
md('''## Payoffs precede prices

The financial object is the written contract. A short market title is insufficient to infer a payoff identity. The current GLOBALTEMPERATURE terms use full reported precision and permit exceptional fair-value settlement. Six integer-labelled ranges can fail to exhaust a continuous temperature domain. Equations (1), (9) and (10) identify the relevant distinction.'''),
code('''equation(1)
equation(9)
equation(10)
audit = pd.read_csv(ROOT/'outputs/tables/contract-audit.csv')
show_table(audit.groupby('series')[['integer_partition','full_precision_exhaustive','exceptional']].sum().reset_index(), 'Table N00.1. Contract audits across historical and live event groups.')
assert audit.integer_partition.all()
assert not audit.full_precision_exhaustive.any()
print('Normal integer-resolution comparisons are conditional; continuous-state gaps are retained.')'''),
md('''## Chronological evaluation

The design sets 19 July–10 September 2026 for development, 11–28 September for validation, and 29 September–16 October for testing. All cities and all contracts on a date stay in the same phase. Noon local time is the primary observation; 09:00 and 15:00 are sensitivity views. The original protocol and amendment are retained. This is retrospective acquisition with a chronological held-out comparison, not a prospective trading trial.'''),
code('''coverage = pd.read_csv(ROOT/'outputs/tables/coverage.csv')
show_table(coverage[coverage.hour==12].groupby(['phase','status']).size().reset_index(name='events'), 'Table N00.2. Primary noon event coverage by sample.')
show_figure(1)
print('Protocol:', (ROOT/'protocol/01_research_design.md').name)
print('Amendment: A01_api_and_contract_audit.md')'''),
md('''## Milestone outcome

The research questions, payoff assumptions, observation clock, evaluation split and publication sequence are fixed. The research review precedes paper compilation. The final paper retains A4 portrait pages, centred captions, numbered equations and all preliminary lists. Public release of empirical API material is unresolved under the developer agreement; original code and synthetic examples can be prepared independently.''')]),
('01_public_api_data_and_provenance',[
md('''# 01 · Public API data and provenance

Kalshi documents unauthenticated REST access for series, markets and order books. The collector uses GET requests only, bounded retries, source snapshots and request clocks. It has no credential input, portfolio endpoint or order-placement method.

The 90-date universe contains 270 daily events and 1,620 contracts. Historical and live storage tiers must both be queried. Archived candles use different field names from current candles; both encode dollar prices as strings.'''),code(SETUP),
code('''metadata = read('data/processed/metadata.json')
candles = read('data/processed/candles.json')
show_table(pd.DataFrame([{'series':s,'historical_contracts':len(v['markets']),'open_contracts':len(v['open_markets']),'fee_type':v['series']['fee_type'],'multiplier':v['series']['fee_multiplier']} for s,v in metadata.items()]), 'Table N01.1. Acquired series and current fee metadata.')
print('Hourly candlesticks:',sum(len(v) for v in candles.values()))
assert len(candles)==1620
assert sum(len(v) for v in candles.values())==56006'''),
md('''## Information available at the forecast time

Every accepted feature uses a completed hourly candle ending exactly at the decision timestamp. Final prices, final trading volume, expiration values and winners are not predictors. Labels are stored separately. Candles do not provide historical queue position or executable depth, and a quiet trading interval does not prove that its quotes were fresh.'''),
code('''features = read('data/processed/forecast-features.json')
assert all(all(t==e['cutoff_ts'] for t in e['feature_timestamps']) for e in features)
forbidden={'winner','expiration_value','last_price_dollars','volume_fp','open_interest_fp','result'}
assert all(not forbidden.intersection(e) for e in features)
show_table(pd.read_csv(ROOT/'outputs/tables/coverage.csv').groupby(['hour','status']).size().reset_index(name='events'), 'Table N01.2. Inclusion and missing-hour exclusions.')
print('Temporal alignment and feature-field exclusion checks passed.')'''),
md('''## Source integrity and practical failures

The first batch size exceeded the endpoint’s 10,000-candle potential-grid cap. Smaller batches corrected the request without changing the sample. The collector then routed archived markets separately. A concurrent manifest append omitted one index entry, although its complete raw snapshot survived; rebuilding the index from the stored records recovered it. The observed wire hash is an acquisition record; file and canonical-payload hashes independently protect the retained parsed JSON.'''),
code('''import hashlib
index = read('outputs/validation/source-snapshot-index.json')
for row in index:
    assert hashlib.sha256((ROOT/row['file']).read_bytes()).hexdigest()==row['snapshot_sha256']
print('Verified stored source snapshots:',len(index))
print('Distinct live payloads:',read('outputs/supplementary-results.json')['book_payload_hashes'])
print('Raw API data are private research inputs; no public-data licence is inferred.')''')]),
('02_order_books_fees_and_liquidity',[
md('''# 02 · Order books, fees and liquidity

As Glosten and Milgrom (1985) show in their study of informed trading, a bid–ask spread can arise from information asymmetry. A discrepancy measured at the midpoint is therefore not a trade available at that price. As Hasbrouck (2007) discusses in *Empirical market microstructure*, trading mechanisms and execution costs must be represented explicitly.

Kalshi returns bids on YES and NO. A NO bid at 0.58 supplies a YES ask at 0.42 with the same quantity. Levels are sorted explicitly, with decimal arithmetic preserving fractional quantities.'''),code(SETUP),
code('''equation(2)
equation(3)
equation(4)
equation(5)
example = Book.from_payload({'yes_dollars':[['0.40','7.25']],'no_dollars':[['0.58','4.50']]})
assert float(example.asks('yes')[0][0])==0.42
show_table(pd.DataFrame([example.metrics()]), 'Table N02.1. Complement reconstruction and displayed-depth metrics.')
show_figure(2)'''),
md('''## Quantity and fee rounding

The current general taker fee is quadratic in price and uses the series multiplier. The rounding guide distinguishes direct-member balance precision from non-direct-member precision and carries rounding overpayment across order fills. Price-level aggregation is not a record of counterparty fill fragmentation; scenario assumptions remain explicit.'''),
code('''from decimal import Decimal
rows=[]
for precision in ['0.0001','0.01']:
    policy=FeePolicy(balance_precision=Decimal(precision))
    rows.append({'balance_precision':precision,'one_contract_fee':float(execution_fee([('0.5','1')],policy)),'100_separate_fills_same_order':float(execution_fee([('0.5','1')]*100,policy))})
show_table(pd.DataFrame(rows), 'Table N02.2. Fee rounding and the order accumulator at a 0.50 price.')
equation(6)
equation(7)
equation(8)
assert not sweep(example,'yes',5)['fillable']
show_figure(6)'''),
md('''## Snapshot imbalance has a limited interpretation

As Cont, Kukanov and Stoikov (2014) describe in *The price impact of order book events*, changes in supply and demand at the best quotes relate to price changes. The present pilot measures displayed depth imbalance from snapshots; it does not reconstruct their event-based order-flow imbalance. Twenty batch responses are too brief to support a forecasting or causal claim.'''),
code('''live=read('outputs/live-results.json')
show_table(pd.DataFrame({'measure':list(live),'value':list(live.values())}), 'Table N02.3. Live collection summary; spans describe HTTP observation uncertainty.')
show_figure(7)
assert live['book_snapshots']==720
print('No per-book exchange timestamp, queue position or market-wide tick history was observed.')''')]),
('03_payoff_constraints_and_arbitrage',[
md('''# 03 · Payoff constraints and arbitrage

As Boyd and Vandenberghe (2004) explain in *Convex optimization*, linear constraints can express feasible portfolios. Here a finite-state linear programme maximises the lowest state payoff after costs, with budget and displayed-depth bounds. The optimisation is only as reliable as its state matrix and execution assumptions.

Synthetic validation tests logic separately from the empirical market scan. All results below distinguish conditional ordinary-resolution baskets from a claim of guaranteed execution.'''),code(SETUP),
code('''equation(10)
equation(11)
A=np.eye(3)
known=statewise_portfolio(A,[.3,.3,.3],[10,10,10],budget=100)
assert abs(known['worst_profit']-1)<1e-8
with_gap=statewise_portfolio(np.vstack([A,np.zeros(3)]),[.3,.3,.3],[10,10,10],budget=100)
assert abs(with_gap['worst_profit'])<1e-8
show_table(pd.DataFrame([{'state_set':'Three exhaustive outcomes','worst_profit':known['worst_profit']},{'state_set':'Plus a no-winner state','worst_profit':with_gap['worst_profit']}]), 'Table N03.1. A missing payoff state can create a false arbitrage certificate.')'''),
code('''summary=pd.read_csv(ROOT/'outputs/tables/synthetic-summary.csv')
show_table(summary, 'Table N03.2. Known-truth outcomes from 3,000 synthetic scenario evaluations.')
assert (summary.accuracy==1).all()
show_figure(8)
print('Five hundred paired probability draws across six scenarios; not 3,000 independent markets.')'''),
md('''## What the acquired sample shows

The hourly historical panel produces apparent gross basket discrepancies, but fees remove them under the stated current-fee scenario. Historical quote summaries cannot supply missing depth or enforce simultaneous fills. The brief live sample contains no positive cost-adjusted basket candidate or statewise portfolio profit. This does not establish the absence of opportunities elsewhere or at other times.'''),
code('''supp=read('outputs/supplementary-results.json');live=read('outputs/live-results.json')
show_table(pd.DataFrame([{'measurement':'Historical gross quote-only gaps','count':supp['gross_positive_quote_baskets']},{'measurement':'Historical gaps after current fee scenario','count':supp['net_positive_current_fee_scenario']},{'measurement':'Live positive conditional baskets','count':live['conditional_basket_candidates']},{'measurement':'Live positive rechecked statewise LP','count':live['positive_rechecked_lp']}]), 'Table N03.3. Distinct screens; historical and live rows are not one execution funnel.')
show_figure(3)''')]),
('04_probability_modelling_and_selection',[
md('''# 04 · Probability modelling and model selection

A normalised midpoint vector is a transparent market-derived baseline, conditional on a single winning outcome. A one-parameter power transformation tests whether the market vector is too concentrated or too diffuse. As Guo et al. (2017) discuss in *On calibration of modern neural networks*, temperature scaling can adjust concentration. This project adapts that transformation to market-derived log probabilities; it trains no neural network and imports no claim about predictive improvement.

As Gneiting and Raftery (2007) explain in *Strictly proper scoring rules, prediction, and estimation*, probabilistic forecasts should be evaluated as distributions. The evaluation therefore uses log loss and Brier score rather than accuracy alone.'''),code(SETUP),
code('''equation(12)
equation(13)
equation(14)
equation(15)
features=read('data/processed/forecast-features.json');labels={(x['event'],x['hour']):x['winner'] for x in read('data/processed/outcomes.json')}
dev=[e|{'winner':labels[(e['event'],e['hour'])]} for e in features if e['hour']==12 and e['phase']=='development']
fresh=fit_temperature(dev);frozen=read('protocol/model-freeze.json')
assert abs(fresh['temperature']-frozen['temperature'])<1e-8
show_table(pd.DataFrame([{'development_temperature':fresh['temperature'],'validation_baseline_log_loss':frozen['validation_baseline_loss'],'validation_candidate_log_loss':frozen['validation_candidate_loss'],'selected_temperature':frozen['chosen_temperature']}]), 'Table N04.1. Recomputed development fit and frozen validation choice.')'''),
md('''## The selection rule can keep the simpler model

The fitted temperature is close to one. Its small development improvement does not carry into validation, so the declared rule selects the unchanged baseline. The later sample is scored only after the predictions and configuration are written and hashed. Keeping the baseline is a model-selection result, not a reason to tune a new family on the test outcomes.'''),
code('''import hashlib
assert hashlib.sha256((ROOT/'outputs/tables/frozen-predictions.json').read_bytes()).hexdigest()==frozen['prediction_hash']
assert frozen['chosen_temperature']==1
p=np.array([.05,.10,.20,.35,.20,.10])
show_table(pd.DataFrame({'outcome':range(1,7),'baseline':p,'T=0.5':calibrate(p,.5),'T=2':calibrate(p,2)}), 'Table N04.2. Synthetic calibration sensitivity; every column sums to one.')
print('Freeze time:',frozen['frozen_utc'])
print('Probability model uses market quotes; it is not an independent meteorological forecast.')'''),
code('''show_figure(4)
show_figure(5)
print('The Brier convention sums squared errors across outcomes within each event.')''')]),
('05_chronological_validation_and_value',[
md('''# 05 · Chronological validation and model-based value

As Brier (1950) proposed in *Verification of forecasts expressed in terms of probability*, squared probability error provides a forecast-quality measure. Here the sum is taken over the six outcomes of each event. All models are compared on the same later events.

The selected model is the baseline itself, so its difference from the baseline is zero apart from numerical precision. Comparisons with the rejected calibration candidate are supplementary; they are not a new selection step.'''),code(SETUP),
code('''pred=read('outputs/tables/frozen-predictions.json');labels={(x['event'],x['hour']):x['winner'] for x in read('data/processed/outcomes.json')}
test=[e for e in pred if e['phase']=='test' and e['hour']==12]
rows=[]
for e in test:
    y=labels[(e['event'],12)]
    for model,key in [('baseline','p'),('candidate','candidate_p')]:rows.append({'event':e['event'],'date':e['date'],'model':model,**scores(e[key],y)})
df=pd.DataFrame(rows)
show_table(df.groupby('model')[['log_loss','brier']].mean().reset_index(), 'Table N05.1. Independently recomputed held-out noon scores.')
assert len(test)==53
assert len({e['date'] for e in test})==18'''),
md('''## Dependence and uncertainty

As Künsch (1989) develops in *The jackknife and the bootstrap for general stationary observations*, resampling neighbouring observations can preserve some serial dependence. The project resamples blocks of calendar-date average paired losses. Cities on a date remain together. Three-day blocks are primary; one- and five-day blocks are sensitivities. Eighteen later dates provide limited support, and weather or source changes can violate stationary approximations.'''),
code('''equation(17)
wide=df.pivot(index=['date','event'],columns='model',values='log_loss')
diffs=(wide.candidate-wide.baseline).groupby(level='date').mean().sort_index()
interval=paired_block_interval(diffs.values,draws=1999,block=3)
show_table(pd.DataFrame([interval]), 'Table N05.2. Paired date-block interval for the rejected candidate, conditional on the frozen fit.')
show_figure(10)'''),
md('''## Expected edge is a different quantity

Equation (16) compares a model probability with acquisition cost. A positive expectation is not a statewise payoff guarantee. The supplementary historical value screen assumes one contract at an hourly ask and a current raw-fee scenario. With no historical depth, queue information or fills, it is not a tradable backtest. The two-cent screen is exploratory and does not determine the primary model selection.'''),
code('''equation(16)
value=read('outputs/probability-results.json')['value_diagnostic']
show_table(pd.DataFrame({'measure':list(value),'value':list(value.values())}), 'Table N05.3. Exploratory candle-ask value diagnostic; no execution claim.')
print('Independent future data are needed before any claim of persistent model-based value.')''')]),
('06_execution_risk_and_research_reflections',[
md('''# 06 · Execution risk and research reflections

As Avellaneda and Stoikov (2008) explain in *High-frequency trading in a limit order book*, inventory and execution considerations matter when managing limit orders. The present study does not estimate their model. Its execution experiment instead makes a simple, inspectable assumption: each basket leg fills independently with a chosen probability, while unfilled legs leave the acquired positions exposed.

This synthetic experiment illustrates why a favourable basket quote is insufficient to guarantee the portfolio will be acquired.'''),code(SETUP),
code('''equation(18)
n=6
show_table(pd.DataFrame([{'per_leg_fill_probability':r,'all_six_fill_probability':r**n} for r in [.5,.7,.85,.95,1]]), 'Table N06.1. Synthetic all-leg completion under independent fills.')
stress=pd.read_csv(ROOT/'outputs/tables/execution-stress.csv')
show_table(stress[np.isclose(stress.adverse_entry_cost,0)][['fill_probability','all_leg_fill_rate','loss_rate','mean_pnl','p05']], 'Table N06.2. Simulated incomplete-basket outcomes at the original entry prices.')
show_figure(9)'''),
md('''## What did not work, and why

The first candle-batch size failed because the API caps the potential grid, not just nonempty rows. Smaller batches repaired acquisition. Archived and current schemas differed, requiring explicit adapters. One manifest index entry was lost during concurrent writes; the raw snapshot was intact and the recovered file-hash index verifies the complete cache.

Rounded bucket labels failed as an unconditional proof of exhaustiveness: the written terms use full source precision. The payoff-state matrix now retains fractional-temperature gaps, while fair-value fallback remains unresolved. Faster HTTP polling would not remove either contractual issue.

Temperature scaling improved development fit but failed validation. The baseline was retained. The live session was too short and lacked queue information, so fill probabilities remain synthetic. None of these issues is hidden by reporting a profitable backtest.'''),
code('''supp=read('outputs/supplementary-results.json')
show_table(pd.DataFrame([{'issue':'Manifest indexing','finding':str(supp['parallel_manifest_missing_entries'])+' recovered missing entry; stored snapshots verified'},{'issue':'Full-precision exhaustiveness','finding':str(supp['continuous_partition_events'])+' events passed the strict partition condition'},{'issue':'Calibration selection','finding':'Baseline selected before test scoring'},{'issue':'Execution','finding':'No empirical fill probability; hypothetical stresses only'},{'issue':'Public release','finding':'API-data permissions remain unresolved'}]), 'Table N06.3. Actual failures, mitigations and remaining limits.')'''),
md('''## A stronger next experiment

A prospective sample would freeze the scanner before collecting a longer, representative sequence, retain exchange-timestamped updates where access is permitted, and record settlement-rule versions. An external forecast must have a verified publication time and compatible settlement target. Each improvement addresses a different identification problem; a more flexible statistical model cannot replace missing execution evidence.'''),
code('''results=read('outputs/probability-results.json')
show_table(pd.DataFrame(results['city_scores']), 'Table N06.4. Later-period noon scores by city; descriptive subgroup comparison.')
print('Additional hours and block lengths are sensitivity analyses, not additional independent successes.')''')]),
('07_synthesis_and_publication_registers',[
md('''# 07 · Synthesis and publication registers

The project is an implemented public-API research engine with explicit contracts, costs and probabilistic evaluation. It finds quote-level discrepancies while preventing those discrepancies from becoming unsupported claims of profitable arbitrage. The completed research package includes executed notebooks, source records, tests, static figures and three interactive explorers.

The empirical result is narrow: the sampled gross historical gaps do not survive the stated fee scenario; the short live sample yields no net candidate; the calibration candidate fails the validation rule. These findings do not establish universal market efficiency or the impossibility of profitable models.'''),code(SETUP),
code('''show_table(pd.DataFrame([{'item':'Historical event dates','count':90},{'item':'Historical events','count':270},{'item':'Historical contracts','count':1620},{'item':'Hourly candles','count':56006},{'item':'Accepted primary noon events','count':268},{'item':'Later noon events','count':53},{'item':'Live book observations','count':720},{'item':'Synthetic scenario checks','count':3000}]), 'Table N07.1. Research evidence inventory.')
print('Original design, amendment, frozen model and frozen predictions are preserved.')'''),
code('''equations=read('paper/equations.json')
show_table(pd.DataFrame(equations)[['number','caption']], 'Table N07.2. Numbered equation register for final paper assembly.')
show_table(pd.read_csv(ROOT/'paper/abbreviations.csv'), 'Table N07.3. Abbreviations.')
show_table(pd.read_csv(ROOT/'paper/mathematical-symbols.csv'), 'Table N07.4. Mathematical notation.')'''),
md('''## Publication sequence

The paper is assembled after this notebook review. Its layout retains the established title page, abstract, contents, lists of figures, tables and equations, abbreviations and symbols, numbered equations, Harvard bibliography, centred captions and A4 portrait pages. The discussion includes actual research failures and remaining limits. GitHub publication, the landing page, graph page and thumbnails follow the paper stage, subject to the empirical-data permissions issue.'''),
code('''show_table(pd.DataFrame(read('paper/figures.json'))[['number','caption']], 'Table N07.5. Figure register.')
refs=read('references/references.json')
print('Harvard reference entries:',len(refs))
print((ROOT/'references/harvard-references.txt').read_text())
print('Final paper has not been compiled. This is the research-review handover.')''')])]

def main():
 manifest=[];tables=[]
 for slug,parts in books:
  cells=[];namespace={'__name__':'__main__'};count=0;start=time.time()
  for kind,source in parts:
   ident=hashlib.sha1((slug+source).encode()).hexdigest()[:12]
   if kind=='markdown':cells.append(dict(cell_type='markdown',id=ident,metadata={},source=source.splitlines(True)));continue
   count+=1;out=[];buf=io.StringIO();presentation.set_sink(lambda b:out.append(dict(output_type='display_data',data=b,metadata={})))
   with contextlib.redirect_stdout(buf),contextlib.redirect_stderr(buf):exec(compile(source,f'{slug}:cell-{count}','exec'),namespace)
   if buf.getvalue():out.append(dict(output_type='stream',name='stdout',text=buf.getvalue().splitlines(True)))
   cells.append(dict(cell_type='code',id=ident,metadata={},source=source.splitlines(True),execution_count=count,outputs=out))
   for o in out:
    h=o.get('data',{}).get('text/html','')
    if 'Table N' in h:
     import re
     match=re.search(r'(Table N\d+\.\d+\..*?)</p>',h)
     if match:tables.append({'notebook':slug,'caption':match.group(1)})
  presentation.set_sink(None)
  nb=dict(nbformat=4,nbformat_minor=5,cells=cells,metadata={'kernelspec':{'name':'python3','display_name':'Python 3','language':'python'},'language_info':{'name':'python','version':platform.python_version()},'research':{'executed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'runner':'scripts/build_notebooks.py; actual cell execution in a fresh namespace','status':'executed'}})
  p=ROOT/'notebooks'/(slug+'.ipynb');p.write_text(json.dumps(nb,ensure_ascii=False,indent=1))
  manifest.append(dict(notebook=str(p.relative_to(ROOT)),title=parts[0][1].splitlines()[0].lstrip('# '),executed_code_cells=count,status='complete',seconds=time.time()-start))
  print(slug,count,'executed code cells',flush=True)
 (ROOT/'outputs/validation/notebook-execution.json').write_text(json.dumps(manifest,indent=2))
 (ROOT/'paper/tables.json').write_text(json.dumps(tables,indent=2))
 (ROOT/'protocol/milestones.json').write_text(json.dumps([dict(id='M'+str(i+1),**r) for i,r in enumerate(manifest)],indent=2))
if __name__=='__main__':main()
