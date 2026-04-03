"""
cp4_analysis.py
Checkpoint 4 — Robustness and statistical validation of CP3 findings.
Extends prior analysis by incorporating population-normalized crime rates,
confidence intervals, statistical significance (p-values), and outlier testing
(e.g., excluding District 12). Also includes enhanced visualizations with
pre/post-2020 comparisons and optional fixed-effects modeling.

Input:
  data/cp3_panel.csv
  (optional) data/cp4_district_population.csv

Outputs:
  plots/cp4_time_trend_counts.png
  plots/cp4_hardship_vs_crime_ci.png
  plots/cp4_income_vs_crime_ci.png
  plots/cp4_pre_post_hardship.png
  plots/cp4_pre_post_income.png
  plots/cp4_coef_plot_counts.png

  (if population provided)
  plots/cp4_time_trend_rate.png
  plots/cp4_hardship_vs_rate_ci.png
  plots/cp4_income_vs_rate_ci.png
  plots/cp4_pre_post_hardship_rate.png
  plots/cp4_pre_post_income_rate.png
  plots/cp4_coef_plot_rate.png

  data/cp4_panel_normalized.csv
  data/cp4_correlation_table.csv
  data/cp4_regression_detailed.csv
  data/cp4_robustness_summary.csv
  data/cp4_analysis_notes.txt

  data/cp4_violent_crime_count_full_sample_results.txt
  data/cp4_violent_crime_count_exclude_district12_results.txt
  (and normalized equivalents if applicable)
"""

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
import statsmodels.formula.api as smf


# =========================
# Config
# =========================
DATA_DIR = Path("data")
PLOTS_DIR = Path("plots")

CP3_PANEL_PATH = DATA_DIR / "cp3_panel.csv"
POP_PATH = DATA_DIR / "cp4_district_population.csv"

CP4_PANEL_PATH = DATA_DIR / "cp4_panel_normalized.csv"
CP4_CORR_PATH = DATA_DIR / "cp4_correlation_table.csv"
CP4_REG_DETAILED_PATH = DATA_DIR / "cp4_regression_detailed.csv"
CP4_ROBUSTNESS_PATH = DATA_DIR / "cp4_robustness_summary.csv"
CP4_NOTES_PATH = DATA_DIR / "cp4_analysis_notes.txt"

sns.set_theme(style="whitegrid")


# =========================
# Helpers
# =========================
def ensure_dirs() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    PLOTS_DIR.mkdir(exist_ok=True)


def significance_stars(p: float) -> str:
    if pd.isna(p):
        return ""
    if p < 0.001:
        return "***"
    if p < 0.01:
        return "**"
    if p < 0.05:
        return "*"
    if p < 0.10:
        return "."
    return ""


def load_panel() -> pd.DataFrame:
    if not CP3_PANEL_PATH.exists():
        raise FileNotFoundError(f"Missing required file: {CP3_PANEL_PATH}")

    df = pd.read_csv(CP3_PANEL_PATH)

    required_cols = {
        "year",
        "district",
        "violent_crime_count",
        "per_capita_income",
        "pct_poverty",
        "pct_unemployed",
        "pct_no_hs",
        "hardship_index",
        "post2020",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"{CP3_PANEL_PATH} is missing columns: {sorted(missing)}")

    numeric_cols = [
        "year",
        "district",
        "violent_crime_count",
        "per_capita_income",
        "pct_poverty",
        "pct_unemployed",
        "pct_no_hs",
        "hardship_index",
        "post2020",
    ]
    if "pct_crowded" in df.columns:
        numeric_cols.append("pct_crowded")
    if "log_crime" in df.columns:
        numeric_cols.append("log_crime")

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna().copy()
    df["district"] = df["district"].astype(int)
    df["year"] = df["year"].astype(int)
    df["post2020"] = df["post2020"].astype(int)
    return df


