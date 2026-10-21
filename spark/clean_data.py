
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession, functions as F
from pyspark.sql.types import LongType

# --------------------------------------------------
# 1. Start Spark
# --------------------------------------------------
spark = (
    SparkSession.builder
    .appName("PopulationIntelligence-DataCleaning")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

RAW_PATH = "hdfs:///government-data/raw/population.csv"
PROCESSED_PATH = "hdfs:///government-data/processed"
DISTRICT_PATH = f"{PROCESSED_PATH}/districts"
AGGREGATE_PATH = f"{PROCESSED_PATH}/aggregate_total"
REPORT_PATH = f"{PROCESSED_PATH}/quality_report"

# --------------------------------------------------
# 2. Read CSV from HDFS
# --------------------------------------------------
df = (
    spark.read
    .option("header", True)
    .option("inferSchema", False)
    .option("nullValue", "NA")
    .option("mode", "PERMISSIVE")
    .csv(RAW_PATH)
)

initial_rows = df.count()
print(f"Rows read from HDFS: {initial_rows}")

# Clean column names' surrounding whitespace
for old_name in df.columns:
    new_name = old_name.strip()
    if old_name != new_name:
        df = df.withColumnRenamed(old_name, new_name)

# --------------------------------------------------
# 3. Identify aggregate row separately
# --------------------------------------------------
district_col = F.trim(F.col("District"))

aggregate_df = df.filter(F.lower(district_col) == "total")
district_df = df.filter(
    F.col("District").isNotNull()
    & (F.lower(district_col) != "total")
)

aggregate_rows = aggregate_df.count()
district_rows_before = district_df.count()

# --------------------------------------------------
# 4. Convert population columns to numeric
# --------------------------------------------------
population_columns = [
    c for c in df.columns
    if c != "District" and c != "Sl. No."
]

for c in population_columns:
    district_df = district_df.withColumn(
        c,
        F.regexp_replace(F.trim(F.col(f"`{c}`")), ",", "")
        .cast(LongType())
    )
    aggregate_df = aggregate_df.withColumn(
        c,
        F.regexp_replace(F.trim(F.col(f"`{c}`")), ",", "")
        .cast(LongType())
    )

# Sl. No. is an identifier, not a population measure

# --------------------------------------------------
# 5. Check duplicates
# --------------------------------------------------
duplicates_before = district_rows_before - district_df.dropDuplicates().count()

district_df = district_df.dropDuplicates()
district_rows_after = district_df.count()

# --------------------------------------------------
# 6. Data-quality checks
# --------------------------------------------------
missing_counts = {}
for c in population_columns:
    missing_counts[c] = district_df.filter(
        F.col(f"`{c}`").isNull()
    ).count()

# Validate male + female against total population
# Validate rural + urban against total population
validation_results = {}

for year in ["1961", "1971", "1981", "1991", "2001", "2011"]:
    total_col = f"{year} Total Population"
    male_col = f"{year} Male Population"
    female_col = f"{year} Female Population"
    rural_col = f"{year} Rural Population"
    urban_col = f"{year} Urban Population"

    if all(c in district_df.columns for c in
           [total_col, male_col, female_col]):
        valid_sex = district_df.filter(
            F.col(f"`{total_col}`").isNotNull()
            & F.col(f"`{male_col}`").isNotNull()
            & F.col(f"`{female_col}`").isNotNull()
        )

        sex_check = valid_sex.filter(
            F.col(f"`{male_col}`") + F.col(f"`{female_col}`")
            != F.col(f"`{total_col}`")
        ).count()

        validation_results[f"{year}_male_female_mismatches"] = sex_check

    if all(c in district_df.columns for c in
           [total_col, rural_col, urban_col]):
        valid_area = district_df.filter(
            F.col(f"`{total_col}`").isNotNull()
            & F.col(f"`{rural_col}`").isNotNull()
            & F.col(f"`{urban_col}`").isNotNull()
        )

        area_check = valid_area.filter(
            F.col(f"`{rural_col}`") + F.col(f"`{urban_col}`")
            != F.col(f"`{total_col}`")
        ).count()

        validation_results[f"{year}_rural_urban_mismatches"] = area_check

# --------------------------------------------------
# 7. Save cleaned data to HDFS as Parquet
# --------------------------------------------------
district_df.write.mode("overwrite").parquet(DISTRICT_PATH)

if aggregate_rows > 0:
    aggregate_df.write.mode("overwrite").parquet(AGGREGATE_PATH)

# --------------------------------------------------
# 8. Create and save quality report
# --------------------------------------------------
report = {
    "project": "Government Population Intelligence Dashboard",
    "stage": "Stage 4 - PySpark Data Cleaning",
    "generated_at_utc": datetime.now(timezone.utc).isoformat(),
    "source_path": RAW_PATH,
    "input_rows": initial_rows,
    "aggregate_rows_separated": aggregate_rows,
    "district_rows_before_deduplication": district_rows_before,
    "duplicate_rows_removed": duplicates_before,
    "clean_district_rows": district_rows_after,
    "population_missing_counts": missing_counts,
    "validation_mismatches": validation_results,
    "district_output_path": DISTRICT_PATH,
    "aggregate_output_path": AGGREGATE_PATH,
    "notes": [
        "Missing population values remain null; they are not replaced with zero.",
        "The aggregate Total row is kept separate from district-level records.",
        "Historical district boundaries may differ between census years."
    ]
}

report_df = spark.createDataFrame(
    [(json.dumps(report, ensure_ascii=False),)],
    ["report_json"]
)

report_df.coalesce(1).write.mode("overwrite").text(REPORT_PATH)

# Print useful summary
print("\n========== DATA CLEANING SUMMARY ==========")
print(f"Input rows: {initial_rows}")
print(f"Aggregate rows separated: {aggregate_rows}")
print(f"District rows before deduplication: {district_rows_before}")
print(f"Duplicate rows removed: {duplicates_before}")
print(f"Clean district rows: {district_rows_after}")
print(f"District data saved to: {DISTRICT_PATH}")
print(f"Aggregate row saved to: {AGGREGATE_PATH}")
print(f"Quality report saved to: {REPORT_PATH}")

print("\nMissing values by population column:")
for col_name, count in missing_counts.items():
    print(f"  {col_name}: {count}")

print("\nValidation mismatches:")
for check_name, count in validation_results.items():
    print(f"  {check_name}: {count}")

spark.stop()
