# Meridian Trust Bank — retention starter kit

```
pip install pandas numpy scipy scikit-learn statsmodels matplotlib tabulate
cd src
python build_powerbi.py "../data/Bank Data.csv" ../out   # 50k dataset + Power BI tables + fidelity report
python charts.py "../data/Bank Data.csv" ../out/figures   # 9 EDA charts (real data only)
```

| Path | What it is |
|---|---|
| `CLAUDE.md` | Team plan (3 parallel tracks, 2 hours) |
| `src/shared_loader.py` | The one loader every track uses (handles all raw-file quirks + checksum) |
| `src/synth.py` | 10k → 50k scaling: stratified Gaussian copula |
| `src/build_powerbi.py` | Builds the star schema and fidelity report |
| `src/charts.py` | The 9 evidence-selected charts |
| `out/analysis_50k.csv` | 10,000 real + 40,000 synthetic rows (`is_synthetic`, `data_split`) |
| `out/synthetic_fidelity.md` | Proof the synthetic rows match the real ones |
| `out/expected_values.json` | Numbers the Power BI dashboard must reproduce |
| `out/figures/` | Charts (deck + reference images for Power BI) |
| `out/powerbi/` | `data/` CSVs, `measures.dax`, `BUILD_GUIDE.md` |

Put `Bank Data.csv` in `data/` before running. Re-running gives identical output (seed 42).
