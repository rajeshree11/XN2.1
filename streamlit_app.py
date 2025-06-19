import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import requests
from datetime import datetime
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

**Sponsor Use Case:** This tool enables data-driven decision-making for bridge operations, marine logistics, and public transit optimization.
""")

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
bridge_df["tide_ft"] = np.random.uniform(0, 10, size=len(bridge_df))
bridge_df["TAVG"] = bridge_df["temperature_C"]
bridge_df["Did_Rain"] = (bridge_df["precipitation_mm"] > 0).astype(int)

# Feature selection and ML model
features = [
    "temperature_C", "precipitation_mm", "windspeed_mph", "tide_ft", "Is_Daylight",
    "Hour", "Day_of_Week", "time_of_day", "TAVG", "Did_Rain",
    "Vessel_Count", "Start_Minutes", "End_Minutes", "Has_Barge", "Has_Tanker"
]
X = bridge_df[features].dropna()
y = bridge_df.loc[X.index, "Lift_Duration_Minutes"]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)
mlp = MLPRegressor(hidden_layer_sizes=(16, 8), activation='relu', solver='adam', max_iter=500, random_state=42)
mlp.fit(X_train, y_train)
y_pred = mlp.predict(X_test)

# Metrics
rmse = np.sqrt(mean_squared_error(y_test, y_pred))
mae = mean_absolute_error(y_test, y_pred)
within_5min = np.mean(np.abs(y_test - y_pred) <= 5) * 100

# --- Dashboard Visuals ---
st.header("📊 Key Performance Indicators")
col1, col2, col3 = st.columns(3)
col1.metric("RMSE", f"{rmse:.2f} min")
col2.metric("MAE", f"{mae:.2f} min")
col3.metric("±5 min Accuracy", f"{within_5min:.2f}%")

# EDA - Histogram
st.subheader("Distribution of Bridge Lift Durations")
fig1, ax1 = plt.subplots(figsize=(10, 5))
sns.histplot(bridge_df['Lift_Duration_Minutes'], bins=30, kde=True, color='skyblue', ax=ax1)
ax1.set_title("Distribution of Bridge Lift Durations")
ax1.set_xlabel("Lift Duration (Minutes)")
ax1.set_ylabel("Frequency")
st.pyplot(fig1)

# EDA - Boxplot
st.subheader("Lift Duration by Tanker Involvement")
fig2, ax2 = plt.subplots(figsize=(10, 5))
sns.boxplot(x="Has_Tanker", y="Lift_Duration_Minutes", data=bridge_df, ax=ax2)
ax2.set_title("Lift Duration by Tanker Presence")
ax2.set_xlabel("Has Tanker (0 = No, 1 = Yes)")
ax2.set_ylabel("Lift Duration (Minutes)")
st.pyplot(fig2)

# Evaluation Plot
st.subheader("MLP: Actual vs Predicted Lift Duration")
fig3, ax3 = plt.subplots(figsize=(8, 6))
ax3.scatter(y_test, y_pred, alpha=0.7)
ax3.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
ax3.set_xlabel("Actual Duration (min)")
ax3.set_ylabel("Predicted Duration (min)")
ax3.set_title("MLP: Actual vs Predicted Duration")
ax3.grid(True)
st.pyplot(fig3)

# Feature Importance
st.subheader("🔍 Feature Importance")
results = permutation_importance(mlp, X_test, y_test, n_repeats=30, random_state=42)
importance_df = pd.DataFrame({
    "Feature": features,
    "Importance": results.importances_mean
}).sort_values(by="Importance", ascending=True)
fig_imp = px.bar(importance_df, x="Importance", y="Feature", orientation="h", title="Feature Contributions to Prediction")
st.plotly_chart(fig_imp)

# Sample Data
st.subheader("📄 Preview of Cleaned Data")
st.dataframe(bridge_df.head(10))
