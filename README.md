# JpegFirat — Reproducible Statistical Validation of Chaos-Based JPEG Quantization

This repository provides reproducibility artifacts for an extended study on
chaos-based JPEG quantization, with a focus on **large-scale statistical validation**
and **cross-domain generalization**.

The repository is designed to enable independent verification of:
- run-level summary statistics (mean ± std, 95% confidence intervals),
- non-parametric significance testing (Friedman + Wilcoxon with Holm correction),
- the complete set of generated **8×8 quantization tables** (CSV),
- JPEG encoder settings used in evaluation.

---

## Repository Structure

- `paper_artifacts/`
  - Excel artifacts containing run protocol (seed/x0), hashes, and results summaries.

- `quantization_tables/`
  - Generated 8×8 quantization tables (CSV), organized by dataset/map/run.

- `config/`
  - JPEG encoder configuration used for metric computation.

- `scripts/`
  - Validation and plotting scripts (if provided/added).

- `figures/`
  - Generated plots used in the manuscript (optional).

---

## Key Files

- `paper_artifacts/Pneumonia_30run_results_repro_protocol_added.xlsx`
  - Includes run seeds / initial conditions (x0), table hashes, and reproducibility notes.

- `config/jpeg_encoder_config_pneumonia.json`
  - Documents JPEG encoder parameters (quality, subsampling, optimization, limits).

- `quantization_tables/README.md`
  - Explains how quantization tables are organized and reused.

---

## Reproducibility Note

Chaotic dynamics are **not embedded inside the JPEG compression pipeline**.
Chaos is used only to generate quantization tables **prior to compression**.
All remaining JPEG stages follow the standard codec without modification.

---

## Citation

If you use these artifacts, please cite the associated manuscript.