def merge_population(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """
    Optional input:
      data/cp4_district_population.csv
    Required columns:
      district,population

    If present, adds:
      population
      violent_crime_rate_per_100k
      log_crime_rate
    """
    if "population" in df.columns:
        out = df.copy()
        out["population"] = pd.to_numeric(out["population"], errors="coerce")
    elif POP_PATH.exists():
        pop = pd.read_csv(POP_PATH)
        required = {"district", "population"}
        missing = required - set(pop.columns)
        if missing:
            raise ValueError(f"{POP_PATH} is missing columns: {sorted(missing)}")
        pop["district"] = pd.to_numeric(pop["district"], errors="coerce")
        pop["population"] = pd.to_numeric(pop["population"], errors="coerce")
        out = df.merge(pop[["district", "population"]], on="district", how="left")
    else:
        return df.copy(), False

    if out["population"].isna().any():
        # If some populations are missing, keep the panel but don't claim full normalization coverage.
        pass

    out["violent_crime_rate_per_100k"] = (
        out["violent_crime_count"] / out["population"] * 100000
    )
    out["log_crime_rate"] = np.log1p(out["violent_crime_rate_per_100k"])
    return out, True


def compute_period_correlations(df: pd.DataFrame, y_col: str) -> pd.DataFrame:
    predictors = [
        "per_capita_income",
        "pct_poverty",
        "pct_unemployed",
        "pct_no_hs",
        "hardship_index",
    ]
    if "pct_crowded" in df.columns:
        predictors.append("pct_crowded")

    pre = df[df["post2020"] == 0]
    post = df[df["post2020"] == 1]

    rows = []
    for var in predictors:
        pre_r = pre[var].corr(pre[y_col])
        post_r = post[var].corr(post[y_col])
        all_r = df[var].corr(df[y_col])

        delta = np.nan
        if pd.notna(pre_r) and pd.notna(post_r):
            delta = post_r - pre_r

        if pd.isna(delta):
            direction = ""
        elif delta > 0:
            direction = "↑"
        elif delta < 0:
            direction = "↓"
        else:
            direction = "→"

        rows.append(
            {
                "variable": var,
                "pre2020_r": pre_r,
                "post2020_r": post_r,
                "all_years_r": all_r,
                "delta_post_minus_pre": delta,
                "direction": direction,
                "outcome": y_col,
            }
        )

    return pd.DataFrame(rows)


def fit_ols_matrix(df: pd.DataFrame, y_col: str, x_cols: list[str]):
    X = sm.add_constant(df[x_cols], has_constant="add")
    y = df[y_col]
    return sm.OLS(y, X).fit()


def tidy_model(model, model_name: str, sample_name: str, outcome_name: str) -> pd.DataFrame:
    conf = model.conf_int()
    out = pd.DataFrame(
        {
            "term": model.params.index,
            "coef": model.params.values,
            "std_err": model.bse.values,
            "t_value": model.tvalues.values,
            "p_value": model.pvalues.values,
            "ci_lower": conf[0].values,
            "ci_upper": conf[1].values,
        }
    )
    out["sig"] = out["p_value"].apply(significance_stars)
    out["model"] = model_name
    out["sample"] = sample_name
    out["outcome"] = outcome_name
    out["r_squared"] = model.rsquared
    out["adj_r_squared"] = model.rsquared_adj
    out["n_obs"] = int(model.nobs)
    return out


def run_models(df: pd.DataFrame, y_col: str, sample_name: str) -> tuple[list, pd.DataFrame]:
    detailed = []

    socio_vars = [
        "per_capita_income",
        "pct_poverty",
        "pct_unemployed",
        "pct_no_hs",
        "hardship_index",
    ]
    if "pct_crowded" in df.columns:
        socio_vars.append("pct_crowded")

    # Model 1
    m1 = fit_ols_matrix(df, y_col, socio_vars)
    detailed.append(tidy_model(m1, "model1_socioeconomic", sample_name, y_col))

    # Model 2
    m2 = fit_ols_matrix(df, y_col, socio_vars + ["post2020"])
    detailed.append(tidy_model(m2, "model2_plus_post2020", sample_name, y_col))

    # Model 3
    df_inter = df.copy()
    df_inter["hardship_x_post2020"] = df_inter["hardship_index"] * df_inter["post2020"]
    m3 = fit_ols_matrix(df_inter, y_col, ["hardship_index", "post2020", "hardship_x_post2020"])
    detailed.append(tidy_model(m3, "model3_interaction", sample_name, y_col))

    models = [m1, m2, m3]

    # Model 4: optional district fixed effects
    try:
        fe = smf.ols(
            formula=f"{y_col} ~ hardship_index + post2020 + hardship_index:post2020 + C(district)",
            data=df,
        ).fit()
        detailed.append(tidy_model(fe, "model4_district_fixed_effects", sample_name, y_col))
        models.append(fe)
    except Exception:
        pass

    return models, pd.concat(detailed, ignore_index=True)


def save_model_summaries(models: list, path: Path, title: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(title + "\n")
        f.write("=" * len(title) + "\n\n")
        for i, model in enumerate(models, start=1):
            f.write(f"MODEL {i}\n")
            f.write("-" * 60 + "\n")
            f.write(model.summary().as_text())
            f.write("\n\n")


def robustness_summary_from_detailed(detailed_df: pd.DataFrame) -> pd.DataFrame:
    keep_terms = {"hardship_index", "post2020", "hardship_x_post2020"}

    rows = []
    for (sample, outcome, model), grp in detailed_df.groupby(["sample", "outcome", "model"]):
        row = {
            "sample": sample,
            "outcome": outcome,
            "model": model,
            "r_squared": grp["r_squared"].iloc[0],
            "adj_r_squared": grp["adj_r_squared"].iloc[0],
            "n_obs": grp["n_obs"].iloc[0],
        }
        for _, r in grp.iterrows():
            if r["term"] in keep_terms:
                row[f"{r['term']}_coef"] = r["coef"]
                row[f"{r['term']}_p"] = r["p_value"]
                row[f"{r['term']}_sig"] = r["sig"]
        rows.append(row)

    return pd.DataFrame(rows)


def make_time_trend_plot(df: pd.DataFrame, y_col: str, filename: str, title: str, y_label: str) -> None:
    yearly = df.groupby("year")[y_col].mean().reset_index()

    plt.figure(figsize=(9, 5))
    plt.plot(yearly["year"], yearly[y_col], marker="o")
    plt.axvline(2020, linestyle="--")
    plt.title(title)
    plt.xlabel("Year")
    plt.ylabel(y_label)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=300)
    plt.close()


def make_regplot_ci(df: pd.DataFrame, x_col: str, y_col: str, filename: str, title: str, y_label: str) -> None:
    plt.figure(figsize=(8, 5))
    sns.regplot(data=df, x=x_col, y=y_col, ci=95, scatter_kws={"alpha": 0.8})
    plt.title(title)
    plt.ylabel(y_label)
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=300)
    plt.close()


