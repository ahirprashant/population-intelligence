
from pathlib import Path

import pandas as pd
import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


# ==================================================
# 1. PROJECT CONFIGURATION
# ==================================================

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_FILE = BASE_DIR / "data" / "raw" / "population.csv"
CHART_DIR = BASE_DIR / "outputs" / "charts"

CHART_DIR.mkdir(parents=True, exist_ok=True)

CENSUS_YEARS = [1961, 1971, 1981, 1991, 2001, 2011]

POPULATION_METRICS = [
    "Total Population",
    "Rural Population",
    "Urban Population",
    "Male Population",
    "Female Population",
]

plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["axes.titlesize"] = 14
plt.rcParams["axes.labelsize"] = 11
plt.rcParams["font.size"] = 10


# ==================================================
# 2. HELPER FUNCTIONS
# ==================================================

def format_population(value, position=None):
    """Format population values with comma separators."""
    return f"{value:,.0f}"


def save_chart(filename):
    """Save chart to the output directory."""
    plt.tight_layout()

    output_path = CHART_DIR / filename

    plt.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close()

    print(
        f"Created: {output_path.relative_to(BASE_DIR)}"
    )


def print_section(title):
    """Print a readable terminal section heading."""
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


# ==================================================
# 3. LOAD RAW CENSUS DATA
# ==================================================

print_section("LOADING POPULATION DATA")

if not RAW_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {RAW_FILE}"
    )

df = pd.read_csv(RAW_FILE)

df.columns = df.columns.str.strip()

if "District" not in df.columns:
    raise ValueError(
        "The CSV must contain a 'District' column."
    )

df["District"] = (
    df["District"]
    .astype(str)
    .str.strip()
)

# Remove aggregate/state rows if present.
aggregate_names = {
    "total",
    "gujarat total",
    "state total",
    "gujarat",
}

df = df[
    ~df["District"].str.casefold().isin(aggregate_names)
].copy()

print(f"Dataset: {RAW_FILE}")
print(f"District rows loaded: {len(df)}")


# ==================================================
# 4. CLEAN POPULATION COLUMNS
# ==================================================

print_section("CLEANING POPULATION DATA")

required_columns = []

for year in CENSUS_YEARS:
    for metric in POPULATION_METRICS:
        column = f"{year} - {metric}"
        required_columns.append(column)

        if column not in df.columns:
            raise ValueError(
                f"Required column missing: {column}"
            )

        # Remove commas and convert values to numbers.
        df[column] = pd.to_numeric(
            df[column]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.strip()
            .replace(
                {
                    "": None,
                    "nan": None,
                    "None": None,
                }
            ),
            errors="coerce",
        )

print("Population columns cleaned successfully.")


# ==================================================
# 5. CREATE CENSUS SUMMARY TABLE
# ==================================================

summary_records = []

for year in CENSUS_YEARS:

    total = df[f"{year} - Total Population"].sum()
    male = df[f"{year} - Male Population"].sum()
    female = df[f"{year} - Female Population"].sum()
    rural = df[f"{year} - Rural Population"].sum()
    urban = df[f"{year} - Urban Population"].sum()

    urbanization = (
        urban / total * 100
        if total > 0
        else 0
    )

    summary_records.append(
        {
            "census_year": year,
            "total_population": total,
            "male_population": male,
            "female_population": female,
            "rural_population": rural,
            "urban_population": urban,
            "urbanization_percentage": urbanization,
        }
    )

summary = pd.DataFrame(summary_records)


# ==================================================
# 6. CHART 1: TOTAL POPULATION TREND
# ==================================================

print_section("GENERATING CHARTS")

plt.figure()

plt.plot(
    summary["census_year"],
    summary["total_population"],
    marker="o",
    linewidth=2.5,
)

plt.title("Gujarat Total Population Trend (1961–2011)")
plt.xlabel("Census Year")
plt.ylabel("Total Population")

plt.xticks(CENSUS_YEARS)

plt.gca().yaxis.set_major_formatter(
    FuncFormatter(format_population)
)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4,
)

save_chart("total_population.png")


# ==================================================
# 7. CHART 2: MALE VS FEMALE POPULATION
# ==================================================

plt.figure()

plt.plot(
    summary["census_year"],
    summary["male_population"],
    marker="o",
    linewidth=2.5,
    label="Male Population",
)

plt.plot(
    summary["census_year"],
    summary["female_population"],
    marker="o",
    linewidth=2.5,
    label="Female Population",
)

plt.title("Male vs Female Population (1961–2011)")
plt.xlabel("Census Year")
plt.ylabel("Population")

plt.xticks(CENSUS_YEARS)

plt.gca().yaxis.set_major_formatter(
    FuncFormatter(format_population)
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4,
)

save_chart("male_female_population.png")


# ==================================================
# 8. CHART 3: RURAL VS URBAN POPULATION
# ==================================================

plt.figure()

plt.plot(
    summary["census_year"],
    summary["rural_population"],
    marker="o",
    linewidth=2.5,
    label="Rural Population",
)

plt.plot(
    summary["census_year"],
    summary["urban_population"],
    marker="o",
    linewidth=2.5,
    label="Urban Population",
)

plt.title("Rural vs Urban Population (1961–2011)")
plt.xlabel("Census Year")
plt.ylabel("Population")

plt.xticks(CENSUS_YEARS)

plt.gca().yaxis.set_major_formatter(
    FuncFormatter(format_population)
)

