
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_FILE = BASE_DIR / "data" / "raw" / "population.csv"

st.set_page_config(
    page_title="Gujarat Population Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("Gujarat Population Intelligence Dashboard")
st.caption(
    "Historical Gujarat Census Data | 1961–2011 | "
    "Interactive demographic analysis"
)

YEARS = [1961, 1971, 1981, 1991, 2001, 2011]
METRICS = [
    "Total Population",
    "Rural Population",
    "Urban Population",
    "Male Population",
    "Female Population",
]


@st.cache_data
def load_data():
    df = pd.read_csv(RAW_FILE)
    df.columns = [c.strip().replace("\ufeff", "") for c in df.columns]

    if "District" not in df.columns:
        raise ValueError("CSV must contain a District column.")

    df["District"] = df["District"].astype(str).str.strip()

    # Convert population columns to numeric; preserve missing values.
    for year in YEARS:
        for metric in METRICS:
            col = f"{year} - {metric}"
            if col in df.columns:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(",", "", regex=False)
                    .replace({"nan": None, "": None}),
                    errors="coerce",
                )

    # Exclude aggregate rows from district-level charts.
    aggregate_names = {"total", "gujarat total", "state total"}
    districts = df[
        ~df["District"].str.lower().isin(aggregate_names)
    ].copy()

    # Convert wide census data into a long, filter-friendly table.
    records = []
    for year in YEARS:
        for metric in METRICS:
            col = f"{year} - {metric}"
            if col not in districts.columns:
                continue

            part = districts[["District", col]].copy()
            part.columns = ["District", "Population"]
            part["Year"] = year
            part["Metric"] = metric
            records.append(part)

    long_df = pd.concat(records, ignore_index=True)
    long_df["Population"] = pd.to_numeric(
        long_df["Population"], errors="coerce"
    )
    return districts, long_df


try:
    wide_df, long_df = load_data()
except Exception as exc:
    st.error(f"Could not load census data: {exc}")
    st.stop()

district_options = sorted(wide_df["District"].dropna().unique().tolist())

st.sidebar.header("Dashboard Filters")

year_options = ["All Years"] + YEARS
selected_year = st.sidebar.selectbox(
    "Census Year",
    year_options,
    index=0,
)

selected_districts = st.sidebar.multiselect(
    "Districts",
    district_options,
    default=district_options,
)

selected_metric = st.sidebar.selectbox(
    "Population Indicator",
    METRICS,
    index=0,
)

if not selected_districts:
    st.warning("Select at least one district from the sidebar.")
    st.stop()

# Apply district filter to all visualizations.
district_data = wide_df[
    wide_df["District"].isin(selected_districts)
].copy()

filtered_long = long_df[
    long_df["District"].isin(selected_districts)
].copy()

if selected_year != "All Years":
    filtered_long = filtered_long[
        filtered_long["Year"] == selected_year
    ]

# KPI year: selected year, or latest year when All Years is selected.
kpi_year = max(YEARS) if selected_year == "All Years" else selected_year

st.subheader(f"Population Overview — {kpi_year}")

kpi_data = district_data.copy()
kpi_columns = {
    metric: f"{kpi_year} - {metric}" for metric in METRICS
}

def safe_total(frame, column):
    if column not in frame.columns:
        return None
    values = frame[column].dropna()
    if values.empty:
        return None
    return values.sum()

total_pop = safe_total(kpi_data, kpi_columns["Total Population"])
male_pop = safe_total(kpi_data, kpi_columns["Male Population"])
female_pop = safe_total(kpi_data, kpi_columns["Female Population"])
urban_pop = safe_total(kpi_data, kpi_columns["Urban Population"])

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total Population",
    f"{total_pop:,.0f}" if total_pop is not None else "N/A",
)
k2.metric(
    "Male Population",
    f"{male_pop:,.0f}" if male_pop is not None else "N/A",
)
k3.metric(
    "Female Population",
    f"{female_pop:,.0f}" if female_pop is not None else "N/A",
)
k4.metric(
    "Urban Population",
    f"{urban_pop:,.0f}" if urban_pop is not None else "N/A",
)

