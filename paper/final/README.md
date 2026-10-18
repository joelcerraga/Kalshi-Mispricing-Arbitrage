# Final paper

**Mispricing and Arbitrage in Prediction Markets**  
Joel Cerraga · October 2026

`Kalshi-Mispricing-and-Arbitrage-Final-Paper.pdf` is the completed 39-page A4 portrait paper. It contains the title page, abstract, contents, lists of figures, tables, equations and code listings, abbreviations, mathematical symbols, research findings, discussion, Harvard references and implementation appendices.

## Recompile the retained source

The source is self-contained for typesetting. Install XeLaTeX with the packages in `main.tex`, plus Nimbus Sans, Latin Modern Math and DejaVu Sans Mono fonts. From the project root run:

```bash
python paper/final/compile_paper.py
```

The compiler runs four passes in a temporary directory, checks the log for unresolved references and layout warnings, and writes the final PDF and LaTeX registers here. It does not download data or refit the model. The PDF byte hash may change between builds because of PDF creation metadata.

## Rebuild the exhibits and verify the paper

The full project package retains the frozen research inputs needed by the exhibit builder. Install the project Python dependencies, then run:

```bash
python paper/final/build_paper.py
python paper/final/compile_paper.py
python paper/final/verify_paper.py
```

The builder creates the tables, equations, vector figures and exact implementation extracts from retained inputs. The verifier checks A4 page geometry, sequential exhibit numbers, register page targets, citation coverage, caption alignment, key reported values and six frozen-file hashes. The delivered `verification-report.json` also records the completed visual page review. Use the verifier's `--visual-reviewed` flag only after visually reviewing the newly rendered document.

`paper-registers.json` describes the exhibits and frozen inputs; `references.json` contains the Harvard reference records. The generated TeX and vector figures are retained for direct editing. Any subsequent edits to generated exhibits should also be incorporated into `build_paper.py` to remain reproducible.

The package is private research material. Publication scope and source-data rights are documented in the project root; compilation does not authorise public redistribution of cached source records.
