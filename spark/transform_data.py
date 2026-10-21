
from pyspark.sql import SparkSession, functions as F

spark = (
    SparkSession.builder
    .appName("PopulationIntelligence-Transformations")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

INPUT_PATH = "hdfs:///government-data/processed/districts"
OUTPUT_BASE = "hdfs:///government-data/processed/kpis"

# 1. Read cleaned district data
df = spark.read.parquet(INPUT_PATH)

print("Clean district rows:", df.count())

# 2. Create district-wise data for 2001 and 2011
def year_data(year):
    return df.select(
        F.col("District"),
        F.lit(int(year)).alias("Census_Year"),
        F.col(f"`{year} - Total Population`").alias("Total_Population"),
        F.col(f"`{year} - Male Population`").alias("Male_Population"),
        F.col(f"`{year} - Female Population`").alias("Female_Population"),
        F.col(f"`{year} - Rural Population`").alias("Rural_Population"),
        F.col(f"`{year} - Urban Population`").alias("Urban_Population")
    )

population_by_district = (
    year_data("2001")
    .unionByName(year_data("2011"))
)

# 3. Calculate urbanization percentage
population_by_district = population_by_district.withColumn(
    "Urbanization_Percentage",
    F.when(
        F.col("Total_Population") > 0,
        F.round(
            F.col("Urban_Population") * 100
            / F.col("Total_Population"),
            2
        )
    )
)

# 4. Calculate 2001-2011 population growth
old = year_data("2001").select(
    "District",
    F.col("Total_Population").alias("Population_2001")
)

new = year_data("2011").select(
    "District",
    F.col("Total_Population").alias("Population_2011")
)

growth = old.join(new, on="District", how="inner")

growth = growth.withColumn(
    "Population_Change",
    F.col("Population_2011") - F.col("Population_2001")
)

growth = growth.withColumn(
    "Growth_Percentage",
    F.when(
        F.col("Population_2001") > 0,
        F.round(
            F.col("Population_Change") * 100
            / F.col("Population_2001"),
            2
        )
    )
)

# 5. Create year-wise population summary
summary = (
    population_by_district
    .groupBy("Census_Year")
    .agg(
        F.count("District").alias("District_Count"),
        F.sum("Total_Population").alias("Total_Population"),
        F.sum("Male_Population").alias("Male_Population"),
        F.sum("Female_Population").alias("Female_Population"),
        F.sum("Rural_Population").alias("Rural_Population"),
        F.sum("Urban_Population").alias("Urban_Population")
    )
    .withColumn(
        "Urbanization_Percentage",
        F.when(
            F.col("Total_Population") > 0,
            F.round(
                F.col("Urban_Population") * 100
                / F.col("Total_Population"),
                2
            )
        )
    )
    .orderBy("Census_Year")
)

# 6. Save KPI outputs to HDFS as Parquet
(
    population_by_district.write
    .mode("overwrite")
    .parquet(f"{OUTPUT_BASE}/population_by_district")
)

(
    growth.write
    .mode("overwrite")
    .parquet(f"{OUTPUT_BASE}/growth_2001_2011")
)

(
    summary.write
    .mode("overwrite")
    .parquet(f"{OUTPUT_BASE}/population_summary")
)

# 7. Display results
print("\n========== POPULATION SUMMARY ==========")
summary.show(truncate=False)

print("\n========== TOP 10 DISTRICTS: 2011 ==========")
(
    population_by_district
    .filter(F.col("Census_Year") == 2011)
    .orderBy(F.desc("Total_Population"))
    .select(
        "District",
        "Total_Population",
        "Male_Population",
        "Female_Population",
        "Rural_Population",
        "Urban_Population",
        "Urbanization_Percentage"
    )
    .show(10, truncate=False)
)

print("\n========== POPULATION GROWTH: 2001-2011 ==========")
growth.orderBy(
    F.desc("Growth_Percentage")
).select(
    "District",
    "Population_2001",
    "Population_2011",
    "Population_Change",
    "Growth_Percentage"
).show(10, truncate=False)

print(f"\nKPI outputs saved under: {OUTPUT_BASE}")

spark.stop()
