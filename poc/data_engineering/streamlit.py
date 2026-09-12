import os
import streamlit as st

st.set_page_config(
    page_title="Area flights tracker",
    page_icon=":material/flight:",
    layout="wide",
)

conn = st.connection("snowflake", ttl=os.getenv("SNOWFLAKE_CONNECTION_TTL"))


@st.cache_data(ttl=300)
def load_flights():
    return conn.query("SELECT * FROM FLIGHTS")


@st.cache_data(ttl=300)
def load_airline_stats():
    return conn.query("""
        SELECT
            LEFT(ID, 3) AS airline,
            COUNT(*)     AS flights,
            ROUND(AVG(ALT)) AS avg_altitude,
            MIN(ALT) AS min_alt,
            MAX(ALT) AS max_alt
        FROM FLIGHTS
        GROUP BY airline
        ORDER BY flights DESC
    """)


@st.cache_data(ttl=300)
def load_dest_stats():
    return conn.query("""
        SELECT DEST AS airport, COUNT(*) AS flights
        FROM FLIGHTS
        GROUP BY DEST
        ORDER BY flights DESC
    """)


@st.cache_data(ttl=300)
def load_origin_stats():
    return conn.query("""
        SELECT ORIG AS airport, COUNT(*) AS flights
        FROM FLIGHTS
        GROUP BY ORIG
        ORDER BY flights DESC
    """)


@st.cache_data(ttl=300)
def load_altitude_distribution():
    return conn.query("""
        SELECT
            CASE
                WHEN ALT < 1000    THEN 'Ground (<1k ft)'
                WHEN ALT < 10000   THEN 'Low (1k-10k ft)'
                WHEN ALT < 25000   THEN 'Mid (10k-25k ft)'
                WHEN ALT < 35000   THEN 'High (25k-35k ft)'
                ELSE                    'Cruise (35k+ ft)'
            END AS altitude_band,
            COUNT(*) AS flights
        FROM FLIGHTS
        GROUP BY altitude_band
        ORDER BY MIN(ALT)
    """)


with st.spinner("Loading flight data..."):
    df = load_flights()
    airline_df = load_airline_stats()
    dest_df = load_dest_stats()
    origin_df = load_origin_stats()
    alt_df = load_altitude_distribution()

# ── Sidebar filters ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Filters", anchor=False)

    all_airlines = sorted(df["AIRLINE"].unique()) if "AIRLINE" in df.columns else sorted(airline_df["AIRLINE"].tolist())
    selected_airlines = st.multiselect(
        "Airlines",
        options=all_airlines,
        default=None,
        placeholder="All airlines",
    )

    alt_min = int(df["ALT"].min())
    alt_max = int(df["ALT"].max())
    alt_range = st.slider(
        "Altitude range (ft)",
        min_value=alt_min,
        max_value=alt_max,
        value=(alt_min, alt_max),
    )

    all_dests = sorted(df["DEST"].unique().tolist())
    selected_dests = st.multiselect(
        "Destination airports",
        options=all_dests,
        default=None,
        placeholder="All destinations",
    )

    if st.button("Refresh data", icon=":material/refresh:"):
        load_flights.clear()
        load_airline_stats.clear()
        load_dest_stats.clear()
        load_origin_stats.clear()
        load_altitude_distribution.clear()
        st.rerun()


# ── Apply filters ─────────────────────────────────────────────────────────────
filtered = df.copy()
filtered["AIRLINE"] = filtered["ID"].str[:3]

if selected_airlines:
    filtered = filtered[filtered["AIRLINE"].isin(selected_airlines)]
if selected_dests:
    filtered = filtered[filtered["DEST"].isin(selected_dests)]
filtered = filtered[(filtered["ALT"] >= alt_range[0]) & (filtered["ALT"] <= alt_range[1])]


# ── Header ────────────────────────────────────────────────────────────────────
st.title("Bay Area flights tracker", anchor=False)
st.caption(f"Live snapshot of {len(df):,} flights arriving at Bay Area airports")

# ── KPI row ───────────────────────────────────────────────────────────────────
total_flights = len(filtered)
unique_airlines = filtered["AIRLINE"].nunique()
unique_origins = filtered["ORIG"].nunique()
avg_alt = int(filtered["ALT"].mean()) if total_flights > 0 else 0
unique_dests = filtered["DEST"].nunique()

with st.container(horizontal=True):
    st.metric("Flights", f"{total_flights:,}", border=True)
    st.metric("Airlines", unique_airlines, border=True)
    st.metric("Origin airports", unique_origins, border=True)
    st.metric("Avg altitude", f"{avg_alt:,} ft", border=True)
    st.metric("Destinations", unique_dests, border=True)


# ── Map + altitude chart row ──────────────────────────────────────────────────
col_map, col_alt = st.columns([3, 2])

