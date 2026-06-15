import streamlit as st
import re
import os
import pandas as pd
import requests
import altair as alt
from dotenv import load_dotenv

# Import client modules
from splunk_client import run_spl, get_service
from llm_client import call_llm
from prompts import build_system_prompt

# Load environment variables
load_dotenv()

# Page setup
st.set_page_config(
    page_title="SPL Generator", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar layout for Navigation, History and Settings
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    # 1. Dark/Light Theme Toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=True)
    st.markdown("---")

# Inject theme-specific CSS (Business/Analytics Focus)
if dark_mode:
    # Slate Dark Theme
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #0F172A !important;
        color: #F8FAFC !important;
    }
    
    .stApp {
        background-color: #0F172A !important;
    }

    /* Global Text Styling overrides */
    p, span, label, small, li, h1, h2, h3, h4, h5, h6 {
        color: #F8FAFC !important;
    }

    /* Sidebar Reset */
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
        border-right: 1px solid #334155 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Inputs & Forms */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stForm"] input, 
    input, 
    textarea {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        caret-color: #3B82F6 !important;
        border: 1px solid #334155 !important;
    }
    
    input::placeholder, textarea::placeholder {
        color: #64748B !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #1E293B !important;
        color: #F8FAFC !important;
        border-color: #334155 !important;
    }
    
    div[data-testid="stTextInput"] label, 
    label {
        color: #94A3B8 !important;
    }

    /* Header */
    .title-container {
        padding-top: 1rem;
        margin-bottom: 0.2rem;
    }

    .title-text {
        font-size: 2.8rem;
        font-weight: 700;
        color: #3B82F6;
    }

    .subtitle-text {
        font-size: 1.05rem;
        color: #94A3B8;
        margin-bottom: 1.5rem;
    }

    /* Diagnostics Card */
    .status-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 1rem;
        color: #E2E8F0 !important;
    }

    span.status-badge.status-green {
        background-color: rgba(16, 185, 129, 0.15) !important;
        color: #34D399 !important;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }

    span.status-badge.status-red {
        background-color: rgba(239, 68, 68, 0.15) !important;
        color: #F87171 !important;
        border: 1px solid rgba(239, 68, 68, 0.3) !important;
    }

    /* Code Block Styling */
    code, pre, code * {
        background-color: #1E293B !important;
        color: #38BDF8 !important;
    }

    /* Query Card */
    .query-card {
        background: #1E293B;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
    }

    .explanation-box {
        background-color: rgba(59, 130, 246, 0.08);
        border-left: 4px solid #3B82F6;
        padding: 0.8rem 1.2rem;
        border-radius: 4px;
        margin-top: 0.8rem;
        margin-bottom: 1rem;
        color: #E2E8F0;
    }

    /* Helper captions */
    div[data-testid="caption"] p, 
    div[data-testid="caption"] span,
    small {
        color: #94A3B8 !important;
    }

    /* Buttons override */
    div.stButton > button, 
    div.stButton > button * {
        background-color: #2563EB !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    div.stButton > button:hover {
        background-color: #1D4ED8 !important;
    }
    </style>
    """, unsafe_allow_html=True)
else:
    # Clean Light Theme
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
        background-color: #F8FAFC !important;
        color: #0F172A !important;
    }
    
    .stApp {
        background-color: #F8FAFC !important;
    }

    /* Global Text Styling overrides */
    p, span, label, small, li, h1, h2, h3, h4, h5, h6 {
        color: #0F172A !important;
    }

    /* Sidebar Reset */
    section[data-testid="stSidebar"] {
        background-color: #F1F5F9 !important;
        border-right: 1px solid #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #0F172A !important;
    }

    /* Inputs & Forms */
    div[data-testid="stTextInput"] input, 
    div[data-testid="stForm"] input, 
    input, 
    textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        caret-color: #1E40AF !important;
        border: 1px solid #CBD5E1 !important;
    }
    
    input::placeholder, textarea::placeholder {
        color: #94A3B8 !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border-color: #CBD5E1 !important;
    }
    
    div[data-testid="stTextInput"] label, 
    label {
        color: #475569 !important;
    }

    /* Header */
    .title-container {
        padding-top: 1rem;
        margin-bottom: 0.2rem;
    }

    .title-text {
        font-size: 2.8rem;
        font-weight: 700;
        color: #1E40AF;
    }

    .subtitle-text {
        font-size: 1.05rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }

    /* Diagnostics Card */
    .status-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 0.8rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        color: #334155 !important;
    }

    span.status-badge.status-green {
        background-color: rgba(4, 120, 87, 0.1) !important;
        color: #047857 !important;
        border: 1px solid rgba(4, 120, 87, 0.2) !important;
    }

    span.status-badge.status-red {
        background-color: rgba(185, 28, 28, 0.1) !important;
        color: #B91C1C !important;
        border: 1px solid rgba(185, 28, 28, 0.2) !important;
    }

    /* Code Block Styling */
    code, pre, code * {
        background-color: #F1F5F9 !important;
        color: #1E40AF !important;
    }

    /* Query Card */
    .query-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.5rem;
        margin-top: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }

    .explanation-box {
        background-color: rgba(30, 64, 175, 0.04);
        border-left: 4px solid #1E40AF;
        padding: 0.8rem 1.2rem;
        border-radius: 4px;
        margin-top: 0.8rem;
        margin-bottom: 1rem;
        color: #1E293B;
    }

    /* Helper captions */
    div[data-testid="caption"] p, 
    div[data-testid="caption"] span,
    small {
        color: #475569 !important;
    }

    /* Buttons override */
    div.stButton > button, 
    div.stButton > button * {
        background-color: #1D4ED8 !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    div.stButton > button:hover {
        background-color: #1E40AF !important;
    }
    </style>
    """, unsafe_allow_html=True)

