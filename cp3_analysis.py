"""
cp3_analysis.py
Checkpoint 3 — Statistical analysis: correlations and regression with
pre/post-2020 interaction terms.

Input:  data/cp3_panel.csv
Outputs:
  plots/cp3_correlation_matrix.png
  plots/cp3_income_vs_crime.png
  plots/cp3_poverty_vs_crime.png
  plots/cp3_hardship_vs_crime.png
  data/cp3_correlation_table.csv
  data/cp3_regression_results.txt
"""

import os
import math
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import StandardScaler

os.makedirs("plots", exist_ok=True)
os.makedirs("data",  exist_ok=True)

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 150

# ── Load ──────────────────────────────────────────────────────────────────────
print("=== CP3 Statistical Analysis ===\n")
panel = pd.read_csv("data/cp3_panel.csv")
print(f"Panel: {len(panel)} rows, {panel['district'].nunique()} districts\n")

SOCECO_VARS = [c for c in ["per_capita_income", "pct_poverty", "pct_unemployed",
                            "pct_no_hs", "hardship_index"] if c in panel.columns]
print(f"Socioeconomic variables available: {SOCECO_VARS}")

pre  = panel[panel["post2020"] == 0]
post = panel[panel["post2020"] == 1]

# ── 1. Correlation table ──────────────────────────────────────────────────────
print("\n── Correlation Analysis ─────────────────────────────────────────────")

corr_rows = []
for var in SOCECO_VARS:
    pre_r  = pre[var].corr(pre["violent_crime_count"])
    post_r = post[var].corr(post["violent_crime_count"])
    all_r  = panel[var].corr(panel["violent_crime_count"])
    corr_rows.append({
        "variable":       var,
        "corr_pre2020":   round(pre_r, 3),
        "corr_post2020":  round(post_r, 3),
        "corr_all":       round(all_r, 3),
        "delta":          round(post_r - pre_r, 3),
    })
    print(f"  {var:40s}  pre={pre_r:+.3f}  post={post_r:+.3f}  delta={post_r - pre_r:+.3f}")

corr_df = pd.DataFrame(corr_rows)
corr_df.to_csv("data/cp3_correlation_table.csv", index=False)
print("  ✓ Saved data/cp3_correlation_table.csv")

# ── 2. Correlation heatmap ────────────────────────────────────────────────────
corr_cols = SOCECO_VARS + ["violent_crime_count"]
corr_matrix = panel[corr_cols].corr().round(2)

fig, ax = plt.subplots(figsize=(8, 6))
sns.heatmap(corr_matrix, ax=ax, annot=True, cmap="RdBu_r", center=0,
            linewidths=0.4, fmt=".2f", annot_kws={"size": 9})
ax.set_title("Correlation Matrix — Socioeconomic Variables vs Violent Crime", fontsize=12)
fig.savefig("plots/cp3_correlation_matrix.png", bbox_inches="tight")
plt.close(fig)
print("  ✓ Saved plots/cp3_correlation_matrix.png")