def make_pre_post_lmplot(df: pd.DataFrame, x_col: str, y_col: str, filename: str, title: str, y_label: str) -> None:
    tmp = df.copy()
    tmp["period"] = tmp["post2020"].map({0: "Pre-2020", 1: "Post-2020"})

    g = sns.lmplot(
        data=tmp,
        x=x_col,
        y=y_col,
        hue="period",
        ci=95,
        height=5.5,
        aspect=1.25,
        scatter_kws={"alpha": 0.85},
    )
    g.set_ylabels(y_label)
    g.fig.subplots_adjust(top=0.88)
    g.fig.suptitle(title)
    g.savefig(PLOTS_DIR / filename, dpi=300)
    plt.close("all")


def make_coefficient_plot(
    detailed_df: pd.DataFrame,
    model_name: str,
    outcome_name: str,
    filename: str,
    title: str,
) -> None:
    plot_df = detailed_df[
        (detailed_df["model"] == model_name)
        & (detailed_df["outcome"] == outcome_name)
        & (detailed_df["sample"] == "full_sample")
        & (detailed_df["term"] != "const")
    ].copy()

    if plot_df.empty:
        return

    plot_df = plot_df.sort_values("coef")
    y_pos = np.arange(len(plot_df))

    plt.figure(figsize=(9, 5))
    plt.errorbar(
        plot_df["coef"],
        y_pos,
        xerr=[plot_df["coef"] - plot_df["ci_lower"], plot_df["ci_upper"] - plot_df["coef"]],
        fmt="o",
        capsize=4,
    )
    plt.axvline(0, linestyle="--")
    plt.yticks(y_pos, plot_df["term"])
    plt.title(title)
    plt.xlabel("Coefficient Estimate")
    plt.ylabel("Term")
    plt.tight_layout()
    plt.savefig(PLOTS_DIR / filename, dpi=300)
    plt.close()


def print_corr_section(corr_df: pd.DataFrame, outcome_label: str) -> None:
    print(f"\n── Correlation Analysis ({outcome_label}) ─────────────────────────────")
    for _, row in corr_df.iterrows():
        print(
            f"  {row['variable']:<25} "
            f"pre={row['pre2020_r']:+.3f}  "
            f"post={row['post2020_r']:+.3f}  "
            f"delta={row['delta_post_minus_pre']:+.3f}"
        )