# Helper parsing and formatting functions
def parse_llm_response(response: str) -> tuple:
    """Extracts the SPL query and the explanation from LLM response."""
    spl = ""
    explanation = ""
    
    # Try using regex to find "SPL:" and "EXPLANATION:"
    spl_match = re.search(r"SPL:\s*(.*?)(?=\nEXPLANATION:|$)", response, re.DOTALL | re.IGNORECASE)
    exp_match = re.search(r"EXPLANATION:\s*(.*)", response, re.DOTALL | re.IGNORECASE)
    
    if spl_match:
        spl = spl_match.group(1).strip()
    if exp_match:
        explanation = exp_match.group(1).strip()
        
    # Fallback if parsing failed
    if not spl:
        spl = re.sub(r"```[\w]*|```", "", response).strip()
        lines = [line.strip() for line in spl.split("\n") if line.strip()]
        if lines:
            spl = lines[0]
            if len(lines) > 1:
                explanation = " ".join(lines[1:])
                
    spl = re.sub(r"```[\w]*|```", "", spl).strip()
    return spl, explanation

def auto_convert_df(df: pd.DataFrame) -> pd.DataFrame:
    """Converts string columns to numeric types or datetimes where possible."""
    df = df.copy()
    for col in df.columns:
        if col in ["_time", "time"]:
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass
            continue
        
        # Try converting to numeric
        try:
            converted = pd.to_numeric(df[col], errors='raise')
            if not col.lower().endswith("ip") and not col.lower().endswith("id") and not col.lower().endswith("status"):
                df[col] = converted
        except Exception:
            pass
    return df

