# Chaos-based JPEG quantization — reproducibility pack

This repository contains:
- The exact result spreadsheets used in the manuscript:
  - `Pneumonia_30run_results.xlsx`
  - `DC_extension_results.xlsx`
- Scripts that **recompute** all summary statistics, 95% confidence intervals,
  and non-parametric significance tests (Friedman + Wilcoxon with Holm correction)
  **directly from the run-level observations stored in the spreadsheets**.

## Quick start

```bash
pip install -r requirements.txt
python scripts/validate_stats.py --xlsx Pneumonia_30run_results.xlsx
python scripts/plot_results.py --xlsx Pneumonia_30run_results.xlsx --out figures
```

## What is validated?

From the `Pneumonia_AllObs` sheet, the scripts reproduce:
- `Pneumonia_Summary_30run` (mean, std, 95% CI, formatted strings)
- `PerImage_Means`
- `Friedman`
- `Posthoc_PSNR`, `Posthoc_SSIM`, `Posthoc_CR` (Wilcoxon + Holm)

The validator checks that the newly computed tables match the ones in the xlsx (within numerical tolerances).

## Notes

This pack focuses on statistical reproducibility. A full end-to-end re-run from images
requires the exact JPEG encoder settings and the exact quantization tables used per run.
If you also publish those quantization tables (recommended), the end-to-end experiment
becomes fully reproducible.
