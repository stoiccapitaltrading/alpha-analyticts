import streamlit as st
import pandas as pd

st.set_page_config(page_title="Market Analytics Dashboard", layout="wide")

# --- Sidebar Navigation ---
st.sidebar.title("📊 Menu")
page = st.sidebar.radio(
    "Go to",
    ["Extended Hours Sweep", "Opening Range Stats", "Other Analysis"]
)

# --- Shared Loader ---
@st.cache_data
def load_data(file):
    df = pd.read_csv(file, sep=";")
    df.columns = [c.strip() for c in df.columns]
    df["Datetime"] = pd.to_datetime(df["<DATE>"] + " " + df["<TIME>"])
    df["Date"] = df["Datetime"].dt.date
    df["Time"] = df["Datetime"].dt.time
    return df

# --- Page 1: Extended Hours Sweep Analyzer ---
def page_extended_sweep():
    st.header("📈 Extended Trading Hours Sweep Analyzer")
    uploaded_file = st.file_uploader("Upload 30-min CSV (Globex → RTH)", type="csv")
    if not uploaded_file:
        st.info("Please upload a CSV to begin.")
        return

    df = load_data(uploaded_file)

    # classify_globex_sweeps code from before...
    def classify_globex_sweeps(df):
        results = []
        for date, group in df.groupby("Date"):
            globex = group[(group["Time"] >= pd.to_datetime("01:00").time()) &
                           (group["Time"] <= pd.to_datetime("16:30").time())]
            us_sess = group[(group["Time"] > pd.to_datetime("16:30").time()) &
                            (group["Time"] <= pd.to_datetime("23:00").time())]
            if globex.empty or us_sess.empty: continue
            gh, gl = globex["<HIGH>"].max(), globex["<LOW>"].min()
            sh, sl = us_sess["<HIGH>"].max(), us_sess["<LOW>"].min()
            high_swept = sh > gh; low_swept = sl < gl
            if high_swept and low_swept: outcome = "Both swept"
            elif high_swept: outcome = "High swept"
            elif low_swept: outcome = "Low swept"
            else: outcome = "None swept"
            results.append({
                "Date": date, "High Swept": high_swept, "Low Swept": low_swept,
                "Outcome": outcome
            })
        return pd.DataFrame(results)

    res = classify_globex_sweeps(df)
    res["DayOfWeek"] = pd.to_datetime(res["Date"]).dt.day_name()

    # Day-of-week filter
    dow = st.selectbox("Filter by Day of Week", ["All"] + sorted(res["DayOfWeek"].unique()))
    if dow != "All":
        res = res[res["DayOfWeek"] == dow]

    st.subheader("Outcome Distribution")
    st.bar_chart(res["Outcome"].value_counts(normalize=True) * 100)

    st.subheader("Daily Results")
    st.dataframe(res)

    csv = res.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Download", data=csv, file_name="extended_sweep.csv")

# --- Page 2: Opening Range Statistics ---
def page_opening_range():
    st.header("⏰ Opening Range Analyzer")
    uploaded_file = st.file_uploader("Upload 30-min CSV (RTH OR)", type="csv", key="or")
    if not uploaded_file:
        st.info("Upload CSV to compute Opening Range stats.")
        return

    df = load_data(uploaded_file)

    # Example: OR from 16:30–17:30
    start, end = pd.to_datetime("16:30").time(), pd.to_datetime("17:30").time()
    results = []
    for date, grp in df.groupby("Date"):
        or_data = grp[(grp["Time"] >= start) & (grp["Time"] <= end)]
        post = grp[(grp["Time"] > end) & (grp["Time"] <= pd.to_datetime("23:00").time())]
        if or_data.empty or post.empty: continue
        or_h, or_l = or_data["<HIGH>"].max(), or_data["<LOW>"].min()
        h_swept = (post["<HIGH>"] > or_h).any()
        l_swept = (post["<LOW>"] < or_l).any()
        if h_swept and l_swept: outcome = "Both swept"
        elif h_swept: outcome = "High swept"
        elif l_swept: outcome = "Low swept"
        else: outcome = "None swept"
        results.append({"Date": date, "Outcome": outcome})
    or_df = pd.DataFrame(results)

    st.subheader("OR Outcome Distribution")
    st.bar_chart(or_df["Outcome"].value_counts(normalize=True) * 100)
    st.subheader("OR Daily Outcomes")
    st.dataframe(or_df)

# --- Page 3: Other Analysis Placeholder ---
def page_other():
    st.header("🔧 Other Analysis")
    st.write("Add your other pages here (volatility, range stats, etc.).")

# --- Router ---
if page == "Extended Hours Sweep":
    page_extended_sweep()
elif page == "Opening Range Stats":
    page_opening_range()
else:
    page_other()
