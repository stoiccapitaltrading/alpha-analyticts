import streamlit as st
import pandas as pd
from PIL import Image
import base64
import os
import altair as alt

# Function to inject a sidebar logo at the top
def inject_sidebar_logo(image_path="logo.png"):
    with open(image_path, "rb") as image_file:
        encoded_logo = base64.b64encode(image_file.read()).decode()

    st.markdown(
        f"""
        <style>
        [data-testid="stSidebarNav"]::before {{
            content: "";
            display: block;
            margin-top: -60px;
            margin-bottom: 0px;
            height: 180px;
            background-image: url("data:image/png;base64,{encoded_logo}");
            background-repeat: no-repeat;
            background-size: contain;
            background-position: center;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

inject_sidebar_logo()

st.set_page_config(page_title="Sweep Analyzer", layout="centered")
st.title("Extended Hours Sweep Statistics")

# Instrument Lists
forex_pairs = [
    "EURUSD", "GBPUSD", "USDJPY", "USDCHF",
    "AUDUSD", "NZDUSD", "USDCAD",
    "EURJPY", "EURGBP", "GBPJPY"
]

crypto_pairs = [
    "BTCUSD", "ETHUSD", "SOLUSD",
    "LTCUSD", "XRPUSD", "BNBUSD",
    "DOGEUSD", "ADAUSD", "AVAXUSD"
]

futures_symbols = [
    "E-mini S&P 500", "E-mini NASDAQ-100", "E-mini Dow Jones 30",
    "E-mini Russell 2000", "DAX 40 Index Futures",
    "Gold Futures", "Silver Futures", "Crude Oil Futures (WTI)",
    "Natural Gas Futures", "CBOE Volatility Index (VIX)"
]

stock_symbols = [
    "AAPL", "MSFT", "AMZN", "GOOGL", "META",
    "TSLA", "NVDA", "NFLX", "AMD", "INTC",
    "JPM", "BAC", "XOM", "CVX", "BA"
]

# Select Category
CATEGORIES = ["Futures", "Forex", "Crypto", "Stocks"]
category = st.sidebar.selectbox("Select Category", CATEGORIES)

# Select Asset
if category == "Forex":
    asset = st.sidebar.selectbox("Select Pair", forex_pairs)
elif category == "Crypto":
    asset = st.sidebar.selectbox("Select Symbol", crypto_pairs)
elif category == "Futures":
    asset = st.sidebar.selectbox("Select Symbol", futures_symbols)
elif category == "Stocks":
    asset = st.sidebar.selectbox("Select Stock", stock_symbols)

# Load CSV file for asset
data_path = os.path.join("data", category.lower(), f"{asset}.csv")
if os.path.exists(data_path):
    df = pd.read_csv(data_path)
    if "DayOfWeek" not in df.columns:
        df["DayOfWeek"] = pd.to_datetime(df["Date"]).dt.day_name()

    day_options = ["All"] + sorted(df["DayOfWeek"].unique())
    day_filter = st.sidebar.selectbox("Filter by Day of Week", day_options)
    if day_filter != "All":
        df = df[df["DayOfWeek"] == day_filter]

    st.subheader(f"Results for {asset} ({category})")

    dist = df["Outcome"].value_counts(normalize=True) * 100
    chart_df = dist.reset_index()
    chart_df.columns = ["Outcome", "Percentage"]
    chart_df["Percentage"] = chart_df["Percentage"].astype(float)
    chart_df["Label"] = chart_df["Percentage"].map(lambda x: f"{x:.1f}%")

    bar_chart = alt.Chart(chart_df).mark_bar(color="#4e79a7").encode(
        x=alt.X("Outcome:N", title="Outcome"),
        y=alt.Y("Percentage:Q", title="Percentage"),
        tooltip=["Outcome", "Percentage"]
    ).properties(width=500)

    text = alt.Chart(chart_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-10,
        color='white'
    ).encode(
        x='Outcome:N',
        y='Percentage:Q',
        text='Label'
    )

    st.altair_chart(bar_chart + text, use_container_width=True)

    st.subheader("Daily Outcomes")
    st.dataframe(df)

    csv = df.to_csv(index=False).encode("utf-8")
    st.sidebar.download_button(
        "Download Filtered Data",
        data=csv,
        file_name=f"{asset}_extended_hours.csv"
    )

# Upload new file for live analysis
uploaded_file = st.file_uploader("Upload a 30-min intraday CSV file", type="csv")

def load_data(file):
    df = pd.read_csv(file, sep=";")
    df.columns = [col.strip() for col in df.columns]
    st.write("\u2705 Columns found:", df.columns.tolist())

    if "<DATE>" not in df.columns or "<TIME>" not in df.columns:
        st.error("\u274c Missing required columns: <DATE> and <TIME>")
        st.stop()

    df["Datetime"] = pd.to_datetime(df["<DATE>"] + " " + df["<TIME>"])
    df["Date"] = df["Datetime"].dt.date
    df["Time"] = df["Datetime"].dt.time
    return df

def classify_globex_sweeps(df):
    results = []
    for date, group in df.groupby("Date"):
        globex = group[(group["Time"] >= pd.to_datetime("01:00").time()) &
                       (group["Time"] <= pd.to_datetime("16:30").time())]
        us_session = group[(group["Time"] > pd.to_datetime("16:30").time()) &
                           (group["Time"] <= pd.to_datetime("23:00").time())]

        if globex.empty or us_session.empty:
            continue

        globex_high = globex["<HIGH>"].max()
        globex_low = globex["<LOW>"].min()
        session_high = us_session["<HIGH>"].max()
        session_low = us_session["<LOW>"].min()

        high_swept = session_high > globex_high
        low_swept = session_low < globex_low

        if high_swept and low_swept:
            outcome = "Both swept"
        elif high_swept:
            outcome = "High swept"
        elif low_swept:
            outcome = "Low swept"
        else:
            outcome = "None swept"

        results.append({
            "Date": date,
            "Globex High": globex_high,
            "Globex Low": globex_low,
            "High Swept": high_swept,
            "Low Swept": low_swept,
            "Outcome": outcome
        })
    return pd.DataFrame(results)

if uploaded_file:
    df = load_data(uploaded_file)
    results_df = classify_globex_sweeps(df)
    results_df["DayOfWeek"] = pd.to_datetime(results_df["Date"]).dt.day_name()

    day_filter = st.selectbox("Filter by Day of Week", ["All"] + sorted(results_df["DayOfWeek"].unique()))
    if day_filter != "All":
        filtered_df = results_df[results_df["DayOfWeek"] == day_filter]
    else:
        filtered_df = results_df

    st.success(f"\u2705 Processed {len(filtered_df)} trading days for: {day_filter if day_filter != 'All' else 'All days'}")

    st.subheader("Outcome Distribution")
    outcome_counts = filtered_df["Outcome"].value_counts(normalize=True) * 100
    chart_df = outcome_counts.reset_index()
    chart_df.columns = ["Outcome", "Percentage"]
    chart_df["Percentage"] = chart_df["Percentage"].astype(float)
    chart_df["Label"] = chart_df["Percentage"].map(lambda x: f"{x:.1f}%")

    bar_chart = alt.Chart(chart_df).mark_bar(color="#4e79a7").encode(
        x=alt.X("Outcome:N", title="Outcome"),
        y=alt.Y("Percentage:Q", title="Percentage"),
        tooltip=["Outcome", "Percentage"]
    ).properties(width=500)

    text = alt.Chart(chart_df).mark_text(
        align='center',
        baseline='bottom',
        dy=-10,
        color='white'
    ).encode(
        x='Outcome:N',
        y='Percentage:Q',
        text='Label'
    )

    st.altair_chart(bar_chart + text, use_container_width=True)

    st.subheader("Filtered Sweep Outcomes")
    st.dataframe(filtered_df)

    csv = filtered_df.to_csv(index=False).encode