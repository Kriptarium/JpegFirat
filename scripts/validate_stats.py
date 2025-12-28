import argparse
import pandas as pd
import numpy as np
from scipy import stats

def ci95(mean, std, n):
    # 95% CI half-width using normal approximation
    return 1.96 * (std / np.sqrt(n))

def holm_adjust(pvals):
    # Holm-Bonferroni step-down adjustment
    m = len(pvals)
    order = np.argsort(pvals)
    adjusted = np.empty(m, dtype=float)
    for k, idx in enumerate(order):
        adjusted[idx] = min((m - k) * pvals[idx], 1.0)
    # enforce monotonicity
    # step-down means adjusted p-values should be non-decreasing in sorted order
    sorted_adj = adjusted[order]
    for i in range(1, m):
        if sorted_adj[i] < sorted_adj[i-1]:
            sorted_adj[i] = sorted_adj[i-1]
    adjusted[order] = sorted_adj
    return adjusted

def wilcoxon_holm(per_image_df, metric, methods, baseline=None):
    # Pairwise Wilcoxon signed-rank tests with Holm correction.
    # If baseline is given: compare each method vs baseline only.
    results = []
    if baseline is None:
        pairs=[]
        for i in range(len(methods)):
            for j in range(i+1, len(methods)):
                pairs.append((methods[i], methods[j]))
    else:
        pairs=[(m, baseline) for m in methods if m!=baseline]

    pvals=[]
    for a,b in pairs:
        xa = per_image_df[a].values
        xb = per_image_df[b].values
        # two-sided Wilcoxon; zero_method='wilcox' ignores zeros
        stat, p = stats.wilcoxon(xa, xb, alternative='two-sided', zero_method='wilcox')
        pvals.append(p)
        results.append((a,b,stat,p))
    pvals = np.array(pvals, dtype=float)
    p_holm = holm_adjust(pvals)
    out=[]
    for (a,b,stat,p), ph in zip(results, p_holm):
        out.append({"A":a, "B":b, "W":stat, "p":p, "p_holm":ph})
    return pd.DataFrame(out).sort_values(["p_holm","p"], ascending=True)

def compute_summary(allobs):
    n = len(allobs)
    grp = allobs.groupby("method").agg(
        n=("psnr","size"),
        psnr_mean=("psnr","mean"),
        psnr_std=("psnr","std"),
        ssim_mean=("ssim","mean"),
        ssim_std=("ssim","std"),
        cr_mean=("cr","mean"),
        cr_std=("cr","std"),
    ).reset_index()
    grp["psnr_ci95"] = ci95(grp["psnr_mean"], grp["psnr_std"], grp["n"])
    grp["ssim_ci95"] = ci95(grp["ssim_mean"], grp["ssim_std"], grp["n"])
    grp["cr_ci95"]   = ci95(grp["cr_mean"], grp["cr_std"], grp["n"])

    grp["PSNR (mean±std, 95%CI)"] = grp.apply(lambda r: f"{r.psnr_mean:.3f} ± {r.psnr_std:.3f} (±{r.psnr_ci95:.3f})", axis=1)
    grp["SSIM (mean±std, 95%CI)"] = grp.apply(lambda r: f"{r.ssim_mean:.5f} ± {r.ssim_std:.5f} (±{r.ssim_ci95:.5f})", axis=1)
    grp["CR (mean±std, 95%CI)"]   = grp.apply(lambda r: f"{r.cr_mean:.3f} ± {r.cr_std:.3f} (±{r.cr_ci95:.3f})", axis=1)
    return grp

def per_image_means(allobs):
    piv = allobs.pivot_table(index="image", columns="method", values=["psnr","ssim","cr"], aggfunc="mean")
    # Flatten multiindex columns: metric_method
    piv.columns = [f"{m}_{meth}" for m,meth in piv.columns]
    piv = piv.reset_index()
    return piv

def friedman_test(allobs, metric, methods):
    # dataset-level: per-image mean over runs, then Friedman across methods
    piv = allobs.pivot_table(index="image", columns="method", values=metric, aggfunc="mean")[methods]
    stat, p = stats.friedmanchisquare(*[piv[m].values for m in methods])
    return stat, p, piv

def validate(xlsx):
    sheets = pd.read_excel(xlsx, sheet_name=None)
    allobs = sheets[[k for k in sheets.keys() if k.lower().endswith("allobs")][0]].copy()
    # normalize column names
    allobs.columns = [c.strip().lower() for c in allobs.columns]
    allobs = allobs.rename(columns={"jpeg_bytes":"jpeg_bytes","raw_bytes":"raw_bytes"})
    # ensure required columns exist
    required={"run","method","image","psnr","ssim","cr"}
    if not required.issubset(set(allobs.columns)):
        raise ValueError(f"AllObs sheet missing columns: {required - set(allobs.columns)}")

    methods = list(pd.unique(allobs["method"]))
    methods.sort()
    # If a 'Standard' method exists, put it first for readability
    if "Standard" in methods:
        methods = ["Standard"] + [m for m in methods if m!="Standard"]

    summary = compute_summary(allobs)
    # Compare with stored summary (if present)
    # Find the summary sheet
    summary_sheet_name = [k for k in sheets.keys() if "summary" in k.lower()][0]
    stored = sheets[summary_sheet_name].copy()
    stored.columns = [c.strip() for c in stored.columns]
    # soft compare on numeric columns
    numeric_cols = ["psnr_mean","psnr_std","ssim_mean","ssim_std","cr_mean","cr_std","psnr_ci95","ssim_ci95","cr_ci95"]
    # Align methods
    merged = pd.merge(summary, stored, on="method", suffixes=("_new","_old"))
    for col in numeric_cols:
        a = merged[f"{col}_new"].astype(float).values
        b = merged[f"{col}_old"].astype(float).values
        if not np.allclose(a,b, rtol=1e-6, atol=1e-6):
            raise AssertionError(f"Mismatch in {col}: max abs diff={np.max(np.abs(a-b))}")
    # Friedman + posthoc validation (recompute; stored values may differ by ordering)
    out_fried=[]
    for metric in ["psnr","ssim","cr"]:
        stat, p, _ = friedman_test(allobs, metric, methods=[m for m in methods if m in allobs["method"].unique()])
        out_fried.append({"metric":metric.upper() if metric!="cr" else "CR",
                          "friedman_stat":stat, "friedman_p":p,
                          "images_n": allobs["image"].nunique(),
                          "methods_n": allobs["method"].nunique()})
    fried_df = pd.DataFrame(out_fried)
    # done
    return True, summary, fried_df

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", required=True)
    args = ap.parse_args()
    ok, summary, fried = validate(args.xlsx)
    print("OK: summary statistics in the xlsx are reproducible from AllObs.")
    print("\nFriedman recomputation (from AllObs):")
    print(fried.to_string(index=False))
