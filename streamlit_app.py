import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
import datetime
import os
import io

from vega_datasets import data

@st.cache_data
def convert_for_download(df):
    return df.to_csv().encode("utf-8")

def format_size(size_in_bytes):
    units = ["B", "KB", "MB", "GB", "TB"]
    size = size_in_bytes
    unit = 0
    while size > 1024 and unit < len(units) - 1:
        size /= 1024
        unit += 1
    return f"{size:.2f} {units[unit]}"

source = data.seattle_weather()

scale = alt.Scale(
    domain=["sun", "fog", "drizzle", "rain", "snow"],
    range=["#e7ba52", "#a7a7a7", "#aec7e8", "#1f77b4", "#9467bd"],
)
color = alt.Color("weather:N", scale=scale)

st.title("📅 Weather@Seattle")

col1, col2, col3 = st.columns(3)

# multiselection
with col1:
    options = ["sun", "fog", "drizzle", "rain", "snow"]
    selection = st.segmented_control(
        "Weather", options, selection_mode="multi", default=options
    )
    st.markdown(f"Selected options: {selection}")

df = source[source["weather"].isin(selection)]

# date input calender
with col2:
    start = st.date_input(
        "Start date",
        value=df["date"].min().date(),
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),    
    )

with col3:
    end = st.date_input(
        "End date",
        value=df["date"].max().date(),  
        min_value=df["date"].min().date(),
        max_value=df["date"].max().date(),      
    )

date_range = st.date_input(
    "Datetime range",
    value=(start, end),
    disabled=True,
)

start_date, end_date = pd.to_datetime(date_range)
filtered_df = df[df["date"].between(start_date, end_date)]

st.scatter_chart(
    data=filtered_df,
    x='date',
    y='temp_max',
)

# We create two selections:
# - a brush that is active on the top panel
# - a multi-click that is active on the bottom panel
brush = alt.selection_interval(encodings=["x"])
click = alt.selection_multi(encodings=["color"])

# Top panel is scatter plot of temperature vs time
points = (
    alt.Chart()
    .mark_point()
    .encode(
        alt.X("monthdate(date):T", title="Date"),
        alt.Y(
            "temp_max:Q",
            title="Maximum Daily Temperature (C)",
            scale=alt.Scale(domain=[-5, 40]),
        ),
        color=alt.condition(brush, color, alt.value("lightgray")),
        size=alt.Size("precipitation:Q", scale=alt.Scale(range=[5, 200])),
    )
    .properties(width=550, height=300)
    .add_selection(brush)
    .transform_filter(click)
)

# Bottom panel is a bar chart of weather type
bars = (
    alt.Chart()
    .mark_bar()
    .encode(
        x="count()",
        y="weather:N",
        color=alt.condition(click, color, alt.value("lightgray")),
    )
    .transform_filter(brush)
    .properties(
        width=550,
    )
    .add_selection(click)
)

chart = alt.vconcat(points, bars, data=filtered_df, title="Seattle Weather: 2012-2015")

tab1, tab2 = st.tabs(["Streamlit theme (default)", "Altair native theme"])

with tab1:
    st.altair_chart(chart, theme="streamlit", use_container_width=True)
with tab2:
    st.altair_chart(chart, theme=None, use_container_width=True)

# Error Bars with Standard Deviation
error_bars = alt.Chart(filtered_df).mark_errorbar(extent='stdev').encode(
  x=alt.X('temp_max').scale(zero=False),
  y=alt.Y('weather'),
)

points = alt.Chart(filtered_df).mark_point(filled=True).encode(
  x=alt.X('mean(temp_max)'),
  y=alt.Y('weather'),
)

error_bars + points

# summary
st.subheader("Summary")
col1, col2 = st.columns(2)
with col1:
    st.write("source data")
    st.write(source.describe())
with col2:
    st.write("filtered data")
    st.write(filtered_df.describe())

source_csv = convert_for_download(source)
filtered_csv = convert_for_download(filtered_df)

# table
st.subheader("Table")
col1, col2 = st.columns(2)
with col1:
    st.write("source data")

    buffer = io.StringIO()
    source.to_csv(buffer, index=False)
    csv_size_bytes = buffer.tell()
    formatted_size = format_size(csv_size_bytes)
    st.write(f"Estimated CSV size: {formatted_size}")

    source
    st.download_button(
    label="Download source data as CSV",
    data=source_csv,
    file_name="source_data.csv",
    mime="text/csv",
    icon=":material/download:",
)

with col2:
    st.write("filtered data")

    buffer = io.StringIO()
    filtered_df.to_csv(buffer, index=False)
    csv_size_bytes = buffer.tell()
    formatted_size = format_size(csv_size_bytes)
    st.write(f"Estimated CSV size: {formatted_size}")

    filtered_df
    st.download_button(
    label="Download filtered data as CSV",
    data=filtered_csv,
    file_name="filtered_data.csv",
    mime="text/csv",
    icon=":material/download:",
)