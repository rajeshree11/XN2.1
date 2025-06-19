import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Chelsea Bridge Custom Dashboard", layout="wide")

st.title("🚢 Chelsea Street Bridge Lift Analytics Dashboard")

@st.cache_data
def load_data():
    # Load Excel and skip first 3 metadata rows
    df = pd.read_excel("Chelsea Bridge Data Points_03272025.xlsx", sheet_name="Data", skiprows=3)

    # Rename columns for clarity
    df = df.rename(columns={
        'ETA Bridge': 'ETA',
        'Start Time': 'Start_Time',
        'End Time': 'End_Time',
        'Duration': 'Duration',
        'Vessel(s)': 'Vessel',
        'Direction': 'Direction'
    })

    # Convert date/time fields
    df['ETA'] = pd.to_datetime(df['ETA'], errors='coerce')
    df['Start_Time'] = pd.to_datetime(df['Start_Time'], errors='coerce')
    df['End_Time'] = pd.to_datetime(df['End_Time'], errors='coerce')

    # Clean duration: Only keep valid hh:mm:ss formats
    df = df[df['Duration'].apply(lambda x: isinstance(x, str) and ':' in x)]
    df['Duration_Minutes'] = pd.to_timedelta(df['Duration'], errors='coerce').dt.total_seconds() / 60

    # Remove incomplete rows
    df = df.dropna(subset=['Start_Time', 'Duration_Minutes', 'Direction', 'ETA'])

    # Add time-based columns
    df['Hour'] = df['Start_Time'].dt.hour
    df['Weekday'] = df['Start_Time'].dt.day_name()
    df['Date'] = df['Start_Time'].dt.date

    return df

# Load and filter data
df = load_data()

st.sidebar.header("🔎 Filter Options")
directions = st.sidebar.multiselect("Select Direction", df['Direction'].unique(), default=df['Direction'].unique())
date_range = st.sidebar.date_input("Select Date Range", [df['Start_Time'].min().date(), df['Start_Time'].max().date()])

filtered_df = df[
    (df['Direction'].isin(directions)) &
    (df['Start_Time'].dt.date >= date_range[0]) &
    (df['Start_Time'].dt.date <= date_range[1])
]

# KPIs
st.markdown("### 📊 Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Lifts", len(filtered_df))
col2.metric("Average Duration (min)", round(filtered_df['Duration_Minutes'].mean(), 2))
col3.metric("Total Lift Time (hrs)", round(filtered_df['Duration_Minutes'].sum() / 60, 2))

# Chart 1: Heatmap of Lifts by Hour and Day
st.markdown("### 🔥 Heatmap: Lifts by Hour & Weekday")
heatmap_data = filtered_df.groupby(['Weekday', 'Hour']).size().unstack().fillna(0)
heatmap_data = heatmap_data.reindex(['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'])
fig1 = px.imshow(heatmap_data, labels=dict(x="Hour", y="Weekday", color="Lift Count"), color_continuous_scale='Blues')
st.plotly_chart(fig1, use_container_width=True)

# Chart 2: Histogram of Duration
st.markdown("### ⏱️ Histogram: Lift Duration Distribution")
fig2 = px.histogram(filtered_df, x='Duration_Minutes', nbins=30, labels={'Duration_Minutes': 'Minutes'})
st.plotly_chart(fig2, use_container_width=True)

# Chart 3: Pie Chart of Directions
st.markdown("### 🧭 Pie Chart: IN vs OUT Lifts")
dir_counts = filtered_df['Direction'].value_counts().reset_index()
fig3 = px.pie(dir_counts, names='index', values='Direction', title="Lift Direction Distribution")
st.plotly_chart(fig3, use_container_width=True)

# Chart 4: Scatter – ETA vs Start Time
st.markdown("### 📍 Scatter Plot: ETA vs Start Time")
fig4 = px.scatter(filtered_df, x='ETA', y='Start_Time', color='Direction',
                  title='ETA vs Actual Start Time')
st.plotly_chart(fig4, use_container_width=True)

# Chart 5: Cumulative Duration Over Time
st.markdown("### 📈 Trend: Cumulative Lift Duration (min)")
trend_data = filtered_df.groupby('Date')['Duration_Minutes'].sum().cumsum().reset_index()
fig5 = px.line(trend_data, x='Date', y='Duration_Minutes',
               labels={'Duration_Minutes': 'Cumulative Minutes'})
st.plotly_chart(fig5, use_container_width=True)

# Final Table
st.markdown("### 📋 Filtered Lift Data")
st.dataframe(filtered_df)