def print_model_section(detailed_df: pd.DataFrame, outcome_name: str, outcome_label: str) -> None:
    print(f"\n── Regression Analysis ({outcome_label}) ────────────────────────────")

    pretty_names = {
        "model1_socioeconomic": "Model 1: Socioeconomic variables",
        "model2_plus_post2020": "Model 2: + post2020 dummy",
        "model3_interaction": "Model 3: hardship_index × post2020 interaction",
        "model4_district_fixed_effects": "Model 4: District fixed effects",
    }

    order = [
        "model1_socioeconomic",
        "model2_plus_post2020",
        "model3_interaction",
        "model4_district_fixed_effects",
    ]

    for model_name in order:
        subset = detailed_df[
            (detailed_df["sample"] == "full_sample")
            & (detailed_df["outcome"] == outcome_name)
            & (detailed_df["model"] == model_name)
        ].copy()

        if subset.empty:
            continue

        print(f"\n{pretty_names[model_name]}")
        print("-" * 60)

        for _, row in subset.iterrows():
            if row["term"] == "const":
                term_name = "intercept"
            else:
                term_name = row["term"]

            print(
                f"  {term_name:<25} "
                f"coef={row['coef']:+.4f}  "
                f"p={row['p_value']:.4f} {row['sig']}"
            )

        print(f"  {'R-squared':<25} {subset['r_squared'].iloc[0]:.4f}")
        print(f"  {'N':<25} {int(subset['n_obs'].iloc[0])}")


def print_robustness_section(robust_df: pd.DataFrame, outcome_name: str, outcome_label: str) -> None:
    print(f"\n── Robustness Check ({outcome_label}) ───────────────────────────────")

    subset = robust_df[
        (robust_df["model"] == "model3_interaction")
        & (robust_df["outcome"] == outcome_name)
    ].copy()

    if subset.empty:
        print("  No robustness results available.")
        return

    for _, row in subset.iterrows():
        print(f"  Sample: {row['sample']}")
        print(f"    hardship_index coef     = {row.get('hardship_index_coef', np.nan):+.4f}")
        print(f"    hardship_index p        = {row.get('hardship_index_p', np.nan):.4f} {row.get('hardship_index_sig', '')}")
        print(f"    post2020 coef           = {row.get('post2020_coef', np.nan):+.4f}")
        print(f"    post2020 p              = {row.get('post2020_p', np.nan):.4f} {row.get('post2020_sig', '')}")
        print(f"    interaction coef        = {row.get('hardship_x_post2020_coef', np.nan):+.4f}")
        print(f"    interaction p           = {row.get('hardship_x_post2020_p', np.nan):.4f} {row.get('hardship_x_post2020_sig', '')}")
        print(f"    R-squared               = {row['r_squared']:.4f}")
        print(f"    N                       = {int(row['n_obs'])}")


def print_key_findings(corr_df: pd.DataFrame, detailed_df: pd.DataFrame, outcome_name: str, outcome_label: str) -> None:
    print(f"\n── Key Findings ({outcome_label}) ───────────────────────────────────")

    hardship = corr_df[corr_df["variable"] == "hardship_index"]
    income = corr_df[corr_df["variable"] == "per_capita_income"]

    if not hardship.empty:
        row = hardship.iloc[0]
        print(
            f"  • Hardship correlation changed from {row['pre2020_r']:+.3f} "
            f"to {row['post2020_r']:+.3f} (delta {row['delta_post_minus_pre']:+.3f})"
        )

    if not income.empty:
        row = income.iloc[0]
        print(
            f"  • Income correlation changed from {row['pre2020_r']:+.3f} "
            f"to {row['post2020_r']:+.3f} (delta {row['delta_post_minus_pre']:+.3f})"
        )

    interaction = detailed_df[
        (detailed_df["sample"] == "full_sample")
        & (detailed_df["outcome"] == outcome_name)
        & (detailed_df["model"] == "model3_interaction")
        & (detailed_df["term"] == "hardship_x_post2020")
    ]
    if not interaction.empty:
        row = interaction.iloc[0]
        direction = "weakened" if row["coef"] < 0 else "strengthened"
        print(
            f"  • Interaction term is {row['coef']:+.4f} (p={row['p_value']:.4f} {row['sig']}), "
            f"suggesting the hardship effect {direction} after 2020"
        )


