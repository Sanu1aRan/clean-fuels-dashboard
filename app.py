import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Clean Fuels for Cooking Dashboard",
    page_icon="🌍",
    layout="wide",
)

# ── Constants ─────────────────────────────────────────────────────────────────
REGION_MAP = {
    "East Asia & Pacific": ["CHN", "IDN", "PHL", "VNM", "THA", "MYS", "KHM", "MMR", "LAO", "PNG", "FJI", "MNG", "PRK", "KOR", "JPN", "AUS", "NZL", "WSM", "TON", "VUT"],
    "Europe & Central Asia": ["RUS", "DEU", "FRA", "GBR", "ITA", "ESP", "POL", "UKR", "KAZ", "UZB", "TUR", "ROU", "NLD", "BEL", "SWE", "CHE", "AUT", "CZE", "GRC", "PRT", "HUN", "BLR", "AZE", "GEO", "ARM", "TJK", "KGZ", "TKM", "MDA", "ALB", "MKD", "BIH", "SRB", "MNE", "XKX", "LTU", "LVA", "EST", "SVK", "SVN", "HRV", "BGR", "DNK", "FIN", "NOR", "IRL", "LUX", "ISL", "CYP", "MLT"],
    "Latin America & Caribbean": ["BRA", "MEX", "COL", "ARG", "PER", "VEN", "CHL", "ECU", "BOL", "PRY", "URY", "GUY", "SUR", "CRI", "PAN", "GTM", "HND", "SLV", "NIC", "DOM", "CUB", "HTI", "JAM", "TTO", "BRB", "GRD", "LCA", "VCT", "ATG", "DMA", "KNA"],
    "Middle East & North Africa": ["SAU", "IRN", "IRQ", "SYR", "YEM", "JOR", "LBN", "ISR", "PSE", "KWT", "ARE", "QAT", "BHR", "OMN", "EGY", "LBY", "TUN", "DZA", "MAR", "MLT", "DJI", "MRT"],
    "North America": ["USA", "CAN"],
    "South Asia": ["IND", "PAK", "BGD", "NPL", "LKA", "AFG", "MDV", "BTN"],
    "Sub-Saharan Africa": ["NGA", "ETH", "COD", "TZA", "KEN", "UGA", "GHA", "MOZ", "MDG", "CIV", "CMR", "AGO", "NER", "BFA", "MLI", "MWI", "ZMB", "SEN", "ZWE", "TCD", "GIN", "RWA", "BEN", "SOM", "SSD", "SLE", "TGO", "ERI", "LBR", "CAF", "MRT", "NAM", "BWA", "LSO", "GMB", "GNB", "GNQ", "GAB", "COG", "SWZ", "MUS", "CPV", "STP", "COM", "SYC", "ZAF"],
}

CODE_TO_REGION = {code: region for region, codes in REGION_MAP.items() for code in codes}

# ── Data loading ──────────────────────────────────────────────────────────────
@st.cache_data
def load_wb_csv(filepath):
    """Load a World Bank indicator CSV (skip the 4-row metadata header)."""
    df = pd.read_csv(filepath, skiprows=4)
    df = df.dropna(subset=["Country Code"])
    year_cols = [c for c in df.columns if c.strip().isdigit()]
    id_cols = ["Country Name", "Country Code"]
    df = df[id_cols + year_cols]
    df_long = df.melt(id_vars=id_cols, var_name="Year", value_name="Value")
    df_long["Year"] = df_long["Year"].astype(int)
    df_long = df_long.dropna(subset=["Value"])
    return df_long


@st.cache_data
def load_all_data():
    import glob

    def find_csv(keyword):
        matches = glob.glob(f"data/API_{keyword}*.csv")
        if not matches:
            return None
        return matches[0]

    total_path = find_csv("EG.CFT.ACCS.ZS")
    rural_path = find_csv("EG.CFT.ACCS.RU.ZS")
    urban_path = find_csv("EG.CFT.ACCS.UR.ZS")

    if not total_path:
        raise FileNotFoundError("Total dataset CSV not found in data/ folder.")
    if not rural_path:
        raise FileNotFoundError("Rural dataset CSV not found in data/ folder.")

    total = load_wb_csv(total_path)
    rural = load_wb_csv(rural_path)
    urban = load_wb_csv(urban_path) if urban_path else None

    total["Type"] = "Total"
    rural["Type"] = "Rural"

    frames = [total, rural]
    if urban is not None:
        urban["Type"] = "Urban"
        frames.append(urban)

    combined = pd.concat(frames, ignore_index=True)
    combined["Region"] = combined["Country Code"].map(CODE_TO_REGION).fillna("Other")
    return total, rural, urban, combined


# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.title("🌍 Dashboard Controls")
st.sidebar.markdown("**Clean Fuels for Cooking**")
st.sidebar.markdown("*% of population using clean cooking fuels (SDG 7.1.2)*")
st.sidebar.divider()

try:
    total_df, rural_df, urban_df, combined_df = load_all_data()
    data_loaded = True
except FileNotFoundError as e:
    data_loaded = False
    st.error(f"CSV file not found: {e}\n\nMake sure the three World Bank CSV files are placed in a `data/` folder.")
    st.stop()

all_years = sorted(total_df["Year"].unique())
min_year, max_year = int(min(all_years)), int(max(all_years))

selected_year = st.sidebar.slider("Select Year", min_year, max_year, max_year, step=1)

all_regions = sorted([r for r in combined_df["Region"].unique() if r != "Other"])
selected_regions = st.sidebar.multiselect("Filter Regions", all_regions, default=all_regions)

all_countries = sorted(total_df["Country Name"].unique())
selected_country = st.sidebar.selectbox("Select Country (Deep-Dive)", all_countries, index=all_countries.index("Sri Lanka") if "Sri Lanka" in all_countries else 0)

st.sidebar.divider()
st.sidebar.caption("Data source: World Bank / IEA / WHO — Tracking SDG 7")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🌍 Access to Clean Fuels for Cooking")
st.markdown(
    "**SDG 7.1.2** — This dashboard explores global progress on access to clean cooking fuels and technologies "
    "(2000–2022), a critical indicator for sustainability, public health, and gender equity."
)
st.divider()

# ── KPI row ───────────────────────────────────────────────────────────────────
year_data = total_df[total_df["Year"] == selected_year]
prev_year_data = total_df[total_df["Year"] == selected_year - 1]

global_avg = year_data["Value"].mean()
prev_avg   = prev_year_data["Value"].mean() if not prev_year_data.empty else global_avg
delta_avg  = global_avg - prev_avg

low_access  = year_data[year_data["Value"] < 20]
high_access = year_data[year_data["Value"] > 95]

col1, col2, col3, col4 = st.columns(4)
col1.metric("🌐 Global Average", f"{global_avg:.1f}%", f"{delta_avg:+.1f}% vs {selected_year-1}")
col2.metric("🔴 Countries < 20% Access", int(len(low_access)))
col3.metric("🟢 Countries > 95% Access", int(len(high_access)))
col4.metric("📅 Year", str(selected_year))

st.divider()

# ── Tab layout ────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🗺️ World Map", "📈 Regional Trends", "🔍 Country Deep-Dive", "🏙️ Urban vs Rural"])

