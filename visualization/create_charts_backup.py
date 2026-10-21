
from pathlib import Path

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_DIR = BASE_DIR / "outputs" / "csv"
CHART_DIR = BASE_DIR / "outputs" / "charts"
CHART_DIR.mkdir(parents=True, exist_ok=True)

summary = pd.read_csv(CSV_DIR / "population_summary.csv")
districts = pd.read_csv(CSV_DIR / "population_by_district.csv")
growth = pd.read_csv(CSV_DIR / "growth_2001_2011.csv")

# Remove Hive table prefixes from column names
summary.columns = [c.split(".")[-1] for c in summary.columns]
districts.columns = [c.split(".")[-1] for c in districts.columns]
growth.columns = [c.split(".")[-1] for c in growth.columns]

# Chart 1: Total population by census year
summary = summary.sort_values("census_year")
plt.figure(figsize=(9, 5))
plt.bar(summary["census_year"].astype(str), summary["total_population"])
plt.title("Gujarat Total Population by Census Year")
plt.xlabel("Census Year")
plt.ylabel("Population")
plt.ticklabel_format(axis="y", style="plain")
plt.tight_layout()
plt.savefig(CHART_DIR / "total_population.png", dpi=150)
plt.close()

# Chart 2: Top 10 districts by 2011 population
latest = districts[districts["census_year"] == 2011]
top10 = latest.nlargest(10, "total_population").sort_values("total_population")

plt.figure(figsize=(10, 6))
plt.barh(top10["district"], top10["total_population"])
plt.title("Top 10 Gujarat Districts by Population (2011)")
plt.xlabel("Population")
plt.ylabel("District")
plt.ticklabel_format(axis="x", style="plain")
plt.tight_layout()
plt.savefig(CHART_DIR / "top10_districts.png", dpi=150)
plt.close()

# Chart 3: Top 10 districts by 2001–2011 growth
top_growth = growth.nlargest(10, "growth_percentage").sort_values(
    "growth_percentage"
)

plt.figure(figsize=(10, 6))
plt.barh(top_growth["district"], top_growth["growth_percentage"])
plt.title("Top 10 Districts by Population Growth (2001–2011)")
plt.xlabel("Growth (%)")
plt.ylabel("District")
plt.tight_layout()
plt.savefig(CHART_DIR / "population_growth.png", dpi=150)
plt.close()

# Chart 4: Urbanization comparison
plt.figure(figsize=(8, 5))
plt.bar(
    summary["census_year"].astype(str),
    summary["urbanization_percentage"],
)
plt.title("Gujarat Urbanization Percentage")
plt.xlabel("Census Year")
plt.ylabel("Urban Population (%)")
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig(CHART_DIR / "urbanization.png", dpi=150)
plt.close()

print("Charts created successfully:")
for path in sorted(CHART_DIR.glob("*.png")):
    print(f"{path.relative_to(BASE_DIR)} ({path.stat().st_size:,} bytes)")
