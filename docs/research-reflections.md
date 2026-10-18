# What changed during the research

## The batch route did not accept the initial collection plan

An attempted batch size exceeded the API route's supported limit. The collector was changed to smaller batches and the remaining history was obtained through the archived market route. Recorded responses and explicit coverage counts preserve what was actually acquired.

## Historical and current schemas differed

The adapter was adjusted to recognise archived candle responses. Missing completed-hour observations remained exclusions; stale or later candles were not substituted. Two Chicago noon panels were excluded.

## An intact snapshot was missing from the index

One stored raw response was recovered into the provenance index after its contents were verified. This repaired the observed omission. It does not establish that the collector's separate file and manifest writes are transactionally atomic.

## Integer-labelled ranges were an insufficient settlement model

The initial integer partition is useful for a conditional basket identity. Full-precision probes can include states outside that partition, while the rules allow exceptional resolution. The analysis therefore distinguishes conditional arithmetic from an unconditional arbitrage certificate. Conservative probes are not evidence that an actual gap settlement occurred.

## Calibration failed validation

The fitted temperature slightly improved development fit but worsened validation log loss. The unchanged baseline won the selection rule. Later comparisons of the rejected model remain supplementary and do not revise the frozen decision.

## Apparent opportunities disappeared after costs

Positive historical gross gaps did not remain positive under the stated current-fee scenario. The live pilot likewise provided no positive cost-adjusted candidate. Historical candles lack executable depth and the observations do not establish fills.

## Execution risk needed a separate mechanism

Synthetic experiments separate a complete-basket payoff from the risk of missing the winning leg. Independent fills are an explicit scenario assumption, not an estimate recovered from the short REST sample.

## Presentation defects were corrected

One-sided books originally produced an infinite spread in the explorer display. Missing spreads now appear as unavailable. Plotly axis-title handling was aligned with the bundled version. The release preparation also repaired an incomplete standalone vector-figure source; the already compiled final paper and research estimates remain unchanged.

## Publication is a separate decision

Publicly readable API routes do not grant general redistribution rights. The prepared presentation, paper and selected explorer payload remain subject to the publication scope recorded in `DATA_AND_SOFTWARE_RIGHTS.md`.

## Browser graphics support

The deployed-site review found that a browser without WebGL displayed Plotly's unsupported-graphics panel while the 2D chart and calculations still worked. The loader now checks graphics support and substitutes a clearly labelled static reference in the 3D panel when necessary. Controls, the linked 2D chart and CSV export remain interactive. The static reference is explicitly identified as independent of the selected controls, avoiding an incorrect impression that it represents the current scenario. Interactive 3D remains available in browsers with WebGL support.
