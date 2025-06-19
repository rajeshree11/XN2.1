import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from datetime import datetime, timedelta
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPRegressor
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_squared_error, mean_absolute_error

st.set_page_config(page_title="Chelsea Street Bridge Dashboard", layout="wide")

st.title("Chelsea Street Bridge Lift Duration Dashboard")
st.markdown("""
Welcome to the **Chelsea Street Bridge Lift Duration Dashboard**.

This dashboard explores bridge lift durations based on vessel type, tide, and weather data. It also provides a machine learning-based prediction model to estimate future lift durations.
""")

# Sidebar Filters
st.sidebar.header("🔎 Filter Options")
selected_day = st.sidebar.selectbox("Select Day of Week", options=["All"] + list(range(7)), index=0)
selected_tanker = st.sidebar.radio("Tanker Involved?", options=["All", "Yes", "No"], index=0)

# Load and clean bridge log data
bridge_df = pd.read_excel("Chelsea Bridge Data Points_03272025.xlsx", sheet_name="Data", header=3)
bridge_df = bridge_df[["ETA Bridge", "Start Time", "End Time", "Duration", "Vessel(s)", "Direction"]].dropna()
bridge_df["ETA Bridge"] = pd.to_datetime(bridge_df["ETA Bridge"])
bridge_df["Start Time"] = pd.to_datetime(bridge_df["Start Time"])
bridge_df["End Time"] = pd.to_datetime(bridge_df["End Time"])

# Safely convert Duration to timedelta
bridge_df = bridge_df[bridge_df["Duration"].notna()].copy()
bridge_df["Duration"] = bridge_df["Duration"].astype(str).str.strip()
bridge_df["Duration"] = pd.to_timedelta(bridge_df["Duration"], errors='coerce')
bridge_df["Lift_Duration_Minutes"] = bridge_df["Duration"].dt.total_seconds() / 60
bridge_df.drop(columns=["Duration"], inplace=True)
bridge_df.dropna(subset=["Lift_Duration_Minutes"], inplace=True)

# Feature engineering
bridge_df["Day_of_Week"] = bridge_df["ETA Bridge"].dt.dayofweek
bridge_df["time_of_day"] = pd.cut(bridge_df["ETA Bridge"].dt.hour, bins=[0, 6, 12, 18, 24], labels=[1, 2, 3, 4], right=False).astype(int)
bridge_df["Start_Minutes"] = bridge_df["Start Time"].dt.hour * 60 + bridge_df["Start Time"].dt.minute
bridge_df["End_Minutes"] = bridge_df["End Time"].dt.hour * 60 + bridge_df["End Time"].dt.minute
bridge_df["Vessel_Count"] = bridge_df["Vessel(s)"].astype(str).apply(lambda x: len(x.split(",")))
bridge_df["Has_Barge"] = bridge_df["Vessel(s)"].str.contains("Barge", case=False, na=False).astype(int)
bridge_df["Has_Tanker"] = bridge_df["Vessel(s)"].str.contains("Tanker", case=False, na=False).astype(int)
bridge_df["Hour"] = bridge_df["ETA Bridge"].dt.hour
bridge_df["Is_Daylight"] = bridge_df["Hour"].between(6, 20).astype(int)

# Simulated weather and tide data
np.random.seed(42)
bridge_df["temperature_C"] = np.random.normal(18, 5, size=len(bridge_df))
bridge_df["precipitation_mm"] = np.random.uniform(0, 1, size=len(bridge_df))
bridge_df["windspeed_mph"] = np.random.normal(10, 3, size=len(bridge_df))
bridge_df["tide_ft"]