with col_map:
    with st.container(border=True):
        st.subheader("Flight positions", anchor=False)
        map_data = filtered[["LAT", "LON"]].rename(columns={"LAT": "latitude", "LON": "longitude"})
        st.map(map_data, use_container_width=True)

with col_alt:
    with st.container(border=True):
        st.subheader("Altitude distribution", anchor=False)
        # Recompute from filtered data
        def compute_alt_bands(data):
            bands = []
            for _, row in data.iterrows():
                alt = row["ALT"]
                if alt < 1000:
                    bands.append("Ground (<1k)")
                elif alt < 10000:
                    bands.append("Low (1k-10k)")
                elif alt < 25000:
                    bands.append("Mid (10k-25k)")
                elif alt < 35000:
                    bands.append("High (25k-35k)")
                else:
                    bands.append("Cruise (35k+)")
            data = data.copy()
            data["band"] = bands
            return data.groupby("band").size().reset_index(name="flights")

        alt_bands = compute_alt_bands(filtered)
        st.bar_chart(alt_bands, x="band", y="flights", horizontal=True, use_container_width=True)


# ── Airline + airport analysis row ────────────────────────────────────────────
col_airline, col_dest = st.columns(2)

with col_airline:
    with st.container(border=True):
        st.subheader("Flights by airline", anchor=False)
        airline_counts = (
            filtered.groupby("AIRLINE")
            .size()
            .reset_index(name="flights")
            .sort_values("flights", ascending=False)
        )
        st.bar_chart(airline_counts, x="AIRLINE", y="flights", use_container_width=True)

with col_dest:
    with st.container(border=True):
        st.subheader("Top origin airports", anchor=False)
        origin_counts = (
            filtered.groupby("ORIG")
            .size()
            .reset_index(name="flights")
            .sort_values("flights", ascending=False)
            .head(10)
        )
        st.bar_chart(origin_counts, x="ORIG", y="flights", use_container_width=True)


# ── Destination breakdown ─────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Destination airports breakdown", anchor=False)
    dest_counts = (
        filtered.groupby("DEST")
        .agg(flights=("DEST", "size"), avg_altitude=("ALT", "mean"), origins=("ORIG", "nunique"))
        .reset_index()
        .sort_values("flights", ascending=False)
    )
    dest_counts["avg_altitude"] = dest_counts["avg_altitude"].round(0).astype(int)
    st.dataframe(
        dest_counts,
        column_config={
            "DEST": st.column_config.TextColumn("Airport"),
            "flights": st.column_config.NumberColumn("Flights"),
            "avg_altitude": st.column_config.NumberColumn("Avg altitude (ft)", format="%d"),
            "origins": st.column_config.NumberColumn("Unique origins"),
        },
        hide_index=True,
        use_container_width=True,
    )


# ── Airline detail table ──────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Airline detail", anchor=False)
    airline_detail = (
        filtered.groupby("AIRLINE")
        .agg(
            flights=("AIRLINE", "size"),
            avg_alt=("ALT", "mean"),
            min_alt=("ALT", "min"),
            max_alt=("ALT", "max"),
            destinations=("DEST", "nunique"),
            origins=("ORIG", "nunique"),
        )
        .reset_index()
        .sort_values("flights", ascending=False)
    )
    airline_detail["avg_alt"] = airline_detail["avg_alt"].round(0).astype(int)
    st.dataframe(
        airline_detail,
        column_config={
            "AIRLINE": st.column_config.TextColumn("Airline"),
            "flights": st.column_config.NumberColumn("Flights"),
            "avg_alt": st.column_config.NumberColumn("Avg altitude (ft)", format="%d"),
            "min_alt": st.column_config.NumberColumn("Min alt (ft)", format="%d"),
            "max_alt": st.column_config.NumberColumn("Max alt (ft)", format="%d"),
            "destinations": st.column_config.NumberColumn("Destinations"),
            "origins": st.column_config.NumberColumn("Origins"),
        },
        hide_index=True,
        use_container_width=True,
    )


# ── Raw flight log ────────────────────────────────────────────────────────────
with st.expander("Raw flight data", icon=":material/table_chart:"):
    st.dataframe(
        filtered.drop(columns=["AIRLINE"], errors="ignore"),
        column_config={
            "ID": "Flight ID",
            "UTC": "Timestamp (UTC)",
            "ALT": st.column_config.NumberColumn("Altitude (ft)", format="%d"),
            "DEST": "Destination",
            "ORIG": "Origin",
            "ICAO": "ICAO hex",
            "LAT": st.column_config.NumberColumn("Latitude", format="%.4f"),
            "LON": st.column_config.NumberColumn("Longitude", format="%.4f"),
        },
        hide_index=True,
        use_container_width=True,
    )