def render_visualisations(df: pd.DataFrame, dark_mode: bool):
    """Renders appropriate Altair charts based on DataFrame shape."""
    time_col = None
    if "_time" in df.columns:
        time_col = "_time"
    elif "time" in df.columns:
        time_col = "time"
        
    numeric_cols = []
    categorical_cols = []
    for col in df.columns:
        if col in ["_time", "time"]:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
        else:
            categorical_cols.append(col)
            
    # Chart Colors selection & Label standouts
    if dark_mode:
        chart_colors = ["#3B82F6", "#10B981", "#F59E0B", "#EC4899"]
        label_color = "#38BDF8"
        title_color = "#94A3B8"
        grid_color = "#334155"
    else:
        chart_colors = ["#1D4ED8", "#0D9488", "#D97706", "#DB2777"]
        label_color = "#1D4ED8"
        title_color = "#475569"
        grid_color = "#E2E8F0"

    # Case 1: Time Series Trend Line Chart (Altair)
    if time_col and numeric_cols:
        st.markdown("### 📈 Trend chart")
        chart_df = df[[time_col] + numeric_cols].copy()
        chart_df = chart_df.sort_values(by=time_col)
        
        # Melt dataframe to support multi-line plotting
        melted_df = chart_df.melt(id_vars=[time_col], value_vars=numeric_cols, var_name="Metric", value_name="Value")
        
        chart = alt.Chart(melted_df).mark_line(point=True).encode(
            x=alt.X(f"{time_col}:T", title=time_col, axis=alt.Axis(
                labelColor=label_color, titleColor=title_color, gridColor=grid_color
            )),
            y=alt.Y("Value:Q", title="Value", axis=alt.Axis(
                labelColor=label_color, titleColor=title_color, gridColor=grid_color
            )),
            color=alt.Color("Metric:N", scale=alt.Scale(range=chart_colors), legend=alt.Legend(
                labelColor=label_color, titleColor=title_color
            )),
            tooltip=[time_col, "Metric", "Value"]
        ).properties(
            height=300
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)
        
    # Case 2: Distribution Bar Chart (Altair)
    elif categorical_cols and numeric_cols:
        cat_col = categorical_cols[0]
        num_col = numeric_cols[0]
        st.markdown(f"### 📊 Distribution: {num_col} by {cat_col}")
        
        chart = alt.Chart(df).mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4).encode(
            x=alt.X(f"{cat_col}:N", title=cat_col, sort='-y', axis=alt.Axis(
                labelColor=label_color, titleColor=title_color, gridColor=grid_color, labelAngle=-45
            )),
            y=alt.Y(f"{num_col}:Q", title=num_col, axis=alt.Axis(
                labelColor=label_color, titleColor=title_color, gridColor=grid_color
            )),
            color=alt.value(chart_colors[0]),
            tooltip=[cat_col, num_col]
        ).properties(
            height=300
        ).configure_view(
            strokeWidth=0
        )
        
        st.altair_chart(chart, use_container_width=True)

# Initialize Session States
if "question" not in st.session_state:
    st.session_state["question"] = ""
if "messages" not in st.session_state:
    st.session_state.messages = []
if "current_spl" not in st.session_state:
    st.session_state.current_spl = ""
if "current_explanation" not in st.session_state:
    st.session_state.current_explanation = ""
if "current_results" not in st.session_state:
    st.session_state.current_results = None
if "history" not in st.session_state:
    st.session_state.history = []

# Title Section
st.markdown("""
<div class="title-container">
    <h1 class="title-text">🔍 SPL Generator</h1>
</div>
<div class="subtitle-text">
    Translate plain English questions into clean Splunk Processing Language (SPL) queries and run them instantly.
</div>
""", unsafe_allow_html=True)

# Connection Status Checkers
splunk_connected = False
splunk_err_msg = ""
try:
    service = get_service()
    splunk_connected = True
except Exception as e:
    splunk_err_msg = str(e)

# Check if local Ollama is running
ollama_connected = False
try:
    resp = requests.get("http://localhost:11434/api/tags", timeout=1)
    if resp.status_code == 200:
        ollama_connected = True
except Exception:
    pass

