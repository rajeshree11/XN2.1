import streamlit as st
import pandas as pd
import plotly.express as px
import os

st.set_page_config(page_title="Chelsea Bridge Dashboard", layout="wide")

st.title("🚢 Chelsea Street Bridge Dashboard")

# Load all required data
@st.cache_data
def load_data():
    data = {}

    if os.path.exists("Chelsea Bridge Data Points_03272025.xlsx"):
        data['operations'] = pd.read_excel("Chelsea Bridge Data Points_03272025.xlsx", sheet_name="Data", skiprows=3)
    else:
        st.warning("Missing file: Chelsea Bridge Data Points_03272025.xlsx")

    if os.path.exists("chelsea_street_bridge_traffic.xlsx"):
        data['traffic'] = pd.read_excel("chelsea_street_bridge_traffic.xlsx")
    else:
        st.warning("Missing file: chelsea_street_bridge_traffic.xlsx")

    if os.path.exists("final_predictions_output.csv"):
        data['predictions'] = pd.read_csv("final_predictions_output.csv")
    else:
        st.warning("Missing file: final_predictions_output.csv")

    if os.path.exists("final_simulated_bridge_lift_dataset.csv"):
        data['simulation'] = pd.read_csv("final_simulated_bridge_lift_dataset.csv")
    else:
        st.warning("Missing file: final_simulated_bridge_lift_dataset.csv")

    if os.path.exists("Tide_Predictions.xlsx"):
        data['tide'] = pd.read_excel("Tide_Predictions.xlsx")
    else:
        st.warning("Missing file: Tide_Predictions.xlsx")

    return data

data = load_data()

# Preprocess operations data
if 'operations' in data:
    ops_df = data['operations'].rename(columns={
        'ETA Bridge': 'ETA',
        'Start Time': 'Start_Time',
        'End Time': 'End_Time',
        'Duration': 'Duration',
        'Vessel(s)': 'Vessel',
        'Direction': 'Direction'
    })

    ops_df['Start_Time'] = pd.to_datetime(ops_df['Start_Time'], errors='coerce')
    ops_df['Duration'] = pd.to_timedelta(ops_df['Duration'].astype(str), errors='coerce')
    ops_df['Duration_Minutes'] = ops_df['Duration'].dt.total_seconds() / 60
    ops_df = ops_df.dropna(subset=['Start_Time', 'Duration_Minutes'])
else:
    ops_df = pd.DataFrame()

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Operations", 
    "🚗 Traffic", 
    "📈 Predictions", 
    "🌦️ Environment", 
    "🌊 Tide & Weather"
])

# --- Tab 1: Operations ---
with tab1:
    st.subheader("Bridge Lift Operations Overview")
    if not ops_df.empty:
        col1, col2 = st.columns(2)
        col1.metric("Total Lifts", len(ops_df))
        col2.metric("Avg Duration (min)", round(ops_df['Duration_Minutes'].mean(), 2))

        fig = px.histogram(ops_df, x='Duration_Minutes', nbins=30, title="Lift Duration Distribution")
        st.plotly_chart(fig, use_container_width=True)

        if 'Vessel' in ops_df.columns:
            top_vessels = ops_df['Vessel'].value_counts().nlargest(5).reset_index()
            top_vessels.columns = ['Vessel', 'Count']
            fig = px.bar(top_vessels, x='Vessel', y='Count', title="Top 5 Vessels")
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Bridge lift data not loaded.")

# --- Tab 2: Traffic ---
with tab2:
    st.subheader("Traffic Volume Over Time")
    if 'traffic' in data:
        traffic_df = data['traffic']
        traffic_df['date'] = pd.to_datetime(traffic_df['date'])
        fig = px.line(traffic_df, x='date', y='vehicles', title="Daily Vehicle Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Traffic data not loaded.")

# --- Tab 3: Predictions ---
with tab3:
    st.subheader("Lift Duration Prediction Accuracy")
    if 'predictions' in data:
        pred_df = data['predictions']
        fig = px.scatter(pred_df, x='Actual_Lift_Duration', y='Predicted_Lift_Duration',
                         color='Within_5_Minutes', title="Actual vs Predicted Duration")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Prediction data not loaded.")

# --- Tab 4: Environment ---
with tab4:
    st.subheader("Environmental Impact on Lift Duration")
    if 'simulation' in data:
        sim_df = data['simulation']
        fig = px.scatter(sim_df, x='Max_Temp', y='Lift_Duration', color='Direction', title="Duration vs Temperature")
        st.plotly_chart(fig, use_container_width=True)

        fig = px.box(sim_df, x='Is_Weekend', y='Lift_Duration', title="Weekend vs Weekday Lift Duration")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Simulation data not loaded.")

# --- Tab 5: Tide & Weather ---
with tab5:
    st.subheader("Tide Predictions")
    if 'tide' in data:
        tide_df = data['tide']

        if 'Date' in tide_df.columns and 'Time (LST/LDT)' in tide_df.columns:
            tide_df = tide_df.dropna(subset=['Date', 'Time (LST/LDT)'])
            tide_df['Datetime'] = pd.to_datetime(
                tide_df['Date'].astype(str) + " " + tide_df['Time (LST/LDT)'].astype(str),
                errors='coerce'
            )
            tide_df = tide_df.dropna(subset=['Datetime'])

            fig = px.line(
                tide_df, 
                x='Datetime', 
                y='Predicted (ft)', 
                color='High/Low', 
                title="Tide Levels Over Time"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Expected columns 'Date' and 'Time (LST/LDT)' not found in tide data.")
    else:
        st.info("Tide data not loaded.")