# ─── Tab 1: Choropleth Map ────────────────────────────────────────────────────
with tab1:
    st.subheader(f"Global Access to Clean Cooking Fuels — {selected_year}")
    map_data = total_df[total_df["Year"] == selected_year]
    fig_map = px.choropleth(
        map_data,
        locations="Country Code",
        color="Value",
        hover_name="Country Name",
        color_continuous_scale="RdYlGn",
        range_color=[0, 100],
        labels={"Value": "Access (%)"},
        title=f"Access to Clean Fuels for Cooking (%) — {selected_year}",
    )
    fig_map.update_layout(
        coloraxis_colorbar=dict(title="Access (%)"),
        geo=dict(showframe=False, showcoastlines=True),
        margin=dict(l=0, r=0, t=40, b=0),
        height=500,
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption("Green = high access. Red = low access. Hover over a country for details.")

# ─── Tab 2: Regional Trends ───────────────────────────────────────────────────
with tab2:
    st.subheader("Regional Trends Over Time (2000–2022)")
    region_filtered = combined_df[
        (combined_df["Type"] == "Total") &
        (combined_df["Region"].isin(selected_regions))
    ]
    region_trend = (
        region_filtered.groupby(["Year", "Region"])["Value"]
        .mean()
        .reset_index()
    )
    fig_trend = px.line(
        region_trend,
        x="Year",
        y="Value",
        color="Region",
        markers=True,
        labels={"Value": "Avg Access (%)", "Year": "Year"},
        title="Average Access to Clean Cooking Fuels by Region",
    )
    fig_trend.update_layout(height=450, hovermode="x unified")
    st.plotly_chart(fig_trend, use_container_width=True)

    st.subheader(f"Top & Bottom 10 Countries — {selected_year}")
    col_top, col_bot = st.columns(2)
    top10 = year_data.nlargest(10, "Value")[["Country Name", "Value"]].reset_index(drop=True)
    bot10 = year_data.nsmallest(10, "Value")[["Country Name", "Value"]].reset_index(drop=True)
    top10.columns = ["Country", "Access (%)"]
    bot10.columns = ["Country", "Access (%)"]
    top10["Access (%)"] = top10["Access (%)"].round(1)
    bot10["Access (%)"] = bot10["Access (%)"].round(1)

    with col_top:
        st.markdown("**🟢 Top 10 — Highest Access**")
        fig_top = px.bar(top10, x="Access (%)", y="Country", orientation="h", color="Access (%)",
                         color_continuous_scale="Greens", range_color=[90, 100])
        fig_top.update_layout(height=350, showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_top, use_container_width=True)

    with col_bot:
        st.markdown("**🔴 Bottom 10 — Lowest Access**")
        fig_bot = px.bar(bot10, x="Access (%)", y="Country", orientation="h", color="Access (%)",
                         color_continuous_scale="Reds_r", range_color=[0, 20])
        fig_bot.update_layout(height=350, showlegend=False, coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        st.plotly_chart(fig_bot, use_container_width=True)

# ─── Tab 3: Country Deep-Dive ─────────────────────────────────────────────────
with tab3:
    st.subheader(f"Country Deep-Dive — {selected_country}")
    country_total = total_df[total_df["Country Name"] == selected_country].sort_values("Year")
    country_rural = rural_df[rural_df["Country Name"] == selected_country].sort_values("Year")
    country_urban = urban_df[urban_df["Country Name"] == selected_country].sort_values("Year")

    if country_total.empty:
        st.warning("No data available for this country.")
    else:
        latest = country_total.iloc[-1]["Value"]
        earliest = country_total.iloc[0]["Value"]
        change = latest - earliest

        kc1, kc2, kc3 = st.columns(3)
        kc1.metric("Latest Value", f"{latest:.1f}%", f"{change:+.1f}% since {int(country_total.iloc[0]['Year'])}")
        kc2.metric("Earliest Value", f"{earliest:.1f}%")
        kc3.metric("Years of Data", len(country_total))

        fig_country = go.Figure()
        fig_country.add_trace(go.Scatter(x=country_total["Year"], y=country_total["Value"],
                                          name="Total", line=dict(color="#2E86AB", width=3), mode="lines+markers"))
        if not country_urban.empty:
            fig_country.add_trace(go.Scatter(x=country_urban["Year"], y=country_urban["Value"],
                                              name="Urban", line=dict(color="#A23B72", width=2, dash="dash"), mode="lines+markers"))
        if not country_rural.empty:
            fig_country.add_trace(go.Scatter(x=country_rural["Year"], y=country_rural["Value"],
                                              name="Rural", line=dict(color="#F18F01", width=2, dash="dot"), mode="lines+markers"))

        fig_country.update_layout(
            title=f"Clean Fuel Access Trend — {selected_country}",
            xaxis_title="Year", yaxis_title="Access (%)",
            yaxis=dict(range=[0, 105]),
            height=400, hovermode="x unified",
        )
        st.plotly_chart(fig_country, use_container_width=True)

        # Regional comparison bar chart
        country_code = total_df[total_df["Country Name"] == selected_country]["Country Code"].iloc[0]
        country_region = CODE_TO_REGION.get(country_code, None)
        if country_region:
            region_year = total_df[
                (total_df["Year"] == selected_year) &
                (total_df["Country Code"].isin(REGION_MAP.get(country_region, [])))
            ].sort_values("Value", ascending=False)
            fig_reg = px.bar(
                region_year, x="Country Name", y="Value",
                color="Value", color_continuous_scale="RdYlGn", range_color=[0, 100],
                title=f"{selected_country} vs {country_region} peers — {selected_year}",
                labels={"Value": "Access (%)", "Country Name": "Country"},
            )
            highlight = region_year[region_year["Country Name"] == selected_country]
            if not highlight.empty:
                fig_reg.add_vline(
                    x=highlight.index[0] if False else selected_country,
                    line_dash="dash", line_color="black",
                )
            fig_reg.update_layout(height=380, xaxis_tickangle=-45, coloraxis_showscale=False)
            st.plotly_chart(fig_reg, use_container_width=True)

# ─── Tab 4: Urban vs Rural ────────────────────────────────────────────────────
with tab4:
    st.subheader("Urban vs Rural Access Gap")
    st.markdown("The gap between urban and rural populations reveals deep inequality in clean fuel access within countries.")

    gap_df = pd.merge(
        urban_df[["Country Name", "Country Code", "Year", "Value"]].rename(columns={"Value": "Urban"}),
        rural_df[["Country Name", "Country Code", "Year", "Value"]].rename(columns={"Value": "Rural"}),
        on=["Country Name", "Country Code", "Year"],
    )
    gap_df["Gap"] = gap_df["Urban"] - gap_df["Rural"]
    gap_year = gap_df[gap_df["Year"] == selected_year].dropna(subset=["Gap"])

    col_gap1, col_gap2 = st.columns(2)

    with col_gap1:
        top_gap = gap_year.nlargest(15, "Gap")[["Country Name", "Urban", "Rural", "Gap"]]
        fig_gap = px.bar(
            top_gap.sort_values("Gap"),
            x="Gap", y="Country Name", orientation="h",
            color="Gap", color_continuous_scale="OrRd",
            title=f"Top 15 Countries by Urban–Rural Gap ({selected_year})",
            labels={"Gap": "Gap (percentage points)", "Country Name": "Country"},
        )
        fig_gap.update_layout(height=480, coloraxis_showscale=False)
        st.plotly_chart(fig_gap, use_container_width=True)

    with col_gap2:
        fig_scatter = px.scatter(
            gap_year,
            x="Rural", y="Urban",
            hover_name="Country Name",
            color="Gap",
            color_continuous_scale="RdYlGn_r",
            title=f"Urban vs Rural Access — {selected_year}",
            labels={"Rural": "Rural Access (%)", "Urban": "Urban Access (%)"},
        )
        fig_scatter.add_shape(type="line", x0=0, y0=0, x1=100, y1=100,
                               line=dict(color="grey", dash="dash"))
        fig_scatter.update_layout(height=480)
        st.plotly_chart(fig_scatter, use_container_width=True)
        st.caption("Points above the diagonal = urban access exceeds rural access.")

    # Global gap trend using all 3
    global_gap = pd.merge(
        urban_df.groupby("Year")["Value"].mean().reset_index().rename(columns={"Value": "Urban"}),
        rural_df.groupby("Year")["Value"].mean().reset_index().rename(columns={"Value": "Rural"}),
        on="Year"
    )
    global_gap = pd.merge(
        global_gap,
        total_df.groupby("Year")["Value"].mean().reset_index().rename(columns={"Value": "National"}),
        on="Year"
    )
    global_gap_long = global_gap.melt(id_vars="Year", var_name="Type", value_name="Access (%)")
    fig_global_gap = px.area(
        global_gap_long, x="Year", y="Access (%)", color="Type",
        title="Global Average: Urban vs Rural vs National Access Trend",
        color_discrete_map={"Urban": "#A23B72", "Rural": "#F18F01", "National": "#2E86AB"},
    )
    fig_global_gap.update_layout(height=350, hovermode="x unified")
    st.plotly_chart(fig_global_gap, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("📊 Data: World Bank / IEA / WHO — Tracking SDG 7: The Energy Progress Report (2023) | Dashboard developed for 5DATA004C Individual Coursework")
