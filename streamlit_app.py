import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

st.set_page_config(page_title="Chelsea Bridge Custom Dashboard", layout="wide")

st.title("🚢 Chelsea Street Bridge Lift Analytics Dashboard")

@st.cache_data
def load_data():
    df = pd.read_excel("Chelsea Bridge Data Points_03272025.xlsx", sheet_name="Data", skiprows=3)

    df = df.rename(columns={
        'ETA Bridge': 'ETA',
        'Start Time': 'Start_Time',
        'End Time': 'End_Time',
        'Duration': 'Duration',
        'Vessel(s)': 'Vessel',
        'Direction': 'Direction'
    })

    df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce')
    df['Start_Time'] = pd.to_datetime(df['Start_Time'], errors='coerce')
    df['End_Time'] = pd.to_datetime(df['End_Time'], errors='coerce')
    df['Duration_Minutes'] = pd.to_timedelta(df['Duration'], errors='coerce').dt.total_seconds() / 60

    df = df.dropna(subset=['Start_Time', 'Duration_Minutes', 'Direction', 'ETA'])

    df['Hour'] = df['Start_Time'].dt.hour
    df['Weekday'] = df['Start_Time'].dt.day_name()
    df['Date'] = df['Start_Time'].dt.date

    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("🔎 Filter Options")
directions = st.sidebar.multiselect("Direction", df['Direction'].unique(), default=df['Direction'].unique())
date_range = st.sidebar.date_input("Date Range", [df['Start_Time'].min().date(), df['Start_Time'].max().date()])

# Apply filters
filtered_df = df[
    (df['Direction'].isin(directions)) &
    (df['Start_Time'].dt.date >= date_range[0]) &
    (df['Start_Time'].dt.date <= date_range[1])
]

# KPIs
st.markdown("### 📊 Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Lifts", len(filtered_df))
col2.metric("Avg Duration (min)", round(filtered_df['Duration_Minutes'].mean(), 2))
col3.metric("Date Range", f"{date_range[0]} to {date_range[1]}")

# Chart 1: Heatmap of Lifts by Hour and Day
st.markdown("### 🔥 Lift Frequency Heatmap (Hour vs Weekday)")
heatmap_data = filtered_df.groupby(['Weekday', 'Hour']).size().unstack().fillna(0)
heatmap_data = heatmap_data.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
fig1 = px.imshow(heatmap_data, aspect="auto", color_continuous_scale='Blues',
                 labels=dict(x="Hour of Day", y="Weekday", color="Lift Count"))
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Histogram of Lift Duration
st.markdown("### ⏱️ Histogram of Lift Durations")
fig2 = px.histogram(filtered_df, x='Duration_Minutes', nbins=30,
                    labels={'Duration_Minutes': 'Lift Duration (minutes)'})
st.plotly_chart(fig2, use_container_width=True)

# Chart 3: Pie Chart of Lift Directions
st.markdown("### 🧭 Direction Distribution")
dir_counts = filtered_df['Direction'].value_counts().reset_index()
fig3 = px.pie(dir_counts, names='index', values='Direction', title='IN vs OUT Lifts',
              labels={'index': 'Direction', 'Direction': 'Count'})
st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Scatter Plot – ETA vs Actual Start
st.markdown("### 📍 ETA vs Actual Start Time")
fig4 = px.scatter(filtered_df, x='ETA', y='Start_Time', color='Direction',
                  title='ETA vs Start Time by Direction')
st.plotly_chart(fig4, use_container_width=True)

# Chart 5: Cumulative Lift Duration Over Time
st.markdown("### 📈 Total Bridge Lift Time Over Time")
cum_data = filtered_df.groupby('Date')['Duration_Minutes'].sum().cumsum().reset_index()
fig5 = px.line(cum_data, x='Date', y='Duration_Minutes',
               labels={'Duration_Minutes': 'Cumulative Duration (min)'})
st.plotly_chart(fig5, use_container_width=True)

# Final Data Table
st.markdown("### 📋 Filtered Data Table")
st.dataframe(filtered_df)