# ── 3. Scatter plots: key variables vs crime, pre vs post ────────────────────
def scatter_pre_post(xvar, xlabel, filename):
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), sharey=True)
    for ax, df, label, color in zip(axes, [pre, post],
                                    ["Pre-2020 (2015–2019)", "Post-2020 (2020–2024)"],
                                    ["#2980b9", "#e74c3c"]):
        # Aggregate to district level for scatter (mean across years)
        agg = df.groupby("district").agg(
            x=(xvar, "mean"), y=("violent_crime_count", "mean")
        ).reset_index()
        ax.scatter(agg["x"], agg["y"], color=color, alpha=0.8, edgecolors="white", s=60)
        # Trend line
        m, b = np.polyfit(agg["x"], agg["y"], 1)
        xs = np.linspace(agg["x"].min(), agg["x"].max(), 100)
        ax.plot(xs, m * xs + b, color=color, linewidth=1.8, linestyle="--")
        r = agg["x"].corr(agg["y"])
        ax.set_title(f"{label}\nr = {r:.3f}", fontsize=11)
        ax.set_xlabel(xlabel)
        ax.set_ylabel("Avg Violent Crimes / Year")
        for _, row in agg.iterrows():
            ax.annotate(str(int(row["district"])), (row["x"], row["y"]),
                        fontsize=7, alpha=0.6, ha="center", va="bottom")
    fig.suptitle(f"{xlabel} vs Violent Crime by District", fontsize=13)
    fig.tight_layout()
    fig.savefig(f"plots/{filename}", bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ Saved plots/{filename}")

if "per_capita_income" in panel.columns:
    scatter_pre_post("per_capita_income", "Per Capita Income ($)", "cp3_income_vs_crime.png")
if "pct_poverty" in panel.columns:
    scatter_pre_post("pct_poverty", "% Households Below Poverty", "cp3_poverty_vs_crime.png")
if "hardship_index" in panel.columns:
    scatter_pre_post("hardship_index", "Hardship Index", "cp3_hardship_vs_crime.png")

# ── 4. OLS Regression with interaction terms ──────────────────────────────────
print("\n── Regression Analysis ──────────────────────────────────────────────")

results_lines = []

def ols(X, y, feature_names):
    """Simple OLS using numpy for no-dependency regression reporting."""
    X_ = np.column_stack([np.ones(len(X)), X])
    try:
        coefs = np.linalg.lstsq(X_, y, rcond=None)[0]
    except np.linalg.LinAlgError:
        return None, None, None, None
    y_hat = X_ @ coefs
    ss_res = np.sum((y - y_hat) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0
    names = ["intercept"] + feature_names
    return coefs, r2, names, y_hat

def report(title, coefs, r2, names):
    lines = [f"\n{title}", "-" * 60]
    for name, coef in zip(names, coefs):
        lines.append(f"  {name:45s}  {coef:+.4f}")
    lines.append(f"  {'R-squared':45s}  {r2:.4f}")
    lines.append(f"  {'N':45s}  {len(panel)}")
    for l in lines:
        print(l)
    results_lines.extend(lines)

# Model 1: Crime ~ socioeconomic variables (all years)
if SOCECO_VARS:
    df_m = panel.dropna(subset=SOCECO_VARS + ["violent_crime_count"])
    X1 = df_m[SOCECO_VARS].values
    y1 = df_m["violent_crime_count"].values
    c1, r1, n1, _ = ols(X1, y1, SOCECO_VARS)
    if c1 is not None:
        report("Model 1: Crime ~ Socioeconomic Variables (all years)", c1, r1, n1)

# Model 2: Crime ~ socioeconomic + post2020 dummy
if SOCECO_VARS:
    feat2 = SOCECO_VARS + ["post2020"]
    df_m2 = panel.dropna(subset=feat2 + ["violent_crime_count"])
    X2 = df_m2[feat2].values
    y2 = df_m2["violent_crime_count"].values
    c2, r2_, n2, _ = ols(X2, y2, feat2)
    if c2 is not None:
        report("Model 2: Crime ~ Socioeconomic + post2020 dummy", c2, r2_, n2)

# Model 3: Interaction model — key variable × post2020
# Use hardship_index if available, else per_capita_income
key_var = "hardship_index" if "hardship_index" in panel.columns else (
          "per_capita_income" if "per_capita_income" in panel.columns else None)

if key_var:
    df_m3 = panel.dropna(subset=[key_var, "post2020", "violent_crime_count"])
    df_m3 = df_m3.copy()
    df_m3["interaction"] = df_m3[key_var] * df_m3["post2020"]
    feat3 = [key_var, "post2020", "interaction"]
    X3 = df_m3[feat3].values
    y3 = df_m3["violent_crime_count"].values
    c3, r3, n3, _ = ols(X3, y3, feat3)
    if c3 is not None:
        report(f"Model 3: Interaction — {key_var} × post2020 (structural break test)", c3, r3, n3)
        results_lines.append(
            f"\n  Interpretation: The interaction term coefficient tests whether the "
            f"relationship between {key_var} and violent crime changed after 2020. "
            f"A nonzero interaction suggests structural change."
        )

# ── Save regression output ────────────────────────────────────────────────────
with open("data/cp3_regression_results.txt", "w") as f:
    f.write("\n".join(results_lines))
print("\n  ✓ Saved data/cp3_regression_results.txt")
print("\nDone. All outputs in data/ and plots/")