llm_status = "Not Configured"
llm_badge_class = "status-red"
if ollama_connected:
    llm_status = "Local: Ollama"
    llm_badge_class = "status-green"
elif os.getenv("SPLUNK_HOSTED_MODEL_ENDPOINT"):
    llm_status = "Splunk Hosted"
    llm_badge_class = "status-green"
elif os.getenv("ANTHROPIC_API_KEY"):
    llm_status = "Anthropic Claude"
    llm_badge_class = "status-green"
elif os.getenv("OPENAI_API_KEY"):
    llm_status = "OpenAI GPT"
    llm_badge_class = "status-green"

# Layout: Main content (col1) and Status Sidebar (col2 - allocated smaller width)
col1, col2 = st.columns([5, 1])

with col2:
    st.markdown("### 📊 Status")
    
    # Splunk Connection Badge
    if splunk_connected:
        st.markdown(f'<div class="status-card">🔌 Splunk: <span class="status-badge status-green">ONLINE</span></div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="status-card">🔌 Splunk: <span class="status-badge status-red">OFFLINE</span><br/><small style="color:#f56565;">{splunk_err_msg}</small></div>', unsafe_allow_html=True)
        
    # LLM Service Badge
    st.markdown(f'<div class="status-card">🤖 LLM: <span class="status-badge {llm_badge_class}">{llm_status}</span></div>', unsafe_allow_html=True)