plt.legend()

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4,
)

save_chart("rural_urban_population.png")


# ==================================================
# 9. CHART 4: TOP 10 DISTRICTS IN 2011
# ==================================================

year_2011_column = "2011 - Total Population"

top10 = (
    df[["District", year_2011_column]]
    .dropna(subset=[year_2011_column])
    .nlargest(10, year_2011_column)
    .sort_values(year_2011_column)
)

plt.figure(figsize=(10, 7))

plt.barh(
    top10["District"],
    top10[year_2011_column],
)

plt.title("Top 10 Districts by Population (2011)")
plt.xlabel("Population")
plt.ylabel("District")

plt.gca().xaxis.set_major_formatter(
    FuncFormatter(format_population)
)

plt.grid(
    axis="x",
    linestyle="--",
    alpha=0.3,
)

save_chart("top10_districts.png")


# ==================================================
# 10. CHART 5: POPULATION GROWTH, 2001–2011
# ==================================================

growth_df = df[
    [
        "District",
        "2001 - Total Population",
        "2011 - Total Population",
    ]
].copy()

growth_df = growth_df.rename(
    columns={
        "2001 - Total Population": "population_2001",
        "2011 - Total Population": "population_2011",
    }
)

valid_growth = (
    growth_df["population_2001"].notna()
    & growth_df["population_2011"].notna()
    & (growth_df["population_2001"] > 0)
)

growth_df = growth_df[valid_growth].copy()

growth_df["growth_percentage"] = (
    (
        growth_df["population_2011"]
        - growth_df["population_2001"]
    )
    / growth_df["population_2001"]
    * 100
)

top_growth = (
    growth_df
    .nlargest(10, "growth_percentage")
    .sort_values("growth_percentage")
)

plt.figure(figsize=(10, 7))

plt.barh(
    top_growth["District"],
    top_growth["growth_percentage"],
)

plt.title("Top 10 Districts by Population Growth (2001–2011)")
plt.xlabel("Population Growth (%)")
plt.ylabel("District")

plt.grid(
    axis="x",
    linestyle="--",
    alpha=0.3,
)

save_chart("population_growth.png")


# ==================================================
# 11. CHART 6: URBANIZATION TREND
# ==================================================

plt.figure()

plt.plot(
    summary["census_year"],
    summary["urbanization_percentage"],
    marker="o",
    linewidth=2.5,
)

plt.title("Gujarat Urbanization Trend (1961–2011)")
plt.xlabel("Census Year")
plt.ylabel("Urban Population (%)")

plt.xticks(CENSUS_YEARS)
plt.ylim(0, 100)

plt.grid(
    axis="y",
    linestyle="--",
    alpha=0.4,
)

save_chart("urbanization.png")


# ==================================================
# 12. EXPORT SUMMARY CSV
# ==================================================

summary_file = (
    CHART_DIR / "population_trend_summary.csv"
)

summary.to_csv(
    summary_file,
    index=False,
)

print(f"\nSummary CSV saved: {summary_file}")


# ==================================================
# 13. TABLE 1: POPULATION SUMMARY
# ==================================================

display_summary = summary.copy()

population_columns = [
    "total_population",
    "male_population",
    "female_population",
    "rural_population",
    "urban_population",
]

for column in population_columns:
    display_summary[column] = (
        display_summary[column]
        .map(lambda value: f"{value:,.0f}")
    )

display_summary["urbanization_percentage"] = (
    display_summary["urbanization_percentage"]
    .map(lambda value: f"{value:.2f}%")
)

print_section(
    "TABLE 1: POPULATION SUMMARY BY CENSUS YEAR"
)

print(
    display_summary.to_string(index=False)
)


# ==================================================
# 14. TABLE 2: TOP 10 DISTRICTS BY POPULATION
# ==================================================

top_table = top10[
    ["District", year_2011_column]
].copy()

top_table = top_table.rename(
    columns={
        "District": "District",
        year_2011_column: "Population_2011",
    }
)

top_table["Population_2011"] = (
    top_table["Population_2011"]
    .map(lambda value: f"{value:,.0f}")
)

top_table = top_table.sort_values(
    "Population_2011",
    key=lambda column: column.str.replace(
        ",", "", regex=False
    ).astype(float),
    ascending=False,
)

print_section(
    "TABLE 2: TOP 10 DISTRICTS BY POPULATION (2011)"
)

print(
    top_table.to_string(index=False)
)


# ==================================================
# 15. TABLE 3: TOP 10 DISTRICTS BY GROWTH
# ==================================================

growth_table = top_growth[
    ["District", "growth_percentage"]
].copy()

growth_table = growth_table.sort_values(
    "growth_percentage",
    ascending=False,
)

growth_table["growth_percentage"] = (
    growth_table["growth_percentage"]
    .map(lambda value: f"{value:.2f}%")
)

print_section(
    "TABLE 3: TOP 10 DISTRICTS BY POPULATION GROWTH (2001–2011)"
)

print(
    growth_table.to_string(index=False)
)


# ==================================================
# 16. FINAL STATUS
# ==================================================

print_section("PROJECT OUTPUT SUMMARY")

print("All charts and output tables generated successfully.")
print(f"Chart directory: {CHART_DIR}")
print(f"Summary CSV: {summary_file}")
print(f"Districts included: {len(df)}")
print(f"Census years: {CENSUS_YEARS}")
print(f"Charts generated: 6")
print(f"Tables displayed: 3")
