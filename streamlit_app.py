import streamlit as st
import pandas as pd
import plotly.express as px
import datetime

st.set_page_config(page_title="Chelsea Bridge Dashboard", layout="wide")
st.title("🚢 Chelsea Street Bridge Lift Analytics Dashboard")

# 🔄 Load simulated prediction data
@st.cache_data
def load_predictions():
    try:
        sim_df = pd.read_csv("final_simulated_bridge_lift_dataset.csv")
        sim_df = sim_df.dropna(subset=['Lift_Duration', 'Notice_min'])
        return sim_df
    except Exception as e:
        st.error(f"❌ Error loading lift simulation data: {e}")
        return pd.DataFrame()

predictions = load_predictions()

# 📅 Show next simulated lift (sorted by notice time)
if not predictions.empty:
    next_lift = predictions.sort_values(by='Notice_min').iloc[0]
    current_time = pd.Timestamp.now()
    predicted_time = current_time + pd.to_timedelta(next_lift['Notice_min'], unit='m')

    st.markdown("### 🧭 Next Bridge Lift")
    st.info(f"""
    🚢 **Lift Type:** {next_lift.get('Lift Type', 'N/A')}  
    ⏱️ **Predicted Duration:** {round(next_lift['Lift_Duration'], 2)} minutes  
    📍 **Direction:** {next_lift.get('Direction', 'N/A')}  
    ⚓ **Vessel Count:** {next_lift.get('Vessel_Count', 'N/A')}  
    🌊 **Tide Level:** {next_lift.get('Tide_Level', 'N/A')} m  
    ☀️ **Is Daylight:** {'Yes' if next_lift.get('Is_Daylight', 0) == 1 else 'No'}  
    🕒 **Predicted Start Time:** {predicted_time.strftime('%Y-%m-%d %H:%M')}
    """)
    
    # Add download option
    top5 = predictions.sort_values(by='Notice_min').head(5)
    st.download_button("📥 Download Top 5 Predictions (CSV)", data=top5.to_csv(index=False), file_name="top5_next_lifts.csv", mime="text/csv")

else:
    st.warning("⚠️ No simulated lift data available.")

# 📦 Load actual bridge lift data
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

# Filter Data
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
st.markdown("### 📊 Historical Lift Summary")
col1, col2, col3 = st.columns(3)
col1.metric("Total Lifts", len(filtered_df))
col2.metric("Avg Duration (min)", round(filtered_df['Duration_Minutes'].mean(), 2) if len(filtered_df) > 0 else "N/A")
col3.metric("Total Lift Time (hrs)", round(filtered_df['Duration_Minutes'].sum() / 60, 2))

# Tabs for Charts
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📅 Lifts by Weekday",
    "⏱️ Duration Histogram",
    "🧭 IN vs OUT",
    "📍 ETA vs Start",
    "📈 Cumulative Duration"
])

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
        fig = px.histogram(filtered_df, x='Duration_Minutes', nbins=30, title="Lift Duration Distribution")
        st.plotly_chart(fig, use_container_width=True)

with tab3:
    if not filtered_df.empty:
        dir_counts = filtered_df['Direction'].value_counts().reset_index()
        dir_counts.columns = ['Direction', 'Count']
        fig = px.pie(dir_counts, names='Direction', values='Count', title="IN vs OUT Lifts")
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    if not filtered_df.empty:
        fig = px.scatter(filtered_df, x='ETA', y='Start_Time', color='Direction', title="ETA vs Start Time")
        st.plotly_chart(fig, use_container_width=True)

with tab5:
    if not filtered_df.empty:
        trend_data = filtered_df.groupby('Date')['Duration_Minutes'].sum().cumsum().reset_index()
        fig = px.line(trend_data, x='Date', y='Duration_Minutes', title="Cumulative Lift Duration Over Time")
        st.plotly_chart(fig, use_container_width=True)
