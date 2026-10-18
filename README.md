# Pricing Uncertainty

**Joel Cerraga · Kalshi Mispricing and Arbitrage Research**

A Python research engine for probability modelling, order-book microstructure and conditional arbitrage screening. It asks whether a quoted discrepancy survives fees, available depth, payoff constraints and chronological validation.

[![Pricing Uncertainty by Joel Cerraga](assets/thumbnails/pricing-uncertainty.jpg)](https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/)

[Project overview](https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/) · [Interactive graphs](https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/explorers/) · [Final paper](paper/final/Kalshi-Mispricing-and-Arbitrage-Final-Paper.pdf) · [Eight notebooks](https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/notebooks/)

**Public research release:** [Pricing Uncertainty](https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/) introduces the project, and [Probability in Motion](https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/explorers/) contains the interactive graphs. This repository includes the paper, executed notebooks, original software, synthetic experiments and selected empirical material. The complete raw-data archive is retained privately. See [DATA_AND_SOFTWARE_RIGHTS.md](DATA_AND_SOFTWARE_RIGHTS.md).

## Research at a glance

| Component | Scope |
| --- | --- |
| Historical sample | 270 daily temperature events, 1,620 contracts and 56,006 hourly candles |
| Cities and dates | New York, Chicago and Miami; 19 July–16 October 2026 |
| Primary panels | 268 complete noon events: 162 development, 53 validation, 53 later events |
| Live pilot | 720 individual book observations in 20 REST batches over 166.12 seconds |
| Methods | Fixed-point books, depth sweeps, fill-level fee rounding, payoff-state constraints, linear programming, temperature calibration and date-block intervals |
| Synthetic validation | Six mechanisms with 500 paired replications each; 3,000 scenario evaluations |
| Deliverables | 39-page paper, eight executed notebooks, three 3D explorers, 45 analytical tests |

## Main findings

- **34 historical gross basket gaps; none positive after the stated fee scenario.** These are conditional integer-resolution basket calculations using hourly quote summaries. Historical executable depth, fee applicability and fills are not established.
- **No positive cost-adjusted candidate in the live pilot.** The brief REST sample is too limited to establish market-wide efficiency or a profitable executable strategy.
- **Validation rejected the calibration candidate.** The development estimate was T = 1.034401; the selected method remained the unchanged baseline at T = 1. Later baseline log loss was 0.718589 nats and Brier score 0.408273.
- **Execution changes the problem.** In the synthetic six-leg model, a complete basket can have a positive conditional payoff while incomplete fills generate losses.
- **Settlement rules matter.** Integer-labelled ranges do not by themselves certify an exhaustive partition of all admissible resolutions. Full source precision and exceptional settlement require explicit treatment.

The evaluation is retrospective and chronologically held out. No orders are submitted, and no reported value is a realised trading return. The probability model calibrates market-derived probabilities; it is not an external weather forecast.

## Interactive graphs

| Explorer | Evidence and interaction |
| --- | --- |
| [The Liquidity Behind the Quote](explorers/liquidity/index.html) | Recorded depth across time, contract selection and quantity-dependent acquisition cost |
| [Calibrating the Market’s Odds](explorers/probability/index.html) | Historical probability vectors, a temperature slider and the subsequently observed outcome |
| [When a Basket Fails to Fill](explorers/execution/index.html) | Synthetic loss probability and expected payoff across basket discounts and fill assumptions |

Each page includes a linked 2D view, static scientific preview, reset control and CSV export. Plotly is bundled with its licence. The site works offline after extracting the package; it needs no API key, analytics service or chart subscription.

## Reproduce the software and synthetic experiments

Use Python 3.12 or later in a virtual environment:

```bash
python -m venv .venv
# Activate the environment using the command for your operating system.
python -m pip install -r requirements.txt
python scripts/reproduce_public.py
```

This checks the analytical implementation hashes, runs the 45 existing engine tests, checks the website package and reruns the known-truth simulations. It makes no API requests. Fresh simulation outputs go to `outputs/public-reproduction/`; the recorded study remains separate.

With Node.js 22 or later installed, also run:

```bash
node scripts/verify_explorers.cjs
```

This checks the JavaScript explorer calculations and control transitions using a document/plot stub. It is a logic check, not a real-browser rendering test.

## View or rebuild the site

Open `index.html` locally, or serve the project with `python -m http.server 8000` and open `http://localhost:8000`.

```bash
python scripts/build_site.py
python scripts/verify_release.py
```

The build uses retained assets and templates, without network access or model refitting. Both the overview and graph gallery have distinct Open Graph and Twitter preview images, absolute canonical URLs and thumbnail metadata. `docs/github-publishing.md` records the deployment steps and website URLs.

## Empirical reproduction and recorded notebooks

The eight notebooks retain their actual outputs from the completed study. The selected book observations and probability vectors power the interactive explorers. The full API response cache and complete processed historical panel are retained privately and are not included in this public repository. An exact empirical rerun therefore requires the separately retained source snapshot; the offline software and synthetic experiments can be reproduced from this repository alone.

The empirical collectors and analysis scripts are retained for transparency. An exact rerun requires the original input snapshot and its permissions; a new download is a new sample, not a substitute for the frozen study. See [data/README.md](data/README.md).

## Repository map

- `kalshi_engine/`: public GET client, book reconstruction, fees, payoff constraints and probability functions.
- `notebooks/`: eight recorded research notebooks and their index page.
- `scripts/`: original analysis, public reproduction, site build and release checks.
- `paper/final/`: final PDF, editable XeLaTeX sources, vector figures and compiler.
- `protocol/`: research design, audit amendment, model freeze and milestone record.
- `outputs/`: selected recorded summaries, synthetic results and verification records.
- `assets/`, `explorers/`, `vendor/`: website, graph payload, local plotting library and thumbnails.
- `references/`: Harvard bibliography and separate source notes.
- `docs/`: research reflections, publication scope and deployment instructions.

## Research context

As Hasbrouck (2007) explains in *Empirical market microstructure*, the process generating observed quotes matters for economic interpretation. As Gneiting and Raftery (2007) explain in *Strictly proper scoring rules, prediction, and estimation*, forecast quality can be assessed with proper scores. This project connects those ideas to explicit payoff and execution assumptions.

The final paper contains the full narrative and [Harvard reference list](references/harvard-references.txt). Original software and prose have no public licence assigned. Third-party licences are retained in `vendor/`. The project is independent and does not claim endorsement by Kalshi.
