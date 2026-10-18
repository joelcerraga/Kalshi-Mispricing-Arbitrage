# Working research argument

These notes support later paper assembly. They are not a compiled paper.

## Contribution

The contribution is a research engine that keeps contractual payoff logic, probabilistic modelling and execution costs distinct. It operates on recurring temperature markets because the underlying outcomes can be ordered and their written boundaries inspected. The evidence is deliberately narrower than an unrestricted prediction-market trading system.

As Wolfers and Zitzewitz (2006) discuss in *Interpreting prediction market prices as probabilities*, price-to-probability interpretation requires assumptions. The baseline is therefore described as market-derived. As Hasbrouck (2007) explains in *Empirical market microstructure*, observed prices and the costs of acquiring positions are separate measurement objects. The engine reconstructs asks from opposite-side bids and sweeps available quantity before considering a net payoff.

## Data and research design

The historical universe covers 270 daily events across three cities, with six contracts per event, from 19 July to 16 October 2026. Public REST acquisition returns 56,006 hourly candles. The primary completed-hour observation is noon in each city’s local timezone; 268 complete six-contract panels survive. The development, validation and test counts are 162, 53 and 53. The later sample spans 18 dates. Separate 09:00 and 15:00 observations test timing sensitivity.

Markets are joined to later outcomes for scoring, but settlement values, final volume and final prices are excluded from model features. Entire dates remain in one chronological split. The model freeze records the protocol, implementation, input and prediction hashes before test scoring. This is a retrospective chronological comparison, not an untouched prospective experiment.

The live pilot comprises 20 batch responses over approximately three minutes, covering 36 contracts in six daily events and yielding 720 book observations. The recorded payload changes across all 20 responses. The endpoints do not supply a per-book exchange timestamp. HTTP round-trip spans cannot be interpreted as exchange processing latency or assumed simultaneous snapshots.

## Contractual reasoning

Kalshi’s current GLOBALTEMPERATURE terms use the source’s full reported precision. Six integer-labelled buckets can partition integer temperatures while leaving gaps between adjacent boundaries under a continuous reading. The statewise matrix retains all distinct endpoint and between-endpoint payoff states. Fair-value fallback introduces an additional payout contingency that is not certified by the ordinary temperature-state matrix.

As Boyd and Vandenberghe (2004) explain in *Convex optimization*, a linear programme can express resource and payoff constraints. The project uses a finite-state maximin portfolio programme with depth and budget bounds. Continuous quantities and raw fee slopes provide a screening relaxation; the implementation floors sizes to the quantity grid and recalculates costs before reporting a numerical candidate. No mathematical optimiser can make omitted contract states valid or guarantee that separate legs will execute.

## Microstructure and costs

As Glosten and Milgrom (1985) explain in their model of informed trading, spreads can arise even with competitive, risk-neutral liquidity provision. A midpoint discrepancy need not imply an obtainable return. The fee model follows the current quadratic schedule, series multiplier, fill-level rounding and order-level rebate accumulator. Historical calculations using that schedule are cost scenarios because the complete dated fee regime has not been certified.

As Cont, Kukanov and Stoikov (2014) analyse in *The price impact of order book events*, depth and order-flow changes matter for short-horizon prices. The available pilot measures snapshot depth imbalance rather than event-by-event order-flow imbalance. Its exploratory correlation with the next observed midpoint change is about 0.0355, and is not evidence of an executable forecast.

The live basket audit contains 720 side/quantity checks. Of these, 378 have enough displayed depth for the requested complete basket and show no positive net gap; 342 fail the depth requirement. Forty-six complete two-sided event observations support the general payoff programme, and none produces a positive rechecked profit. These denominators are distinct from 720 individual market-book observations.

## Probability modelling and results

As Guo et al. (2017) describe in *On calibration of modern neural networks*, temperature scaling adjusts the concentration of a probability vector. The project applies the mathematical transformation to log market-derived probabilities; it does not fit a neural network or an independent weather forecast. As Gneiting and Raftery (2007) explain in *Strictly proper scoring rules, prediction, and estimation*, full predictive distributions can be evaluated using proper scores. Log loss and the multiclass Brier score therefore provide the primary comparison.

The fitted development temperature is 1.0344, close to the identity transformation. The candidate’s validation log loss is 0.819043 versus 0.813803 for the baseline, so the frozen rule retains the baseline. On later noon events, baseline log loss is 0.718589 and Brier score is 0.408273. The rejected candidate records 0.722152 and 0.409355 respectively. The candidate comparison is supplementary; it does not trigger a new model search.

As Brier (1950) proposed in his forecast-verification paper, squared probability errors summarise probability accuracy. This study sums errors over outcomes within an event. As Künsch (1989) develops for dependent observations, block resampling can preserve local dependence. The implementation resamples three-day blocks of paired calendar-date mean loss differences, with one- and five-day sensitivity checks. Eighteen test dates and possible seasonal shifts limit those intervals. A score improvement would still be distinct from a trading-profit claim.

## Structural and execution findings

The historical noon quotes contain 34 positive gross conditional basket gaps. None survives the stated current-fee scenario. Historical candles lack depth, contemporaneous multi-leg availability and fill records, so these counts are quote diagnostics. The live sample likewise contains no positive cost-adjusted basket or statewise portfolio candidate. These are sample results, not a general proof of prediction-market efficiency.

Synthetic validation uses 500 probability draws across six mechanisms, producing 3,000 scenario checks. The tested logic distinguishes genuine opportunities within the supplied state set from fees, insufficient depth, asynchronous observation and exceptional settlement. Perfect classification within this small designed family does not establish broad external reliability.

As Avellaneda and Stoikov (2008) discuss in their limit-order-book model, inventory and execution influence trading decisions. The project’s separate experiment uses explicitly synthetic independent leg fills. An attractive expected payoff can coexist with losses when only some legs execute. Twenty thousand draws per fill setting are reused across cost stresses; these are not estimated Kalshi fill probabilities.

## Reflection and remaining work

The initial batch size failed against the API’s potential-grid cap. Smaller batches repaired acquisition without changing the event sample. Archived and current data used different field names, so adapters now distinguish their schemas explicitly. A concurrent manifest append omitted one index entry; the intact raw snapshot enabled a complete rebuilt, file-hashed index. These are implemented corrections, not hypothetical checklist items.

The assumption that integer-labelled buckets establish an unconditional fixed payoff failed the contract review. Full-precision states were added, while exceptional settlement remains an unresolved boundary of certification. The calibration candidate failed validation and was rejected. The short live session cannot identify durable opportunity frequency, queue dynamics or execution probabilities.

The developer agreement restricts collection/storage, data sharing and public references. The retained material is a private research review, with no public release represented as cleared. A public empirical paper or dashboard needs a specific rights decision. Original software and synthetic examples can be prepared separately, but do not themselves establish permission for empirical redistribution.

The next stronger empirical stage would collect a prospective, sufficiently long sample after the scanner and inclusion rules are frozen, retain permitted exchange-timestamped order-book updates, and use any external forecasts only with verified issue times and settlement-source compatibility. These improvements address the actual limits of this study.