with col1:
    st.markdown("### 📝 Ask a Question")
    
    # Query Suggestions Box (Aligned to the 10-day tutorial range)
    st.markdown("**Suggestions:**")
    suggestions = [
        "Show me the top 10 pages by visits",
        "How many errors happened each hour over the last 10 days",
        "Which IP addresses made the most requests",
        "Show me all 404 errors in the last 10 days",
    ]
    
    s_cols = st.columns(len(suggestions))
    for idx, s in enumerate(suggestions):
        if s_cols[idx].button(s, key=f"sug_{idx}"):
            st.session_state["question"] = s
            st.session_state.messages = []
            st.session_state.current_results = None
            st.session_state.current_spl = ""
            st.session_state.current_explanation = ""
            st.rerun()

    # Form to input base question
    with st.form("query_form", clear_on_submit=False):
        user_input = st.text_input(
            "Natural Language Question:",
            value=st.session_state["question"],
            placeholder="e.g., show me all errors in index=main over the last 10 days",
            key="user_question"
        )
        submit_button = st.form_submit_button("Generate & Run Query")

    # If the user submitted a new base query
    if submit_button and user_input.strip():
        st.session_state["question"] = user_input
        st.session_state.messages = [{"role": "user", "content": user_input}]
        st.session_state.current_results = None
        st.session_state.current_spl = ""
        st.session_state.current_explanation = ""
        
        # Add to sidebar history if not duplicate
        if not st.session_state.history or st.session_state.history[-1] != user_input:
            st.session_state.history.append(user_input)
            
        with st.spinner("Generating SPL..."):
            try:
                raw_response = call_llm(build_system_prompt(), st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": raw_response})
                
                spl, explanation = parse_llm_response(raw_response)
                st.session_state.current_spl = spl
                st.session_state.current_explanation = explanation
            except Exception as e:
                st.error(f"❌ Failed to generate SPL: {e}")
                
        # Run Splunk query
        if st.session_state.current_spl:
            with st.spinner("Executing query..."):
                rows, error = run_spl(st.session_state.current_spl)
                if error:
                    st.error(f"❌ Splunk query execution failed: {error}")
                else:
                    st.session_state.current_results = rows
        st.rerun()

    # Render results
    if st.session_state.current_spl:
        st.markdown('<div class="query-card">', unsafe_allow_html=True)
        
        st.subheader("Generated SPL Query")
        st.code(st.session_state.current_spl, language="sql")
        
        if st.session_state.current_explanation:
            st.markdown(f'<div class="explanation-box">💡 {st.session_state.current_explanation}</div>', unsafe_allow_html=True)
            
        if st.session_state.current_results is not None:
            if not st.session_state.current_results:
                st.warning("⚠️ Query executed successfully but returned 0 rows.")
                spl_query = st.session_state.current_spl.lower()
                short_ranges = ["earliest=-1h", "earliest=-30m", "earliest=-15m", "earliest=-24h", "earliest=-4h", "earliest=-6h"]
                if any(sr in spl_query for sr in short_ranges) or "latest=now" in spl_query:
                    st.info("💡 **Demo Tip:** The Splunk tutorial dataset is static (spanning June 7 to June 15, 2026). Narrow relative filters like `earliest=-1h` or `earliest=-24h` will return 0 rows if run outside of that window. For your demo, try asking for the **last 10 days** or **last week** to ensure data points are matched!")
            else:
                st.subheader(f"📊 Results — {len(st.session_state.current_results)} rows")
                
                df = pd.DataFrame(st.session_state.current_results)
                df = auto_convert_df(df)
                
                # Render Altair charts (with standout labels)
                render_visualisations(df, dark_mode)
                
                # Display data table
                st.markdown("### 📋 Data table")
                cols = list(df.columns)
                time_cols = [c for c in ["_time", "time"] if c in cols]
                for tc in time_cols:
                    cols.remove(tc)
                    cols = [tc] + cols
                df = df[cols]
                st.dataframe(df, use_container_width=True)
                
                # Export option
                csv_data = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Export Results as CSV",
                    data=csv_data,
                    file_name="splunk_search_results.csv",
                    mime="text/csv"
                )
                
        # conversational refinement form
        st.markdown("---")
        with st.form("refine_form", clear_on_submit=True):
            refinement_input = st.text_input(
                "💬 Refine search / ask a follow-up question:",
                placeholder="e.g. limit to top 5, filter status=500, change time range to 10 days",
                key="refinement_input_val"
            )
            refine_submit = st.form_submit_button("Apply Refinement")
            
        if refine_submit and refinement_input.strip():
            st.session_state.messages.append({"role": "user", "content": refinement_input})
            
            with st.spinner("Refining SPL..."):
                try:
                    raw_response = call_llm(build_system_prompt(), st.session_state.messages)
                    st.session_state.messages.append({"role": "assistant", "content": raw_response})
                    
                    spl, explanation = parse_llm_response(raw_response)
                    st.session_state.current_spl = spl
                    st.session_state.current_explanation = explanation
                    
                    rows, error = run_spl(spl)
                    if error:
                        st.error(f"❌ Splunk query execution failed: {error}")
                    else:
                        st.session_state.current_results = rows
                except Exception as e:
                    st.error(f"❌ Failed to refine SPL: {e}")
            st.rerun()
            
        st.markdown('</div>', unsafe_allow_html=True)

# Sidebar layout for History
with st.sidebar:
    st.markdown("### Setup Guidelines")
    st.markdown("""
    1. Make sure your local **Splunk Enterprise** is running.
    2. Upload the tutorial data (`tutorialdata.zip`) into Splunk.
       * Go to Splunk Web → Settings → Add Data → Upload.
       * Source type: `access_combined_wcookie`, Index: `main`.
    """)
    
    # Query History List
    if st.session_state.history:
        st.markdown("---")
        st.markdown("### 🕒 Recent Searches")
        for idx, q in enumerate(reversed(st.session_state.history[-10:])):
            if st.button(q, key=f"hist_{idx}"):
                st.session_state["question"] = q
                st.session_state.messages = []
                st.session_state.current_results = None
                st.session_state.current_spl = ""
                st.session_state.current_explanation = ""
                st.rerun()
                
        if st.button("🗑️ Clear History"):
            st.session_state.history = []
            st.session_state.messages = []
            st.session_state.current_results = None
            st.session_state.current_spl = ""
            st.session_state.current_explanation = ""
            st.rerun()
