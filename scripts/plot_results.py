import argparse, os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def ensure_dir(p): os.makedirs(p, exist_ok=True)

def boxplot_metric(allobs, metric, outpath):
    methods = list(pd.unique(allobs["method"]))
    # keep Standard first if present
    methods = (["Standard"] + [m for m in methods if m!="Standard"]) if "Standard" in methods else sorted(methods)
    data = [allobs.loc[allobs["method"]==m, metric].values for m in methods]
    plt.figure(figsize=(10,5))
    plt.boxplot(data, labels=methods, showfliers=False)
    plt.xticks(rotation=30, ha="right")
    plt.ylabel(metric.upper())
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()

def ci_bar(summary, metric_mean, metric_ci, outpath, ylabel):
    df = summary.copy().sort_values(metric_mean, ascending=False)
    x = np.arange(len(df))
    plt.figure(figsize=(10,5))
    plt.errorbar(x, df[metric_mean].values, yerr=df[metric_ci].values, fmt='o')
    plt.xticks(x, df["method"].values, rotation=30, ha="right")
    plt.ylabel(ylabel)
    plt.tight_layout()
    plt.savefig(outpath, dpi=300)
    plt.close()

if __name__ == "__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--out", default="figures")
    args=ap.parse_args()

    sheets=pd.read_excel(args.xlsx, sheet_name=None)
    allobs = sheets[[k for k in sheets.keys() if k.lower().endswith("allobs")][0]].copy()
    allobs.columns=[c.strip().lower() for c in allobs.columns]

    summary_sheet=[k for k in sheets.keys() if "summary" in k.lower()][0]
    summary=sheets[summary_sheet].copy()

    ensure_dir(args.out)
    boxplot_metric(allobs, "psnr", os.path.join(args.out,"boxplot_psnr.png"))
    boxplot_metric(allobs, "ssim", os.path.join(args.out,"boxplot_ssim.png"))
    boxplot_metric(allobs, "cr",   os.path.join(args.out,"boxplot_cr.png"))

    # CI plots
    ci_bar(summary, "psnr_mean", "psnr_ci95", os.path.join(args.out,"ci_psnr.png"), "PSNR (mean ± 95% CI)")
    ci_bar(summary, "ssim_mean", "ssim_ci95", os.path.join(args.out,"ci_ssim.png"), "SSIM (mean ± 95% CI)")
    ci_bar(summary, "cr_mean",   "cr_ci95",   os.path.join(args.out,"ci_cr.png"),   "CR (mean ± 95% CI)")
    print(f"Saved figures to: {args.out}")
