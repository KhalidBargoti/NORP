"""
cp2_eda.py
Checkpoint 2 — Exploratory Data Analysis on violent crime by district and year.
Run AFTER cp2_extraction.py has produced data/cp2_violent_crimes_by_district_year.csv.
Outputs:
  - data/cp2_eda_summary.csv          (district-level stats)
  - plots/cp2_citywide_trend.png      (citywide totals 2015–2024)
  - plots/cp2_district_heatmap.png    (district × year heatmap)
  - plots/cp2_pre_post_2020.png       (average per district pre vs post)
  - plots/cp2_pct_change.png          (% change pre → post by district)
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns

# ── Config ────────────────────────────────────────────────────────────────────

INPUT_CSV   = "data/cp2_violent_crimes_by_district_year.csv"
SUMMARY_CSV = "data/cp2_eda_summary.csv"
PLOT_DIR    = "plots"
PRE_YEARS   = list(range(2015, 2020))   # 2015–2019
POST_YEARS  = list(range(2020, 2025))   # 2020–2024

sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.dpi"] = 150

# ── Load ──────────────────────────────────────────────────────────────────────

def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["district"] = df["district"].astype(int)
    df["year"]     = df["year"].astype(int)
    return df


# ── Plot helpers ──────────────────────────────────────────────────────────────

def save(fig, name: str):
    os.makedirs(PLOT_DIR, exist_ok=True)
    path = os.path.join(PLOT_DIR, name)
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print(f"  ✓ Saved {path}")


# ── Analysis functions ────────────────────────────────────────────────────────

def plot_citywide_trend(df: pd.DataFrame):
    """Line chart of total citywide violent crimes per year."""
    annual = df.groupby("year")["violent_crime_count"].sum().reset_index()

    fig, ax = plt.subplots(figsize=(9, 4))
    ax.plot(annual["year"], annual["violent_crime_count"], marker="o", linewidth=2.2,
            color="#c0392b", label="Violent crimes")
    ax.axvline(2020, color="steelblue", linestyle="--", linewidth=1.4, label="2020 (COVID)")
    ax.set_title("Citywide Violent Crime Totals — Chicago (2015–2024)", fontsize=13)
    ax.set_xlabel("Year")
    ax.set_ylabel("Total Violent Crimes")
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend()
    save(fig, "cp2_citywide_trend.png")


def plot_district_heatmap(df: pd.DataFrame):
    """Heatmap of violent crime counts: rows = district, cols = year."""
    pivot = df.pivot_table(index="district", columns="year",
                           values="violent_crime_count", aggfunc="sum")
    pivot = pivot.sort_index()

    fig, ax = plt.subplots(figsize=(13, 8))
    sns.heatmap(pivot, ax=ax, cmap="YlOrRd", linewidths=0.4,
                fmt=".0f", annot=True, annot_kws={"size": 7},
                cbar_kws={"label": "Violent Crime Count"})
    ax.set_title("Violent Crime by District and Year — Chicago (2015–2024)", fontsize=13)
    ax.set_xlabel("Year")
    ax.set_ylabel("Police District")
    save(fig, "cp2_district_heatmap.png")


def plot_pre_post_comparison(df: pd.DataFrame):
    """Grouped bar chart: average annual violent crimes per district, pre vs post 2020."""
    pre  = df[df["year"].isin(PRE_YEARS)].groupby("district")["violent_crime_count"].mean()
    post = df[df["year"].isin(POST_YEARS)].groupby("district")["violent_crime_count"].mean()

    comp = pd.DataFrame({"Pre-2020 (avg)": pre, "Post-2020 (avg)": post}).dropna()
    comp = comp.sort_index()

    x     = range(len(comp))
    width = 0.38

    fig, ax = plt.subplots(figsize=(13, 5))
    ax.bar([i - width/2 for i in x], comp["Pre-2020 (avg)"],  width, label="Pre-2020",
           color="#2980b9", alpha=0.85)
    ax.bar([i + width/2 for i in x], comp["Post-2020 (avg)"], width, label="Post-2020",
           color="#e74c3c", alpha=0.85)
    ax.set_xticks(list(x))
    ax.set_xticklabels(comp.index, fontsize=8)
    ax.set_title("Average Annual Violent Crimes per District — Pre vs Post 2020", fontsize=13)
    ax.set_xlabel("Police District")
    ax.set_ylabel("Avg Violent Crimes / Year")
    ax.legend()
    save(fig, "cp2_pre_post_2020.png")


def plot_pct_change(df: pd.DataFrame):
    """Horizontal bar chart of % change in avg violent crime, pre → post 2020, by district."""
    pre  = df[df["year"].isin(PRE_YEARS)].groupby("district")["violent_crime_count"].mean()
    post = df[df["year"].isin(POST_YEARS)].groupby("district")["violent_crime_count"].mean()

    pct = ((post - pre) / pre * 100).dropna().sort_values()

    colors = ["#e74c3c" if v > 0 else "#27ae60" for v in pct]

    fig, ax = plt.subplots(figsize=(7, 9))
    ax.barh(pct.index.astype(str), pct.values, color=colors, edgecolor="white")
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_title("% Change in Avg Violent Crimes by District\n(Pre-2020 → Post-2020)", fontsize=12)
    ax.set_xlabel("% Change")
    ax.set_ylabel("District")
    save(fig, "cp2_pct_change.png")


def build_summary(df: pd.DataFrame) -> pd.DataFrame:
    """District-level summary table exported to CSV."""
    pre  = df[df["year"].isin(PRE_YEARS)].groupby("district")["violent_crime_count"].mean().rename("avg_pre2020")
    post = df[df["year"].isin(POST_YEARS)].groupby("district")["violent_crime_count"].mean().rename("avg_post2020")
    total = df.groupby("district")["violent_crime_count"].sum().rename("total_2015_2024")
    peak_year = df.loc[df.groupby("district")["violent_crime_count"].idxmax(), ["district", "year"]].set_index("district")["year"].rename("peak_year")

    summary = pd.concat([pre, post, total, peak_year], axis=1).dropna()
    summary["pct_change"] = ((summary["avg_post2020"] - summary["avg_pre2020"])
                              / summary["avg_pre2020"] * 100).round(1)
    summary = summary.sort_values("total_2015_2024", ascending=False)
    summary.to_csv(SUMMARY_CSV)
    return summary


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    if not os.path.exists(INPUT_CSV):
        print(f"ERROR: {INPUT_CSV} not found. Run cp2_extraction.py first.")
        return

    print("=== CP2 Exploratory Data Analysis ===\n")
    df = load_data(INPUT_CSV)
    print(f"Loaded {len(df)} rows | {df['district'].nunique()} districts | "
          f"{df['year'].min()}–{df['year'].max()}\n")

    print("Generating plots...")
    plot_citywide_trend(df)
    plot_district_heatmap(df)
    plot_pre_post_comparison(df)
    plot_pct_change(df)

    print("\nBuilding summary table...")
    summary = build_summary(df)
    print(f"  ✓ Saved {SUMMARY_CSV}\n")

    print("── District Summary (top 10 by total crimes) ──────────────────────")
    print(summary.head(10).to_string())

    print("\n── Key observations ────────────────────────────────────────────────")
    increased = (summary["pct_change"] > 0).sum()
    decreased = (summary["pct_change"] < 0).sum()
    print(f"  Districts with MORE violent crime post-2020 : {increased}")
    print(f"  Districts with LESS violent crime post-2020 : {decreased}")
    print(f"  Median % change across districts            : {summary['pct_change'].median():.1f}%")
    print(f"  Largest increase : District {summary['pct_change'].idxmax()} "
          f"(+{summary['pct_change'].max():.1f}%)")
    print(f"  Largest decrease : District {summary['pct_change'].idxmin()} "
          f"({summary['pct_change'].min():.1f}%)")

    print("\nDone. All outputs in data/ and plots/")


if __name__ == "__main__":
    main()
