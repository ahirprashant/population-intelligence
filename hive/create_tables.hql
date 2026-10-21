
USE population_intelligence;

CREATE EXTERNAL TABLE IF NOT EXISTS population_by_district (
    District STRING,
    Census_Year INT,
    Total_Population BIGINT,
    Male_Population BIGINT,
    Female_Population BIGINT,
    Rural_Population BIGINT,
    Urban_Population BIGINT,
    Urbanization_Percentage DOUBLE
)
STORED AS PARQUET
LOCATION 'hdfs:///government-data/processed/kpis/population_by_district';

CREATE EXTERNAL TABLE IF NOT EXISTS growth_2001_2011 (
    District STRING,
    Population_2001 BIGINT,
    Population_2011 BIGINT,
    Population_Change BIGINT,
    Growth_Percentage DOUBLE
)
STORED AS PARQUET
LOCATION 'hdfs:///government-data/processed/kpis/growth_2001_2011';

CREATE EXTERNAL TABLE IF NOT EXISTS population_summary (
    Census_Year INT,
    District_Count BIGINT,
    Total_Population BIGINT,
    Male_Population BIGINT,
    Female_Population BIGINT,
    Rural_Population BIGINT,
    Urban_Population BIGINT,
    Urbanization_Percentage DOUBLE
)
STORED AS PARQUET
LOCATION 'hdfs:///government-data/processed/kpis/population_summary';