st.caption(
    "KPIs sum the selected districts. Missing values are excluded, "
    "not treated as zero. Older census years may have incomplete data."
)

st.divider()

# 1. Total population trend across all available census years.
st.subheader("1. Total Population Trend — All Census Years")

trend = long_df[
    (long_df["District"].isin(selected_districts))
    & (long_df["Metric"] == "Total Population")
].groupby("Year", as_index=False)["Population"].sum(min_count=1)

if not trend.empty:
    st.line_chart(
        trend.set_index("Year")[["Population"]],
        y_label="Population",
        x_label="Census Year",
    )
else:
    st.info("No total population data is available for this selection.")

# 2. Male vs female trend.
st.subheader("2. Male vs Female Population — All Census Years")

sex_data = long_df[
    (long_df["District"].isin(selected_districts))
    & (long_df["Metric"].isin(["Male Population", "Female Population"]))
]

sex_trend = sex_data.pivot_table(
    index="Year",
    columns="Metric",
    values="Population",
    aggfunc="sum",
)

for col in ["Male Population", "Female Population"]:
    if col not in sex_trend.columns:
        sex_trend[col] = float("nan")

sex_trend = sex_trend[
    ["Male Population", "Female Population"]
].sort_index()

if sex_trend.notna().any().any():
    st.bar_chart(
        sex_trend,
        y_label="Population",
        x_label="Census Year",
    )
else:
    st.info("Male/female data is unavailable for this selection.")

st.divider()

# 3. Rural vs urban trend.
st.subheader("3. Rural vs Urban Population — All Census Years")

rural_urban = long_df[
    (long_df["District"].isin(selected_districts))
    & (
        long_df["Metric"].isin(
            ["Rural Population", "Urban Population"]
        )
    )
].pivot_table(
    index="Year",
    columns="Metric",
    values="Population",
    aggfunc="sum",
)

for col in ["Rural Population", "Urban Population"]:
    if col not in rural_urban.columns:
        rural_urban[col] = float("nan")

rural_urban = rural_urban[
    ["Rural Population", "Urban Population"]
].sort_index()

st.bar_chart(
    rural_urban,
    y_label="Population",
    x_label="Census Year",
)

# 4. District comparison for the selected year.
st.subheader(f"4. District Comparison — {kpi_year}")

district_metric_col = f"{kpi_year} - {selected_metric}"

if district_metric_col in district_data.columns:
    ranking = district_data[
        ["District", district_metric_col]
    ].rename(columns={district_metric_col: selected_metric})

    ranking[selected_metric] = pd.to_numeric(
        ranking[selected_metric], errors="coerce"
    )
    ranking = ranking.dropna().sort_values(
        selected_metric, ascending=False
    )

    if not ranking.empty:
        st.bar_chart(
            ranking.set_index("District"),
            y_label=selected_metric,
        )
    else:
        st.info("No data available for this indicator and year.")
else:
    st.info("This indicator is not available for the selected year.")

# 5. Filtered data table.
st.divider()
st.subheader("5. Filtered Census Data")

table_data = filtered_long[
    filtered_long["Metric"] == selected_metric
].copy()

if not table_data.empty:
    table_data = table_data[
        ["Year", "District", "Metric", "Population"]
    ].sort_values(["Year", "Population"], ascending=[True, False])

    st.dataframe(table_data, use_container_width=True, hide_index=True)

    st.download_button(
        "Download Filtered Data (CSV)",
        data=table_data.to_csv(index=False).encode("utf-8"),
        file_name="filtered_gujarat_census_data.csv",
        mime="text/csv",
    )
else:
    st.info("No records match the selected filters.")

st.caption(
    "Source: project raw census CSV. Verify the original source before "
    "describing the data as official government data. "
    "This dashboard shows historical census data, not current estimates."
)
