# Mispricing and Arbitrage in Prediction Markets

Working subtitle: Probability coherence, order-book liquidity and execution costs on Kalshi.

Author: Joel Cerraga. Project opened 17 October 2026.

## Research questions and distinct claims

1. Can a public-data engine identify payoff inconsistencies in related contracts, and which candidates survive fees, available depth, non-simultaneous observations and settlement uncertainty?
2. Can a calibrated probabilistic model improve the proper scoring rules of a market-derived baseline on later, previously unscored observations?
3. How do spreads, imbalance, depth and execution assumptions change apparent opportunities?

Statistical model disagreement is not arbitrage. A structural candidate must have a strictly positive worst-state payoff after purchase costs and fees for a verified set of payoff states. Actual execution is a further claim requiring fills on every leg. This project is a research scanner and paper-execution laboratory, with no order-placement interface.

## Scope frozen before the historical outcome analysis

Public, unauthenticated REST endpoints. Initial series: KXHIGHNY (New York), KXHIGHCHI (Chicago), KXHIGHMIA (Miami). Choice is motivated by recurring events and ordered, normally exhaustive temperature ranges, not observed profitability. Primary historical window: 19 July–16 October 2026 (90 event dates). Sample limitations and endpoint changes will be retained as amendments.

Primary forecast observation: 12:00 event-city local time, using the final completed hourly candle ending no later than that time. Additional 09:00 and 15:00 observations are descriptive sensitivity checks. No future candle, settlement value, final volume or final open interest enters model features. Historical candles contain quote summaries, not depth, queue position or executable fills. Neither historical spread checks nor candles prove arbitrage.

Development dates: 19 July–10 September. Validation: 11–28 September. Test: 29 September–16 October. All contracts from an event and all cities on a date remain in the same split. Development fits use only development outcomes; model choice uses validation; frozen predictions precede inspection of test scores. Keep final prediction hashes and algorithm configuration. Because this is retrospectively acquired public history, call it chronological held-out evaluation, not a preregistered prospective trial.

Baseline: normalised positive midpoint probabilities for a complete event. Model: one-parameter temperature/power calibration on the simplex, with log probability scaled by inverse temperature. Compare development-optimised temperature with the unchanged baseline on validation; use the lower validation multiclass log loss, preferring baseline on ties. Report multiclass log loss and Brier score per event, with paired moving-block bootstrap by calendar date (three-day blocks, 1,999 draws) and city-specific sensitivity. Missing or invalid complete-event probabilities are excluded with reasons; no outcome-driven removal. A minimum of 30 development events and 15 test dates is required for inferential reporting; otherwise descriptive pilot only.

Live order books: capture repeated complete-event sweeps. Store request start/finish, HTTP date, fixed-point prices and quantities, raw hashes and series fee metadata. A sweep is not atomic; do not claim executable arbitrage from it. A 2-second maximum cross-leg acquisition span is the strict simultaneity gate, with broader bounds descriptive only. Date and season effects cannot be inferred from one collection session.

## Engine and validation

Parse decimal-dollar and fractional-contract strings with Decimal; sort levels explicitly rather than trust inconsistent ordering documentation. Derive YES asks as one minus NO bids, and vice versa. Sweep displayed asks to calculate quantity-dependent cost; refuse insufficient depth. Fees use verified series fee type/multiplier, contemporary rounding policy and conservative fill fragmentation sensitivity. Historical fee assumptions are scenarios unless dated schedules are verified.

Payoff matrix checks: complement identity; complete mutually exclusive outcome baskets; nested-event dominance; general statewise long-only linear-programming search with finite depth. Same-contract opposite positions cannot create independent resources through double-counting. Ordinary weather states may partition integer temperature outcomes, but exceptional fair-value resolution can invalidate the fixed-sum guarantee. Keep separate ordinary-resolution and exceptional-resolution stress results. Unverified rules block a strict arbitrage label.

Synthetic tests include true opportunities, fee-erased gaps, insufficient depth, unsynchronised quotes, non-exhaustive baskets, fractional sizes, scalar outcomes and partial-leg execution. Synthetic illustrations and observed results remain explicitly labelled.

## Reporting and workflow

Work through the research milestones, then present the notebooks and milestone review before final paper compilation. The final publication follows the established sequence: paper review, then GitHub repository, landing page, separate interactive-graphs page and individual page thumbnails.

Paper layout: A4 portrait, title page, abstract, contents, lists of figures/tables/equations, abbreviations and mathematical symbols; numbered equations and centred captions beneath figures, tables and equations; compact page flow. Narrative scholarly attribution leads into the research relationships. Reference list contains Harvard entries only. Discussion records actual failures, their causes, attempted corrections and residual limitations. Public prose describes the research itself.
