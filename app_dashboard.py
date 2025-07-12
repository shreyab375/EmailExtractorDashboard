import streamlit as st
import pandas as pd
import plotly.express as px
import json
import time
from streamlit_autorefresh import st_autorefresh
import requests
import io

# --- Configuration ---
# For public sheets, use the CSV export URL
GOOGLE_SHEET_ID = "179XQa9LLvivItAPTZZ0o3v6iu_TEBdcF7zFX1eK3r04"
GOOGLE_SHEET_URL = f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}/export?format=csv&gid=0"

# --- Helper Functions ---
@st.cache_data(ttl=30)  # Cache for 30 seconds
def load_email_data_from_gsheets():
    """
    Connects to Google Sheets and loads the data into a DataFrame using CSV export.
    """
    try:
        # Download CSV data from Google Sheets
        response = requests.get(GOOGLE_SHEET_URL)
        response.raise_for_status()
        
        # Read CSV data into DataFrame
        df = pd.read_csv(io.StringIO(response.text))
        
        # Clean the data
        df = df.dropna(how='all')  # Remove completely empty rows
        df = df.fillna('')  # Fill remaining NaN values with empty strings
        
        # Ensure numeric columns are correctly typed
        numeric_cols = ["output.confidence", "output.sentiment_score", "output.priority_score"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df
    except Exception as e:
        st.error(f"Error loading data from Google Sheets: {str(e)}")
        return pd.DataFrame()

# --- Streamlit App Layout ---
st.set_page_config(layout="wide", page_title="Email Workflow Dashboard")

# Configure auto-refresh (refresh every 60 seconds)
st_autorefresh(interval=60000, key="data_refresher")

st.title("✉️ Customer Email Insights Dashboard")

# Load data
df = load_email_data_from_gsheets()

if df.empty:
    st.warning("No email data available. Please check your Google Sheet connection.")
    st.info("Make sure your Google Sheet is public and sharing is enabled.")
    st.stop()

# Show data info
st.info(f"⏰ Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
st.success(f"✅ Successfully loaded {len(df)} rows of data")

# Debug: Show available columns
with st.expander("Debug: Available Columns"):
    st.write("Available columns:", df.columns.tolist())
    st.write("Data types:", df.dtypes.to_dict())

# Check if we have the required columns
required_columns = [
    "output.extracted_requested_action",
    "output.routing_recommendation.department",
    "output.extracted_date_of_issue",
    "output.predicted_intent",
    "output.extracted_product",
    "output.urgency_level"
]

missing_columns = [col for col in required_columns if col not in df.columns]
if missing_columns:
    st.warning(f"Some expected columns are missing: {missing_columns}")
    st.info("The dashboard will show available data only.")

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.header("📋 Latest Email (JSON Format)")
    if len(df) > 0:
        latest_row = df.iloc[-1].to_dict()
        st.json(latest_row)

with col2:
    st.header("Total Emails")
    email_count = len(df)
    st.markdown(
        f"""
        <div style='
            font-size: 164px;
            font-weight: bold;
            color: #00ffcc;
            text-align: center;
            animation: pulse 1.5s infinite;
        '>{email_count}</div>

        <style>
        @keyframes pulse {{
            0% {{ transform: scale(1); }}
            50% {{ transform: scale(1.2); }}
            100% {{ transform: scale(1); }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

with col3:
    st.header("Forwarding Department")
    if len(df) > 0:
        # Use safe column access
        complaint_col = "output.extracted_requested_action"
        department_col = "output.routing_recommendation.department"
        
        complaint = df[complaint_col].iloc[-1] if complaint_col in df.columns else "N/A"
        department = df[department_col].iloc[-1] if department_col in df.columns else "N/A"
        
        st.markdown(
            f"""
            <div style='font-size: 36px; font-weight: bold; color: #aeb002; text-align: center;
            animation: pulse 1.5s infinite;'>{complaint}</div>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style='font-size: 72px; font-weight: bold; color: #ffa500; text-align: center;
            animation: pulse 1.5s infinite;'>{department}</div>
            """,
            unsafe_allow_html=True
        )

# Create charts with safe column access
col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.header("Emails by Department")
    dept_col = "output.routing_recommendation.department"
    if dept_col in df.columns and len(df[dept_col].dropna()) > 0:
        department_counts = df[dept_col].value_counts().reset_index()
        department_counts.columns = ["Department", "Count"]
        fig_dept = px.pie(
            department_counts,
            names="Department",
            values="Count",
            title="Distribution by Department"
        )
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("No department data available")

with col2:
    st.header("Complaint Volume Over Time")
    date_col = "output.extracted_date_of_issue"
    if date_col in df.columns:
        try:
            # Convert to datetime
            df_temp = df.copy()
            df_temp[date_col] = pd.to_datetime(df_temp[date_col], errors='coerce')
            valid_dates = df_temp[df_temp[date_col].notna()]
            
            if len(valid_dates) > 0:
                complaints_by_date = valid_dates.groupby(date_col).size().reset_index(name='Count')
                fig_time = px.line(complaints_by_date, 
                                x=date_col, 
                                y='Count',
                                title="Complaints Over Time")
                fig_time.update_layout(xaxis_title='Date of Complaint')
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("No valid date data available")
        except Exception as e:
            st.error(f"Error creating time chart: {str(e)}")
    else:
        st.info("No date data available")

with col3:
    st.header("Complaints by Intent")
    intent_col = "output.predicted_intent"
    if intent_col in df.columns and len(df[intent_col].dropna()) > 0:
        intent_counts = df[intent_col].value_counts().reset_index()
        intent_counts.columns = ['Predicted Intent', 'Count']
        fig_intent = px.bar(intent_counts, 
                            x='Predicted Intent', 
                            y='Count',
                            title="Complaints by Intent")
        st.plotly_chart(fig_intent, use_container_width=True)
    else:
        st.info("No intent data available")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.header("Complaints by Product")
    product_col = "output.extracted_product"
    if product_col in df.columns and len(df[product_col].dropna()) > 0:
        product_counts = df[product_col].value_counts().reset_index()
        product_counts.columns = ['Product', 'Count']
        fig_product = px.bar(product_counts, 
                            x='Product', 
                            y='Count',
                            title="Complaints by Product")
        st.plotly_chart(fig_product, use_container_width=True)
    else:
        st.info("No product data available")

with col2:
    st.header("Urgency Levels")
    urgency_col = "output.urgency_level"
    if urgency_col in df.columns and len(df[urgency_col].dropna()) > 0:
        urgency_counts = df[urgency_col].value_counts().reset_index()
        urgency_counts.columns = ['Urgency Level', 'Count']
        fig_urgency = px.bar(urgency_counts, 
                            x='Urgency Level', 
                            y='Count',
                            title="Distribution of Urgency Levels")
        st.plotly_chart(fig_urgency, use_container_width=True)
    else:
        st.info("No urgency data available")

with col3:
    st.header("Requested Actions")
    action_col = "output.extracted_requested_action"
    if action_col in df.columns and len(df[action_col].dropna()) > 0:
        action_counts = df[action_col].value_counts().reset_index()
        action_counts.columns = ['Requested Action', 'Count']
        fig_action = px.bar(action_counts,
                           x='Requested Action',
                           y='Count',
                           title="Complaints by Requested Action")
        fig_action.update_layout(xaxis_title='Requested Action', yaxis_title='Count')
        st.plotly_chart(fig_action, use_container_width=True)
    else:
        st.info("No action data available")

# Manual refresh button
if st.button("🔄 Refresh Data"):
    st.cache_data.clear()
    st.rerun()

# Show raw data in expandable section
with st.expander("📊 Raw Data"):
    st.dataframe(df)
