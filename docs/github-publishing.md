# GitHub Pages publication

The public repository is `https://github.com/joelcerraga/Kalshi-Mispricing-Arbitrage`. Its history starts with the approved public tree. The full research snapshot is retained in the separate private repository `Kalshi-Mispricing-Arbitrage-Private`.

## Website destinations

- Overview: `https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/`
- Graph gallery: `https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/explorers/`
- Liquidity: `https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/explorers/liquidity/`
- Calibration: `https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/explorers/probability/`
- Execution: `https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/explorers/execution/`
- Notebooks: `https://joelcerraga.github.io/Kalshi-Mispricing-Arbitrage/notebooks/`

## Build and deploy

1. Run `python scripts/build_site.py` after editing the retained templates.
2. Run `python scripts/reproduce_public.py` and `node scripts/verify_explorers.cjs`.
3. Commit the approved tree on `main`.
4. In Settings → Pages, use **Deploy from a branch**, **main**, **/(root)**. The `.nojekyll` file supports the buildless site.
5. Check the Pages deployment, then the landing page, three graph loads, controls and paper link.

The research workflow runs analytical, synthetic and site checks. It does not obtain new market data. Keep private source inputs and correspondence out of this repository, including its history.

## Thumbnail assets

| Page | File | Dimensions |
| --- | --- | --- |
| Landing / repository social preview | `assets/thumbnails/pricing-uncertainty.jpg` | 1774 × 887 |
| Graph gallery and explorers | `assets/thumbnails/probability-in-motion.jpg` | 1774 × 887 |

Both page families have their own Open Graph and Twitter preview metadata. The covers are conceptual artwork rather than research figures; prompts and generation details are retained in `assets/thumbnails/prompts.json`.

The current deployment and verification record is in `docs/release-status.json`.
