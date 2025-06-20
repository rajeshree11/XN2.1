import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Chelsea Bridge Dashboard", layout="wide")
st.title("🚢 Chelsea Street Bridge Lift Analytics Dashboard")


@st.cache_data
def load_predictions():
    try:
        pred_df = pd.read_csv("final_simulated_bridge_lift_dataset.csv")
        pred_df['ETA'] = pd.to_datetime(pred_df['ETA'], errors='coerce')
        pred_df = pred_df.dropna(subset=['ETA', 'Lift_Duration'])
        return pred_df
    except Exception as e:
        st.error(f"❌ Error loading simulated lift data: {e}")
        return pd.DataFrame()

predictions = load_predictions()

# Show next lift from simulated data
if not predictions.empty:
    upcoming = predictions[predictions['ETA'] > pd.Timestamp.now()].sort_values(by='ETA')
    if not upcoming.empty:
        next_lift = upcoming.iloc[0]
        st.markdown("### 📅 Next Scheduled Simulated Lift")
        st.info(f"""
        🛥️ **ETA:** {next_lift['ETA'].strftime('%Y-%m-%d %H:%M')}  
        ⏱️ **Predicted Duration:** {round(next_lift['Lift_Duration'], 2)} minutes  
        📍 **Direction:** {next_lift.get('Direction', 'N/A')}  
        🚢 **Vessel Type:** {next_lift.get('Vessel', 'N/A')}
        """)
    else:
        st.success("✅ No future lifts currently scheduled.")


# 📦 Load core bridge data
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

    df['Duration'] = df['Duration'].astype(str)
    df['Duration_Minutes'] = pd.to_timedelta(df['Duration'], errors='coerce').dt.total_seconds() / 60

    df = df.dropna(subset=['Start_Time', 'Duration_Minutes', 'Direction', 'ETA'])

    df['Hour'] = df['Start_Time'].dt.hour
    df['Weekday'] = df['Start_Time'].dt.day_name()
    df['Date'] = df['Start_Time'].dt.date

    return df

df = load_data()

# Sidebar Filters
st.sidebar.header("🔎 Filter Options")
directions = st.sidebar.multiselect("Select Direction", df['Direction'].unique(), default=df['Direction'].unique())

min_date = df['Start_Time'].min()
max_date = df['Start_Time'].max()
default_range = [min_date.date(), max_date.date()] if pd.notnull(min_date) else [datetime.date.today(), datetime.date.today()]
date_range = st.sidebar.date_input("Select Date Range", default_range)

vessel_search = st.sidebar.text_input("Search Vessel (optional)", "")

min_dur = int(df['Duration_Minutes'].min()) if not df.empty else 0
max_dur = int(df['Duration_Minutes'].max()) if not df.empty else 60
duration_range = st.sidebar.slider("Select Duration Range (Minutes)", min_dur, max_dur, (min_dur, max_dur))

# Filter data
filtered_df = df[
    (df['Direction'].isin(directions)) &
    (df['Start_Time'].dt.date >= date_range[0]) &
    (df['Start_Time'].dt.date <= date_range[1]) &
    (df['Duration_Minutes'] >= duration_range[0]) &
    (df['Duration_Minutes'] <= duration_range[1])
]

if vessel_search:
    filtered_df = filtered_df[filtered_df['Vessel'].str.contains(vessel_search, case=False, na=False)]

# KPIs
st.markdown("### 📊 Summary Metrics")
col1, col2, col3 = st.columns(3)
col1.metric("Total Lifts", len(filtered_df))
col2.metric("Avg Duration (min)", round(filtered_df['Duration_Minutes'].mean(), 2) if len(filtered_df) > 0 else "N/A")
col3.metric("Total Lift Time (hrs)", round(filtered_df['Duration_Minutes'].sum() / 60, 2))

# Tabs for Visualization
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📅 Lifts by Weekday", "⏱️ Duration Histogram", "🧭 IN vs OUT", "📍 ETA vs Start", "📈 Cumulative Duration"])

with tab1:
    if not filtered_df.empty:
        weekday_counts = filtered_df['Weekday'].value_counts().reindex(
            ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        ).fillna(0).reset_index()
        weekday_counts.columns = ['Weekday', 'Lift Count']
        fig = px.bar(weekday_counts, x='Weekday', y='Lift Count', text='Lift Count')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available for selected filters.")

with tab2:
    if not filtered_df.empty:
        fig = px.histogram(filtered_df, x='Duration_Minutes', nbins=30)
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not filtered_df.empty:
        dir_counts = filtered_df['Direction'].value_counts().reset_index()
        dir_counts.columns = ['Direction', 'Count']
        fig = px.pie(dir_counts, names='Direction', values='Count')
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    if not filtered_df.empty:
        fig = px.scatter(filtered_df, x='ETA', y='Start_Time', color='Direction')
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    if not filtered_df.empty:
        trend_data = filtered_df.groupby('Date')['Duration_Minutes'].sum().cumsum().reset_index()
        fig = px.line(trend_data, x='Date', y='Duration_Minutes')
        st.plotly_chart(fig, use_container_width=True)
