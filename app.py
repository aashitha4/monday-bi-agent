import streamlit as st
import pandas as pd
import requests
from openai import OpenAI
import re
import os

# --- 1. CONFIGURATION (Environment Variables) ---
# We use os.environ.get() to pull secrets from the hosting platform
# --- 1. CONFIGURATION (Universal Secret Loader) ---

def get_secret(key):
    """Retrieves secrets from Streamlit Cloud OR Environment Variables (Local/Vercel)"""
    # 1. Try Streamlit Secrets (Best for Streamlit Cloud)
    if key in st.secrets:
        return st.secrets[key]
    # 2. Try OS Environment Variables (Best for Vercel / Local .env)
    return os.environ.get(key)

# Load the keys
MONDAY_TOKEN = get_secret("MONDAY_TOKEN")
DEALS_BOARD_ID = get_secret("DEALS_BOARD_ID")
WO_BOARD_ID = get_secret("WO_BOARD_ID")
GROQ_API_KEY = get_secret("GROQ_API_KEY")

# Fail fast if keys are missing
if not MONDAY_TOKEN or not GROQ_API_KEY:
    st.error(f"🚨 Critical Error: Secrets are missing. Please add MONDAY_TOKEN and GROQ_API_KEY to your configuration.")
    st.stop()

# Initialize Client
client = OpenAI(base_url="https://api.groq.com/openai/v1", api_key=GROQ_API_KEY)

# --- 2. ROBUST DATA FETCHING & CLEANING ---
@st.cache_data(ttl=300)
def fetch_and_clean(board_id):
    url = "https://api.monday.com/v2"
    headers = {
        "Authorization": MONDAY_TOKEN, 
        "API-Version": "2023-10", 
        "Content-Type": "application/json"
    }
    
    query = """
    query {
      boards (ids: [%s]) {
        columns { id title }
        items_page (limit: 500) {
          items {
            name
            column_values { id text }
          }
        }
      }
    }
    """ % board_id
    
    try:
        response = requests.post(url, json={'query': query}, headers=headers, timeout=30)
        data = response.json()
        
        if 'errors' in data:
            st.error(f"Monday API Error: {data['errors'][0]['message']}")
            return pd.DataFrame()

        board_data = data['data']['boards'][0]
        col_map = {c['id']: c['title'] for c in board_data['columns'] if c['title'].lower() != 'name'}
        
        parsed_rows = []
        for item in board_data['items_page']['items']:
            row_data = {"Item Name": item['name']}
            item_vals = {val['id']: val['text'] for val in item['column_values']}
            for col_id, col_title in col_map.items():
                row_data[col_title] = item_vals.get(col_id, "")
            parsed_rows.append(row_data)
            
        df = pd.DataFrame(parsed_rows)

        # 1. Standardize Column Headers
        df.columns = [re.sub(r'[^\w\s]', ' ', col).strip() for col in df.columns]

        # 2. Advanced Type Conversion & Sanity Filter
        money_keywords = ['value', 'amount', 'revenue', 'budget', 'cost', 'price']
        exclude_keywords = ['status', 'stage', 'date', 'id', 'code', 'name', 'probability', 'sector']

        for col in df.columns:
            col_lower = col.lower()
            is_money_col = any(k in col_lower for k in money_keywords)
            is_excluded = any(k in col_lower for k in exclude_keywords)

            if is_money_col and not is_excluded:
                df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                df.loc[df[col] > 1_000_000_000_000, col] = 0
            
        return df
    except Exception as e:
        st.error(f"Fetch Error: {e}")
        return pd.DataFrame()

# --- 3. BI AGENT LOGIC ---
def run_bi_agent(question, deals_df, wo_df):
    deals_cols = list(deals_df.columns)
    wo_cols = list(wo_df.columns)
    
    code_prompt = f"""
    You are a Data Analyst writing Python code.
    User Query: "{question}"
    Dataframes:
    1. deals_df ({len(deals_df)} rows): {deals_cols}
    2. wo_df ({len(wo_df)} rows): {wo_cols}
    Instructions:
    1. Write PANDAS code to solve the query.
    2. Save result in `result`.
    3. Use `.str.contains('Term', case=False)` for text.
    4. Return ONLY raw Python code.
    """
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": code_prompt}], 
            temperature=0
        )
        raw_code = res.choices[0].message.content.strip()
        clean_code = re.sub(r'^```python\s*|```$', '', raw_code, flags=re.MULTILINE).strip()
        
        with st.expander("🛠️ View Generated Python Logic"):
            st.code(clean_code)

        local_vars = {"deals_df": deals_df, "wo_df": wo_df, "pd": pd}
        exec(clean_code, {}, local_vars)
        raw_val = local_vars.get("result", "No result returned")

        summary_prompt = f"""
        User asked: "{question}"
        Result: {raw_val}
        Write a professional 1-sentence executive summary.
        """
        explanation = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[{"role": "user", "content": summary_prompt}]
        )
        return explanation.choices[0].message.content
    except Exception as e:
        return f"⚠️ Agent Logic Error: {str(e)}"

# --- 4. UI LAYOUT ---
st.set_page_config(page_title="Skylark AI Analyst", page_icon="📊", layout="wide")
st.title("📊 Skylark BI Agent")

with st.sidebar:
    if st.button("🔄 Sync Live Data", type="primary"):
        st.cache_data.clear()
        st.session_state['deals_df'] = fetch_and_clean(DEALS_BOARD_ID)
        st.session_state['wo_df'] = fetch_and_clean(WO_BOARD_ID)
        st.success("Data Synced!")

if 'deals_df' in st.session_state:
    query = st.text_input("Start typing your question...")
    if query:
        with st.spinner("Analyzing..."):
            st.success(run_bi_agent(query, st.session_state['deals_df'], st.session_state['wo_df']))
    
    with st.expander("📂 View Raw Data"):
        st.dataframe(st.session_state['deals_df'])
else:

    st.info("👋 Click 'Sync Live Data' to begin.")