# =========================
# Main
# =========================
def main() -> None:
    ensure_dirs()

    print("=== CP4 Robustness & Statistical Validation ===\n")

    notes = []

    # Load and prep
    df = load_panel()
    print(f"Panel: {len(df)} rows, {df['district'].nunique()} districts")
    notes.append(f"Loaded CP3 panel with {len(df)} rows across {df['district'].nunique()} districts.")

    df, has_population = merge_population(df)
    if has_population:
        valid_pop = df["population"].notna().sum() if "population" in df.columns else 0
        districts_with_pop = df.loc[df["population"].notna(), "district"].nunique() if "population" in df.columns else 0
        print(
            f"Population normalization available: yes "
            f"({districts_with_pop} districts with population data, {valid_pop} rows matched)"
        )
        notes.append("Population file found. Added violent_crime_rate_per_100k and log_crime_rate.")
    else:
        print("Population normalization available: no (skipping normalized-rate models)")
        notes.append(
            "Population file not found. Skipped normalized-rate models. "
            "Add data/cp4_district_population.csv with columns district,population to enable."
        )

    df.to_csv(CP4_PANEL_PATH, index=False)

    outcomes = [("violent_crime_count", "Raw Crime Count")]
    if has_population and "violent_crime_rate_per_100k" in df.columns:
        outcomes.append(("violent_crime_rate_per_100k", "Crime Rate per 100k"))

    all_corr = []
    all_detailed = []
    summary_text_paths = []

    # Full sample analyses
    for outcome_col, outcome_label in outcomes:
        corr_df = compute_period_correlations(df, outcome_col)
        all_corr.append(corr_df)
        print_corr_section(corr_df, outcome_label)

        models, detailed = run_models(df, outcome_col, "full_sample")
        all_detailed.append(detailed)
        print_model_section(detailed, outcome_col, outcome_label)

        txt_path = DATA_DIR / f"cp4_{outcome_col}_full_sample_results.txt"
        save_model_summaries(models, txt_path, f"CP4 Regression Results — {outcome_label} — Full Sample")
        summary_text_paths.append(txt_path.name)

    # Outlier robustness: exclude District 12
    print("\n── Outlier Analysis ─────────────────────────────────────────────────")
    df_no12 = df[df["district"] != 12].copy()
    print(
        f"Excluding District 12: {len(df_no12)} rows remain across "
        f"{df_no12['district'].nunique()} districts"
    )
    notes.append(
        f"Outlier robustness sample excludes District 12 and contains {len(df_no12)} rows."
    )

    for outcome_col, outcome_label in outcomes:
        models, detailed = run_models(df_no12, outcome_col, "exclude_district_12")
        all_detailed.append(detailed)

        txt_path = DATA_DIR / f"cp4_{outcome_col}_exclude_district12_results.txt"
        save_model_summaries(
            models,
            txt_path,
            f"CP4 Regression Results — {outcome_label} — Excluding District 12",
        )
        summary_text_paths.append(txt_path.name)

    # Save tables
    corr_out = pd.concat(all_corr, ignore_index=True)
    corr_out.to_csv(CP4_CORR_PATH, index=False)

    detailed_out = pd.concat(all_detailed, ignore_index=True)
    detailed_out.to_csv(CP4_REG_DETAILED_PATH, index=False)

    robustness_df = robustness_summary_from_detailed(detailed_out)
    robustness_df.to_csv(CP4_ROBUSTNESS_PATH, index=False)

    # Print robustness + key findings
    for outcome_col, outcome_label in outcomes:
        print_robustness_section(robustness_df, outcome_col, outcome_label)

        outcome_corr = corr_out[corr_out["outcome"] == outcome_col]
        print_key_findings(outcome_corr, detailed_out, outcome_col, outcome_label)

    # Plots: raw counts
    print("\nGenerating plots...")
    make_time_trend_plot(
        df,
        "violent_crime_count",
        "cp4_time_trend_counts.png",
        "Average Violent Crime Count by Year",
        "Violent Crime Count",
    )
    print("  ✓ Saved plots/cp4_time_trend_counts.png")

    make_regplot_ci(
        df,
        "hardship_index",
        "violent_crime_count",
        "cp4_hardship_vs_crime_ci.png",
        "Hardship Index vs Violent Crime Count (95% CI)",
        "Violent Crime Count",
    )
    print("  ✓ Saved plots/cp4_hardship_vs_crime_ci.png")

    make_regplot_ci(
        df,
        "per_capita_income",
        "violent_crime_count",
        "cp4_income_vs_crime_ci.png",
        "Per Capita Income vs Violent Crime Count (95% CI)",
        "Violent Crime Count",
    )
    print("  ✓ Saved plots/cp4_income_vs_crime_ci.png")

    make_pre_post_lmplot(
        df,
        "hardship_index",
        "violent_crime_count",
        "cp4_pre_post_hardship.png",
        "Pre/Post 2020: Hardship Index vs Violent Crime Count",
        "Violent Crime Count",
    )
    print("  ✓ Saved plots/cp4_pre_post_hardship.png")

    make_pre_post_lmplot(
        df,
        "per_capita_income",
        "violent_crime_count",
        "cp4_pre_post_income.png",
        "Pre/Post 2020: Income vs Violent Crime Count",
        "Violent Crime Count",
    )
    print("  ✓ Saved plots/cp4_pre_post_income.png")

    make_coefficient_plot(
        detailed_out,
        "model3_interaction",
        "violent_crime_count",
        "cp4_coef_plot_counts.png",
        "Coefficient Plot: Interaction Model (Raw Crime Count)",
    )
    print("  ✓ Saved plots/cp4_coef_plot_counts.png")

    # Optional plots: normalized rates
    if has_population and "violent_crime_rate_per_100k" in df.columns:
        make_time_trend_plot(
            df,
            "violent_crime_rate_per_100k",
            "cp4_time_trend_rate.png",
            "Average Violent Crime Rate per 100k by Year",
            "Violent Crime Rate per 100k",
        )
        print("  ✓ Saved plots/cp4_time_trend_rate.png")

        make_regplot_ci(
            df,
            "hardship_index",
            "violent_crime_rate_per_100k",
            "cp4_hardship_vs_rate_ci.png",
            "Hardship Index vs Violent Crime Rate per 100k (95% CI)",
            "Violent Crime Rate per 100k",
        )
        print("  ✓ Saved plots/cp4_hardship_vs_rate_ci.png")

        make_regplot_ci(
            df,
            "per_capita_income",
            "violent_crime_rate_per_100k",
            "cp4_income_vs_rate_ci.png",
            "Per Capita Income vs Violent Crime Rate per 100k (95% CI)",
            "Violent Crime Rate per 100k",
        )
        print("  ✓ Saved plots/cp4_income_vs_rate_ci.png")

        make_pre_post_lmplot(
            df,
            "hardship_index",
            "violent_crime_rate_per_100k",
            "cp4_pre_post_hardship_rate.png",
            "Pre/Post 2020: Hardship Index vs Violent Crime Rate per 100k",
            "Violent Crime Rate per 100k",
        )
        print("  ✓ Saved plots/cp4_pre_post_hardship_rate.png")

        make_pre_post_lmplot(
            df,
            "per_capita_income",
            "violent_crime_rate_per_100k",
            "cp4_pre_post_income_rate.png",
            "Pre/Post 2020: Income vs Violent Crime Rate per 100k",
            "Violent Crime Rate per 100k",
        )
        print("  ✓ Saved plots/cp4_pre_post_income_rate.png")

        make_coefficient_plot(
            detailed_out,
            "model3_interaction",
            "violent_crime_rate_per_100k",
            "cp4_coef_plot_rate.png",
            "Coefficient Plot: Interaction Model (Crime Rate per 100k)",
        )
        print("  ✓ Saved plots/cp4_coef_plot_rate.png")

    # Notes file
    with open(CP4_NOTES_PATH, "w", encoding="utf-8") as f:
        f.write("Checkpoint 4 Analysis Notes\n")
        f.write("==========================\n\n")
        for line in notes:
            f.write(f"- {line}\n")

        f.write("\nGenerated summary files:\n")
        for name in summary_text_paths:
            f.write(f"- {name}\n")

        f.write("\nMain outputs:\n")
        f.write(f"- {CP4_PANEL_PATH.name}\n")
        f.write(f"- {CP4_CORR_PATH.name}\n")
        f.write(f"- {CP4_REG_DETAILED_PATH.name}\n")
        f.write(f"- {CP4_ROBUSTNESS_PATH.name}\n")

    print("\nSaved outputs:")
    print(f"  ✓ {CP4_PANEL_PATH}")
    print(f"  ✓ {CP4_CORR_PATH}")
    print(f"  ✓ {CP4_REG_DETAILED_PATH}")
    print(f"  ✓ {CP4_ROBUSTNESS_PATH}")
    print(f"  ✓ {CP4_NOTES_PATH}")

    print("\nDone. All outputs in data/ and plots/")


if __name__ == "__main__":
    main()