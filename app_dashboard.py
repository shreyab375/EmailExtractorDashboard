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

df = load_email_data_from_gsheets()
st.write(df)
