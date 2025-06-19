import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Chelsea Street Bridge Dashboard", layout="wide")

# Title
st.title("🚢 Chelsea Street Bridge Lift Dashboard")

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

    df = df.dropna(subset=['Start_Time', 'End_Time', 'Duration_Minutes', 'Direction', 'Vessel'])

    df['Date'] = df['Start_Time'].dt.date
    return df

df = load_data()

# Sidebar
st.sidebar.header("🔎 Filter Options")
directions = st.sidebar.multiselect("Direction", options=df['Direction'].unique(), default=df['Direction'].unique())
vessels = st.sidebar.multiselect("Vessel", options=df['Vessel'].unique(), default=df['Vessel'].unique())
date_range = st.sidebar.date_input("Date Range", [df['Start_Time'].min().date(), df['Start_Time'].max().date()])

# Filter data
filtered_df = df[
    (df['Direction'].isin(directions)) &
    (df['Vessel'].isin(vessels)) &
    (df['Start_Time'].dt.date >= date_range[0]) &
    (df['Start_Time'].dt.date <= date_range[1])
]

# Metrics
st.markdown("### 📈 Key Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Lifts", len(filtered_df))
col2.metric("Avg Duration (min)", round(filtered_df['Duration_Minutes'].mean(), 2))
col3.metric("Date Range", f"{date_range[0]} to {date_range[1]}")

# Charts
st.markdown("### ⏱️ Average Lift Duration by Vessel")
fig1 = px.bar(filtered_df.groupby('Vessel')['Duration_Minutes'].mean().reset_index(),
              x='Vessel', y='Duration_Minutes',
              labels={'Duration_Minutes': 'Avg Duration (min)'})
st.plotly_chart(fig1, use_container_width=True)

st.markdown("### 📅 Daily Lift Counts")
fig2 = px.line(filtered_df.groupby('Date').size().reset_index(name='Lifts'),
               x='Date', y='Lifts')
st.plotly_chart(fig2, use_container_width=True)

st.markdown("### 📦 Lift Duration Distribution by Direction")
fig3 = px.box(filtered_df, x='Direction', y='Duration_Minutes',
              labels={'Duration_Minutes': 'Lift Duration (min)'})
st.plotly_chart(fig3, use_container_width=True)

# Data Table
st.markdown("### 🧾 Filtered Data Table")
st.dataframe(filtered_df)

