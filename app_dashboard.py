import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
import json
import time
from streamlit_autorefresh import st_autorefresh


# --- Configuration ---
# For public sheets, use the sharing URL
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/179XQa9LLvivItAPTZZ0o3v6iu_TEBdcF7zFX1eK3r04/edit?usp=sharing"

# --- Helper Functions ---
@st.cache_data(ttl=30)  # Increased cache time to 30 seconds
def load_email_data_from_gsheets():
    """
    Connects to Google Sheets and loads the data into a DataFrame.
    """
    try:
        # For PUBLIC sheets - simplified approach
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Try different methods to read the data
        try:
            # Method 1: Read without specifying worksheet
            df = conn.read(spreadsheet=GOOGLE_SHEET_URL)
        except:
            try:
                # Method 2: Specify worksheet explicitly
                df = conn.read(spreadsheet=GOOGLE_SHEET_URL, worksheet="Sheet1")
            except Exception as e:
                st.error(f"Failed to read from Google Sheets: {str(e)}")
                return pd.DataFrame()
            
        # Clean the data
        df = df.dropna(how='all')  # Remove completely empty rows
        df = df.fillna('')  # Fill remaining NaN values with empty strings
        
        # Ensure numeric columns are correctly typed (using actual column names)
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

# Configure auto-refresh (refresh every 60 seconds instead of 30)
st_autorefresh(interval=60000, key="data_refresher")

st.title("✉️ Customer Email Insights Dashboard")

# Load data
df = load_email_data_from_gsheets()

if df.empty:
    st.warning("No email data available. Please check your Google Sheet connection.")
    st.stop()  # Stop execution if no data

# Show data info
st.info(f"⏰ Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

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
    st.error(f"Missing required columns: {missing_columns}")
    st.write("Available columns:", df.columns.tolist())
    st.stop()

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.header("📋 Latest Email (JSON Format)")
    if len(df) > 0:
        latest_row = df.iloc[-1].to_dict()  # Get the last row
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
        complaint = df["output.extracted_requested_action"].iloc[-1]
        department = df["output.routing_recommendation.department"].iloc[-1]
        st.markdown(
            f"""
            <div style='font-size: 36px; font-weight: bold; color: #aeb002; text-align: center;
            animation: pulse 1.5s infinite;'>{complaint}</div>
            <style>@keyframes pulse {{
                0% {{ transform: scale(1); opacity: 1; }}
                50% {{ transform: scale(1.1); opacity: 0.7; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}</style>
            """,
            unsafe_allow_html=True
        )
        st.markdown(
            f"""
            <div style='font-size: 72px; font-weight: bold; color: #ffa500; text-align: center;
            animation: pulse 1.5s infinite;'>{department}</div>
            <style>@keyframes pulse {{
                0% {{ transform: scale(1); opacity: 1; }}
                50% {{ transform: scale(1.1); opacity: 0.7; }}
                100% {{ transform: scale(1); opacity: 1; }}
            }}</style>
            """,
            unsafe_allow_html=True
        )

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    # 1. Emails by Department
    st.header("Emails by Department")
    dept_col = "output.routing_recommendation.department"
    if dept_col in df.columns and len(df[dept_col].dropna()) > 0:
        department_counts = df[dept_col].value_counts().reset_index()
        department_counts.columns = ["Department", "Count"]
        fig_dept = px.pie(
            department_counts,
            names="Department",
            values="Count",
            color="Department"
        )
        st.plotly_chart(fig_dept, use_container_width=True)
    else:
        st.info("No department data available")

with col2:
    st.header("Complaint Volume Over Time")
    try:
        # Convert 'output.extracted_date_of_issue' to datetime
        df['output.extracted_date_of_issue'] = pd.to_datetime(df['output.extracted_date_of_issue'], errors='coerce')
        # Filter out invalid dates
        valid_dates = df['output.extracted_date_of_issue'].dropna()
        if len(valid_dates) > 0:
            # Group by date and count the number of complaints
            complaints_by_date = df.groupby('output.extracted_date_of_issue').size().reset_index(name='Count')
            fig_time = px.scatter(complaints_by_date, 
                            x='output.extracted_date_of_issue', 
                            y='Count')
            fig_time.update_layout(showlegend=False)
            fig_time.update_layout(xaxis_title='Date of Complaint')
            st.plotly_chart(fig_time, use_container_width=True)
        else:
            st.info("No valid date data available")
    except Exception as e:
        st.error(f"Error creating time chart: {str(e)}")

with col3:
    st.subheader("Complaints by Predicted Intent")
    if 'output.predicted_intent' in df.columns and len(df['output.predicted_intent'].dropna()) > 0:
        intent_counts = df['output.predicted_intent'].value_counts().reset_index()
        intent_counts.columns = ['Predicted Intent', 'Count']
        fig_intent = px.bar(intent_counts, 
                            x='Predicted Intent', 
                            y='Count',
                            color='Predicted Intent')
        st.plotly_chart(fig_intent, use_container_width=True)
    else:
        st.info("No intent data available")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.header("Complaints by Product")
    if 'output.extracted_product' in df.columns and len(df['output.extracted_product'].dropna()) > 0:
        product_counts = df['output.extracted_product'].value_counts().reset_index()
        product_counts.columns = ['Product', 'Count']
        fig_product = px.bar(product_counts, 
                                x='Product', 
                                y='Count', 
                                color='Product')
        st.plotly_chart(fig_product, use_container_width=True)
    else:
        st.info("No product data available")

with col2:
    st.header("Distribution of Urgency Levels")
    if 'output.urgency_level' in df.columns and len(df['output.urgency_level'].dropna()) > 0:
        urgency_counts = df['output.urgency_level'].value_counts().reset_index()
        urgency_counts.columns = ['Urgency Level', 'Count']
        fig_urgency = px.bar(urgency_counts, 
                                x='Urgency Level', 
                                y='Count', 
                                color='Urgency Level')
        st.plotly_chart(fig_urgency, use_container_width=True)
    else:
        st.info("No urgency data available")

with col3:
    st.subheader("Complaints by Requested Action")
    if 'output.extracted_requested_action' in df.columns and len(df['output.extracted_requested_action'].dropna()) > 0:
        action_counts = df['output.extracted_requested_action'].value_counts().reset_index()
        action_counts.columns = ['Requested Action', 'Count']
        fig_action = px.bar(action_counts,
                                    x='Requested Action',
                                    y='Count',
                                    color='Requested Action',
                                    labels={'Count': 'Number of Complaints'},
                                    template='plotly_white')
        fig_action.update_layout(xaxis_title='Requested Action', yaxis_title='Number of Complaints')
        st.plotly_chart(fig_action, use_container_width=True)
    else:
        st.info("No action data available")

# Clear cache periodically (but don't force rerun)
if st.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()
