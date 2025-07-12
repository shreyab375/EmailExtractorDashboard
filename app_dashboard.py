import streamlit as st
import pandas as pd
import plotly.express as px
import json
import time
import requests
import io

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


st.title("✉️ Customer Email Insights Dashboard")
#time.sleep(5)
#st.rerun()
df = load_email_data_from_gsheets()
#print(df)
if df.empty:
    st.warning("No email data available. Please check your Google Sheet connection.")
else:
    # Show data info
    #st.success(f"✅ Successfully loaded {len(df)} rows of data")
    st.info(f"⏰ Last updated: {time.strftime('%Y-%m-%d %H:%M:%S')}")

col1, col2, col3 = st.columns([2, 1, 1])
with col1:
    st.header("📋 Latest Email (JSON Format)")
    if len(df) > 0:
        latest_row = df.iloc[-1].to_dict()  # Get the last row
        st.json(latest_row)

with col2:
    st.header("Total Emails")
    email_count = (len(df))
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
                color="Department"  # Use color to map to department
            )
        st.plotly_chart(fig_dept, use_container_width=True)
    
with col2:
    st.header("Complaint Volume Over Time")
    # Convert 'output.extracted_date_of_issue' to datetime
    df['output.extracted_date_of_issue'] = pd.to_datetime(df['output.extracted_date_of_issue'])
    # Group by date and count the number of complaints
    complaints_by_date = df.groupby('output.extracted_date_of_issue').size().reset_index(name='Count')
    fig_time = px.scatter(complaints_by_date, 
                    x='output.extracted_date_of_issue', 
                    y='Count')
    fig_time.update_layout(showlegend=False)
    fig_time.update_layout(xaxis_title='Date of Complaint')
    st.plotly_chart(fig_time, use_container_width=True)

with col3:
    st.subheader("Complaints by Predicted Intent")
    intent_counts = df['output.predicted_intent'].value_counts().reset_index()
    intent_counts.columns = ['Predicted Intent', 'Count']
    fig_intent = px.bar(intent_counts, 
                        x='Predicted Intent', 
                        y='Count',
                        color='Predicted Intent')
    st.plotly_chart(fig_intent, use_container_width=True)

col1, col2, col3 =  st.columns([1, 1, 1])
with col1:
    st.header("Complaints by Product")
    product_counts = df['output.extracted_product'].value_counts().reset_index()
    product_counts.columns = ['Product', 'Count']
    fig_product = px.bar(product_counts, 
                            x='Product', 
                            y='Count', 
                             color='Product')
    st.plotly_chart(fig_product, use_container_width=True)

with col2:
    st.header(" Distribution of Urgency Levels")
    urgency_counts = df['output.urgency_level'].value_counts().reset_index()
    urgency_counts.columns = ['Urgency Level', 'Count']
    fig_urgency = px.bar(urgency_counts, 
                             x='Urgency Level', 
                             y='Count', 
                             color='Urgency Level')
    st.plotly_chart(fig_urgency, use_container_width=True)

with col3:
    st.subheader("Complaints by Requested Action")
    # Count occurrences of each requested action
    action_counts = df['output.extracted_requested_action'].value_counts().reset_index()
    action_counts.columns = ['Requested Action', 'Count'] # Rename columns for clarity
    fig_action = px.bar(action_counts,
                                x='Requested Action',
                                y='Count',
                                color='Requested Action', # Color bars by requested action
                                labels={'Count': 'Number of Complaints'},
                                template='plotly_white')
    fig_action.update_layout(xaxis_title='Requested Action', yaxis_title='Number of Complaints')
    st.plotly_chart(fig_action, use_container_width=True)
