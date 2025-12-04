import streamlit as st
import pandas as pd
import altair as alt

st.set_page_config(layout="wide", page_title="CT Affordability Dashboard")
st.title("Connecticut Affordability Dashboard (2020–2024)")

df = pd.read_csv("data/cleaned_ct_data.csv")
df["Year"] = df["Year"].astype(int)

st.sidebar.header("Controls")
year_min, year_max = int(df.Year.min()), int(df.Year.max())
selected_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))
show_afford_ratio = st.sidebar.checkbox("Show affordability ratio", True)
show_raw = st.sidebar.checkbox("Show raw data", False)
smoothing = st.sidebar.selectbox("Rolling window (years)", [1,2,3], index=0)

df = df[(df["Year"] >= selected_range[0]) & (df["Year"] <= selected_range[1])]

if show_raw:
    st.subheader("Raw data")
    st.write(df)

df["Affordability"] = df["HomePriceIndex"] / df["MedianIncome"]

if smoothing > 1:
    df["MedianIncome_roll"] = df["MedianIncome"].rolling(smoothing).mean()
    df["HomePriceIndex_roll"] = df["HomePriceIndex"].rolling(smoothing).mean()
    df["Affordability_roll"] = df["Affordability"].rolling(smoothing).mean()
else:
    df["MedianIncome_roll"] = df["MedianIncome"]
    df["HomePriceIndex_roll"] = df["HomePriceIndex"]
    df["Affordability_roll"] = df["Affordability"]

st.subheader("Median Income Over Time")
st.altair_chart(alt.Chart(df).mark_line(point=True).encode(x="Year:O", y="MedianIncome_roll:Q", tooltip=["Year","MedianIncome"]).properties(height=300), use_container_width=True)

st.subheader("CT House Price Index")
st.altair_chart(alt.Chart(df).mark_line(point=True).encode(x="Year:O", y="HomePriceIndex_roll:Q", tooltip=["Year","HomePriceIndex"]).properties(height=300), use_container_width=True)

st.subheader("Income vs Home Price Index (Normalized)")
df2 = df.copy()
df2["MedianIncome_norm"] = (df2["MedianIncome_roll"] - df2["MedianIncome_roll"].min()) / (df2["MedianIncome_roll"].max() - df2["MedianIncome_roll"].min()) * 100
df2["HomePriceIndex_norm"] = (df2["HomePriceIndex_roll"] - df2["HomePriceIndex_roll"].min()) / (df2["HomePriceIndex_roll"].max() - df2["HomePriceIndex_roll"].min()) * 100
df3 = df2.melt(id_vars=["Year"], value_vars=["MedianIncome_norm","HomePriceIndex_norm"], var_name="Metric", value_name="Value")
st.altair_chart(alt.Chart(df3).mark_line(point=True).encode(x="Year:O", y="Value:Q", color="Metric:N", tooltip=["Year","Metric","Value"]).properties(height=350), use_container_width=True)

st.subheader("Quarter-over-Quarter & Year-over-Year Changes")
cols = []
if "Income_QoQ" in df.columns:
    cols.append(alt.Chart(df).mark_bar().encode(x="Year:O", y="Income_QoQ:Q"))
if "Home_QoQ" in df.columns:
    cols.append(alt.Chart(df).mark_bar().encode(x="Year:O", y="Home_QoQ:Q"))
if cols:
    st.altair_chart(alt.hconcat(*cols).resolve_scale(y='independent'), use_container_width=True)

st.subheader("Median Income vs Home Price Index")
st.altair_chart(alt.Chart(df).mark_circle(size=80).encode(x="MedianIncome:Q", y="HomePriceIndex:Q", color="Year:O", tooltip=["Year","MedianIncome","HomePriceIndex"]).interactive().properties(height=350), use_container_width=True)

if show_afford_ratio:
    st.subheader("Affordability Ratio (HPI / Income)")
    st.altair_chart(alt.Chart(df).mark_line(point=True).encode(x="Year:O", y="Affordability_roll:Q", tooltip=["Year","Affordability"]).properties(height=300), use_container_width=True)

st.subheader("Largest Yearly Jumps")
if "Home_YoY" in df.columns:
    largest_home = df.loc[df["Home_YoY"].idxmax()]
    st.write("Year with largest Home YoY increase:", int(largest_home["Year"]), f"{largest_home['Home_YoY']:.2%}")
if "Income_YoY" in df.columns:
    largest_income = df.loc[df["Income_YoY"].idxmax()]
    st.write("Year with largest Income YoY increase:", int(largest_income["Year"]), f"{largest_income['Income_YoY']:.2%}")

st.subheader("Inflation-Adjusted Median Income")
inflation_rate = 0.03
df["Income_Real"] = df["MedianIncome"] / ((1+inflation_rate)**(df["Year"]-2020))
st.altair_chart(alt.Chart(df).mark_line(point=True).encode(x="Year:O", y=alt.Y("Income_Real:Q", scale=alt.Scale(domain=[40000, df["Income_Real"].max()])), tooltip=["Year","Income_Real"]).properties(height=300), use_container_width=True)
