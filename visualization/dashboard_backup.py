
from pathlib import Path

import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent.parent
CSV_DIR = BASE_DIR / "outputs" / "csv"
CHART_DIR = BASE_DIR / "outputs" / "charts"

st.set_page_config(
    page_title="Gujarat Population Intelligence",
    page_icon="📊",
    layout="wide",
)

st.title("Gujarat Population Intelligence Dashboard")
st.caption("District population, demographic indicators, and growth | Census years 2001–2011")

@st.cache_data
def load_data():
    summary = pd.read_csv(CSV_DIR / "population_summary.csv")
    districts = pd.read_csv(CSV_DIR / "population_by_district.csv")
    growth = pd.read_csv(CSV_DIR / "growth_2001_2011.csv")

    for df in (summary, districts, growth):
        df.columns = [column.split(".")[-1] for column in df.columns]

    return summary, districts, growth

try:
    summary, districts, growth = load_data()
except Exception as error:
    st.error(f"Could not load dashboard data: {error}")
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard Filters")

years = sorted(districts["census_year"].dropna().unique().tolist())
selected_year = st.sidebar.selectbox(
    "Select census year",
    years,
    index=len(years) - 1,
)

district_options = sorted(districts["district"].dropna().unique().tolist())
selected_districts = st.sidebar.multiselect(
    "Select districts",
    district_options,
    default=district_options,
)

filtered = districts[
    (districts["census_year"] == selected_year)
    & (districts["district"].isin(selected_districts))
].copy()

year_summary = summary[summary["census_year"] == selected_year]

if year_summary.empty:
    st.error("No summary record is available for this census year.")
    st.stop()

record = year_summary.iloc[0]

# KPI cards
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Population", f"{int(record['total_population']):,}")
c2.metric("Districts", f"{int(record['district_count']):,}")
c3.metric("Urban Population", f"{int(record['urban_population']):,}")
c4.metric("Urbanization", f"{record['urbanization_percentage']:.2f}%")

st.divider()

# Charts
left, right = st.columns(2)

with left:
    st.subheader("Total Population by Census Year")
    chart_path = CHART_DIR / "total_population.png"
    if chart_path.exists():
        st.image(str(chart_path), width="stretch")

with right:
    st.subheader("Urbanization Comparison")
    chart_path = CHART_DIR / "urbanization.png"
    if chart_path.exists():
        st.image(str(chart_path), width="stretch")

left, right = st.columns(2)

with left:
    st.subheader("Top 10 Districts by Population (2011)")
    chart_path = CHART_DIR / "top10_districts.png"
    if chart_path.exists():
        st.image(str(chart_path), width="stretch")

with right:
    st.subheader("Top 10 Districts by Growth (2001–2011)")
    chart_path = CHART_DIR / "population_growth.png"
    if chart_path.exists():
        st.image(str(chart_path), width="stretch")

st.divider()

# District-level table
st.subheader(f"District Data — {selected_year}")

if filtered.empty:
    st.info("No districts match the selected filters.")
else:
    display_columns = [
        "district",
        "total_population",
        "male_population",
        "female_population",
        "rural_population",
        "urban_population",
        "urbanization_percentage",
    ]
    st.dataframe(
        filtered[display_columns].sort_values(
            "total_population", ascending=False
        ),
        width="stretch",
        hide_index=True,
    )

    csv_data = filtered[display_columns].to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered district data (CSV)",
        data=csv_data,
        file_name=f"gujarat_population_{selected_year}.csv",
        mime="text/csv",
    )

# Growth table
st.subheader("Population Growth: 2001–2011")
st.dataframe(
    growth.sort_values("growth_percentage", ascending=False),
    width="stretch",
    hide_index=True,
)

st.caption(
    "Data source: project CSV exports from the Hive tables. "
    "Verify the original dataset source before presenting it as official government data."
)
