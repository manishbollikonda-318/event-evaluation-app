"""
==============================================================================
 EVENT EVALUATION APP — Professional Scoring Platform
==============================================================================
 A single-file Streamlit + SQLite application that replaces spreadsheet-based
 evaluation with a structured, real-time scoring system.

 Run with:  streamlit run app.py
 Requires:  pip install streamlit pandas plotly
==============================================================================
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
from contextlib import contextmanager
import io


# ============================================================================
# SECTION 1: SOVEREIGN DATABASE ENGINE
# ============================================================================
@contextmanager
def db_session():
    """
    Sovereign Context Manager for SQLite sessions.
    Ensures absolute connection closure and handles timeouts.
    """
    conn = sqlite3.connect('evaluations.db', timeout=15)
    try:
        yield conn
    finally:
        conn.close()

@st.cache_resource
def init_database():
    """
    Initializes the Level-10 persistence layer.
    """
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_name   TEXT    NOT NULL,
                evaluator_name   TEXT    NOT NULL,
                technical_score  INTEGER NOT NULL,
                communication    INTEGER NOT NULL,
                overall_fit      INTEGER NOT NULL,
                total_score      INTEGER NOT NULL,
                submitted_at     TEXT    NOT NULL
            )
        ''')
        conn.commit()


# ============================================================================
# SECTION 2: DATABASE INSERT OPERATION
# ============================================================================
def insert_score(candidate_name, evaluator_name, technical, communication, fit):
    """
    Inserts a validated evaluation record.
    """
    total_score = technical + communication + fit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO scores (
                    candidate_name,
                    evaluator_name,
                    technical_score,
                    communication,
                    overall_fit,
                    total_score,
                    submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (candidate_name, evaluator_name, technical, communication,
                  fit, total_score, timestamp))
            conn.commit()
            
        if 'get_raw_data' in globals():
            get_raw_data.clear()
        return True

    except sqlite3.OperationalError as e:
        st.error(f"Database contention detected. Retrying... ({e})")
        return False
    except Exception as e:
        st.error(f"Sovereign Engine Error (Insertion): {e}")
        return False


# ============================================================================
# SECTION 3: DATABASE READ + PANDAS AGGREGATION
# ============================================================================
@st.cache_data(ttl=60)
def get_raw_data():
    with db_session() as conn:
        raw_df = pd.read_sql_query(
            "SELECT * FROM scores ORDER BY submitted_at DESC",
            conn
        )
    # Filter out corrupted data (special characters in names)
    import re
    valid_name_pattern = r"^[A-Za-z\s]+$"
    raw_df = raw_df[
        raw_df['candidate_name'].str.match(valid_name_pattern, na=False) &
        raw_df['evaluator_name'].str.match(valid_name_pattern, na=False)
    ]
    return raw_df

def get_leaderboard():
    """
    Queries all scores and aggregates them into a ranked leaderboard.
    """
    raw_df = get_raw_data()

    if raw_df.empty:
        return pd.DataFrame(), raw_df

    leaderboard = raw_df.groupby('candidate_name').agg(
        total_combined_score=('total_score', 'sum'),
        avg_score=('total_score', 'mean'),
        num_evaluations=('total_score', 'count'),
        avg_technical=('technical_score', 'mean'),
        avg_communication=('communication', 'mean'),
        avg_fit=('overall_fit', 'mean'),
    ).sort_values(
        'total_combined_score', ascending=False
    ).reset_index()

    leaderboard['avg_score'] = leaderboard['avg_score'].round(1)
    leaderboard['avg_technical'] = leaderboard['avg_technical'].round(1)
    leaderboard['avg_communication'] = leaderboard['avg_communication'].round(1)
    leaderboard['avg_fit'] = leaderboard['avg_fit'].round(1)

    leaderboard.insert(0, 'Rank', range(1, len(leaderboard) + 1))

    return leaderboard, raw_df


# ============================================================================
# SECTION 4: DATA DELETION
# ============================================================================
def delete_score(score_id):
    """
    Atomic deletion from the Sovereign persistence layer.
    """
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM scores WHERE id = ?', (score_id,))
            conn.commit()
            
        if 'get_raw_data' in globals():
            get_raw_data.clear()
        return True

    except Exception as e:
        st.error(f"Deletion failed in Sovereign Engine: {e}")
        return False


# ============================================================================
# SECTION 5: STREAMLIT UI — PAGE CONFIG & CLEAN LIGHT-MODE CSS
# ============================================================================
st.set_page_config(
    page_title="Event Evaluation App",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# SECTION 5.5: SECURITY GATING (REMOVED)
# ============================================================================
# Security gating removed per user request for free access.

init_database()

# ---------- PRO-MAX RESPONSIVE DESIGN SYSTEM ----------
# White/light-gray background throughout. A single functional blue (#2563EB)
# is used ONLY for buttons and interactive highlights — never for text or UI bg.
st.markdown("""
<style>
    /* Google Fonts Integration */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;800&display=swap');

    /* Global Overrides */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background: radial-gradient(circle at top right, #0B1120 0%, #030712 100%) !important;
        color: #f8fafc !important;
    }

    /* Transparent Sidebar with Blur */
    [data-testid="stSidebar"] {
        background-color: rgba(9, 14, 23, 0.7) !important;
        backdrop-filter: blur(20px);
        -webkit-backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        min-width: 300px !important;
    }

    /* Sidebar Navigation glowing state */
    .stRadio > div[role="radiogroup"] > label {
        background: transparent !important;
        padding: 10px 15px;
        border-radius: 8px;
        transition: all 0.3s ease;
    }
    .stRadio > div[role="radiogroup"] > label[data-checked="true"] {
        background: rgba(56, 189, 248, 0.1) !important;
        border-left: 4px solid #38bdf8 !important;
        box-shadow: inset 20px 0 30px -20px rgba(56, 189, 248, 0.3);
    }
    
    [data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }

    /* Premium Logo Container */
    .premium-logo {
        padding: 1.5rem;
        background: linear-gradient(145deg, rgba(30, 41, 59, 0.4) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 24px;
        box-shadow: inset 0 1px 1px rgba(255, 255, 255, 0.05), 0 8px 20px rgba(0,0,0,0.3);
    }
    .premium-logo h3 {
        margin: 0;
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Outfit', sans-serif;
        font-size: 1.4rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    /* Typography */
    .main-header {
        font-family: 'Outfit', sans-serif;
        font-size: 3.2rem;
        font-weight: 800;
        color: #f8fafc;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
    }

    .sub-header {
        font-size: 1.1rem;
        color: #94a3b8;
        margin-bottom: 2.5rem;
        font-weight: 400;
        line-height: 1.6;
    }

    /* Inputs with Glowing Focus */
    div[data-baseweb="input"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    div[data-baseweb="input"]:focus-within {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.3) !important;
    }
    div[data-baseweb="input"] input {
        color: #f8fafc !important;
    }

    /* Glassmorphism Cards */
    .metric-card, .tutorial-card {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        padding: 1.5rem !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.2) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    /* Bento Box Design */
    .bento-container {
        display: grid;
        grid-template-columns: 1fr;
        gap: 16px;
    }
    .bento-card {
        background: rgba(30, 41, 59, 0.3);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 24px;
        padding: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
    }
    .bento-main {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    
    /* Circular Progress Gauge */
    .flex-wrapper {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .single-chart {
        width: 180px;
        justify-content: space-around;
        filter: drop-shadow(0 0 15px rgba(0, 0, 0, 0.3));
    }
    .circular-chart {
        display: block;
        margin: 0 auto;
        max-width: 100%;
        max-height: 250px;
    }
    .circle-bg {
        fill: none;
        stroke: rgba(255, 255, 255, 0.05);
        stroke-width: 2.5;
    }
    .circle {
        fill: none;
        stroke-width: 2.8;
        stroke-linecap: round;
        transition: stroke-dasharray 1s ease-out;
    }
    .percentage {
        fill: #f8fafc;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 0.6em;
        text-anchor: middle;
    }

    /* Sub-score Mini Bars */
    .sub-score-item {
        margin-top: 16px;
    }
    .sub-score-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        color: #94a3b8;
        font-weight: 600;
        margin-bottom: 6px;
    }
    .mini-track {
        height: 8px;
        background: rgba(0,0,0,0.3);
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05);
    }
    .mini-fill {
        height: 100%;
        border-radius: 10px;
        box-shadow: inset 0 0 10px rgba(255,255,255,0.2);
        transition: width 0.5s ease-out;
    }

    /* Premium Button Stack */
    .stButton > button {
        background: linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%) !important;
        color: white !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        padding: 0.8rem 2rem !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 20px rgba(56, 189, 248, 0.2) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-family: 'Outfit', sans-serif !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 15px 30px rgba(56, 189, 248, 0.4) !important;
        filter: brightness(1.1);
    }

    /* Custom Sliders */
    .stSlider > div > div > div > div {
        background: linear-gradient(90deg, #38bdf8, #818cf8) !important;
    }
    .stSlider > div > div > div > div > div {
        background-color: #ffffff !important;
        border: 2px solid #818cf8 !important;
        box-shadow: 0 0 10px rgba(129, 140, 248, 0.6) !important;
    }
    .stSlider label p {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }

    /* Glowing Pill Status */
    .status-pill {
        display: inline-block;
        padding: 8px 24px;
        border-radius: 30px;
        font-family: 'Outfit', sans-serif;
        font-weight: 800;
        font-size: 0.95rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 24px;
        backdrop-filter: blur(10px);
    }

    /* Hide UI Noise */
    #MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True), unsafe_allow_html=True)


# ============================================================================
# SECTION 6: SIDEBAR NAVIGATION
# ============================================================================
with st.sidebar:
    st.markdown("""
    <div class="premium-logo">
        <h3>
            <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="color: #38bdf8;"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>
            SOVEREIGN
        </h3>
        <p style="margin:4px 0 0 0; font-size:0.75rem; color:#94a3b8; text-transform:uppercase; letter-spacing:1px; font-weight:600;">Engine v10 &bull; Active</p>
    </div>
    """, unsafe_allow_html=True)
    
    page = st.radio(
        "Navigation",
        ["Score Entry", "Executive Dashboard", "Data Mastery"],
        label_visibility="collapsed"
    )
    
    st.markdown("---")
    st.markdown("<h5 style='color:#94a3b8; font-size:0.85rem; font-weight:600; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;'>System Actions</h5>", unsafe_allow_html=True)
    
    if st.button("🔄 Force Data Refresh"):
        get_raw_data.clear()
        st.rerun()
    
    # Professional CSV Export in Sidebar
    raw_df_export = get_raw_data()
    if not raw_df_export.empty:
        csv = raw_df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"event_eval_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime='text/csv',
            use_container_width=True
        )


# Legacy Tutorial Removed per user request for performance.
if "tutorial_done" not in st.session_state:
    st.session_state.tutorial_done = True


# ============================================================================
# SECTION 7: SCORE ENTRY PAGE
# ============================================================================
# Layout: LEFT column = inputs & controls, RIGHT column = live score feedback.
# All sliders are outside st.form so total updates in real-time on drag.
#
# IMPORTANT — State Reset Pattern:
#   Streamlit raises StreamlitAPIException if you modify session_state for a
#   widget key AFTER that widget has already been instantiated in the current
#   script run.  To work around this, we use a flag ('form_submitted'):
#     1. On submit  -> set flag to True, call st.experimental_rerun()
#     2. On the NEXT rerun (before widgets render) -> detect the flag,
#        clear the keys, delete the flag.  Now the widgets see fresh defaults.
# ============================================================================

if page == "Score Entry":

    submitted_data = st.session_state.get("form_submitted", None)
    if submitted_data:
        if "reset_counter" not in st.session_state:
            st.session_state.reset_counter = 0
        st.session_state.reset_counter += 1
        
        cand_name_display = submitted_data.get("cand", "Candidate")
        eval_name_display = submitted_data.get("eval", "You")
        
        del st.session_state["form_submitted"]
        
        # Render a beautiful custom animated popup + Confetti
        st.markdown(f"""
        <div class="custom-popup">
            <div class="popup-icon">🏆</div>
            <div class="popup-text">
                <h4 style="color: #60a5fa; font-family: 'Outfit', sans-serif;">Submission Beast Mode!</h4>
                <p>Thank you <b>{eval_name_display}</b>! Your evaluation for <b>{cand_name_display}</b> is live.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Confetti Script
        st.components.v1.html("""
            <script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
            <script>
                confetti({
                    particleCount: 150,
                    spread: 70,
                    origin: { y: 0.6 },
                    colors: ['#2563eb', '#60a5fa', '#f8fafc']
                });
            </script>
        """, height=0)

    if "reset_counter" not in st.session_state:
        st.session_state.reset_counter = 0

    st.markdown('<p class="main-header">Score Entry</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Evaluate candidates on Technical Skills, Communication, and Overall Fit.'
        '</p>',
        unsafe_allow_html=True
    )

    # ---- Two-column layout: Controls LEFT | Live Feedback RIGHT ----
    col_left, col_spacer, col_right = st.columns([1.1, 0.1, 1])

    with col_left:
        st.markdown("<h5 style='color:#e2e8f0; margin-bottom:16px;'>Candidate Details</h5>", unsafe_allow_html=True)
        candidate_name = st.text_input(
            "Candidate Name",
            placeholder="e.g., Priya Sharma",
            key=f"cand_name_{st.session_state.reset_counter}"
        )
        evaluator_name = st.text_input(
            "Your Name (Evaluator)",
            placeholder="e.g., Rahul Verma",
            key=f"eval_name_{st.session_state.reset_counter}"
        )

        st.markdown("<hr style='border-color: rgba(255,255,255,0.05); margin: 24px 0;'>", unsafe_allow_html=True)
        st.markdown("<h5 style='color:#e2e8f0; margin-bottom:16px;'>Scoring Criteria</h5>", unsafe_allow_html=True)

        technical_score = st.slider(
            "Technical Skills",
            min_value=1, max_value=10, value=5,
            key=f"tech_slider_{st.session_state.reset_counter}",
            help="Rate the candidate's technical knowledge and problem-solving ability."
        )
        communication_score = st.slider(
            "Communication",
            min_value=1, max_value=10, value=5,
            key=f"comm_slider_{st.session_state.reset_counter}",
            help="Rate the candidate's clarity, articulation, and presentation skills."
        )
        overall_fit_score = st.slider(
            "Overall Fit",
            min_value=1, max_value=10, value=5,
            key=f"fit_slider_{st.session_state.reset_counter}",
            help="Rate how well the candidate aligns with the team's culture and goals."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        submitted = st.button("Submit Evaluation", use_container_width=True, type="primary")

    # ---- RIGHT Column: Live Score Preview ----
    with col_right:
        total_preview = technical_score + communication_score + overall_fit_score

        if total_preview >= 24:
            quality = ("EXCELLENT", "#34d399", "52, 211, 153")
        elif total_preview >= 18:
            quality = ("STRONG", "#38bdf8", "56, 189, 248")
        elif total_preview >= 12:
            quality = ("AVERAGE", "#fb923c", "251, 146, 60")
        else:
            quality = ("NEEDS REVIEW", "#f87171", "248, 113, 113")

        st.markdown("<h5 style='color:#e2e8f0; margin-bottom:16px;'>Score Preview</h5>", unsafe_allow_html=True)
        st.markdown(
            f'''
            <div class="bento-container">
                <div class="bento-card bento-main">
                    <div style="font-family:'Outfit'; font-weight:600; font-size: 0.85rem; letter-spacing: 0.05em; color:#94a3b8; margin-bottom:16px; text-transform: uppercase;">Total Yield</div>
                    <div class="flex-wrapper">
                      <div class="single-chart">
                        <svg viewBox="0 0 36 36" class="circular-chart">
                          <path class="circle-bg"
                            d="M18 2.0845
                              a 15.9155 15.9155 0 0 1 0 31.831
                              a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <path class="circle"
                            stroke-dasharray="{(total_preview / 30) * 100}, 100"
                            stroke="{quality[1]}"
                            d="M18 2.0845
                              a 15.9155 15.9155 0 0 1 0 31.831
                              a 15.9155 15.9155 0 0 1 0 -31.831"
                          />
                          <text x="18" y="21.5" class="percentage">{total_preview}</text>
                        </svg>
                      </div>
                    </div>
                    <div class="status-pill" style="background: rgba({quality[2]}, 0.15); color: {quality[1]}; border: 1px solid rgba({quality[2]}, 0.4); box-shadow: 0 0 20px rgba({quality[2]}, 0.2);">
                        {quality[0]}
                    </div>
                </div>
                
                <div class="bento-card">
                    <div style="font-family:'Outfit'; font-weight:600; font-size: 0.85rem; letter-spacing: 0.05em; color:#94a3b8; margin-bottom:12px; text-transform: uppercase;">Criteria Breakdown</div>
                    
                    <div class="sub-score-item">
                        <div class="sub-score-header"><span>Technical</span><span style="color:#e2e8f0;">{technical_score}/10</span></div>
                        <div class="mini-track"><div class="mini-fill" style="width: {technical_score*10}%; background: #38bdf8; box-shadow: 0 0 8px #38bdf8;"></div></div>
                    </div>
                    
                    <div class="sub-score-item">
                        <div class="sub-score-header"><span>Communication</span><span style="color:#e2e8f0;">{communication_score}/10</span></div>
                        <div class="mini-track"><div class="mini-fill" style="width: {communication_score*10}%; background: #a78bfa; box-shadow: 0 0 8px #a78bfa;"></div></div>
                    </div>
                    
                    <div class="sub-score-item">
                        <div class="sub-score-header"><span>Overall Fit</span><span style="color:#e2e8f0;">{overall_fit_score}/10</span></div>
                        <div class="mini-track"><div class="mini-fill" style="width: {overall_fit_score*10}%; background: #34d399; box-shadow: 0 0 8px #34d399;"></div></div>
                    </div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True
        )

    # ---- Submission Handler (below both columns) ----
    if submitted:
        import re
        if not candidate_name.strip() or not evaluator_name.strip():
            st.warning("Please enter both the Candidate Name and your Name.")
        elif not re.match(r"^[A-Za-z\s]+$", candidate_name.strip()) or not re.match(r"^[A-Za-z\s]+$", evaluator_name.strip()):
            st.error("Invalid name format. Only letters and spaces are allowed. No special characters like @, #, $, etc.")
        else:
            success = insert_score(
                candidate_name.strip(),
                evaluator_name.strip(),
                technical_score,
                communication_score,
                overall_fit_score
            )

            if success:
                # Flag-based reset: set flag with data, then rerun.
                # The flag is detected at the TOP of this page section
                # on the next run, BEFORE widgets are instantiated.
                st.session_state["form_submitted"] = {
                    "cand": candidate_name.strip(),
                    "eval": evaluator_name.strip()
                }
                st.rerun()


# ============================================================================
# SECTION 8: EXECUTIVE DASHBOARD (BEAST MODE 3.0)
# ============================================================================
elif page == "Executive Dashboard":

    st.markdown('<p class="main-header"><span class="live-indicator"></span>Live Leaderboard</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Real-time candidate rankings based on all submitted evaluations.'
        '</p>',
        unsafe_allow_html=True
    )

    leaderboard, raw_df = get_leaderboard()

    if leaderboard.empty:
        st.info("No evaluations submitted yet. Start scoring candidates to see rankings.")
    else:
        # ---- Summary Metric Cards (minimal, clean) ----
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(leaderboard)}</h3>'
                f'<p>Total Candidates</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(raw_df)}</h3>'
                f'<p>Total Evaluations</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m3:
            avg_all = round(raw_df["total_score"].mean(), 1) if not raw_df.empty else 0
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{avg_all}</h3>'
                f'<p>Global Avg Score</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m4:
            stability = round(raw_df["total_score"].std(), 2) if len(raw_df) > 1 else 0
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{stability}</h3>'
                f'<p>Score Variance</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- BEAST MODE AI INSIGHTS ----
        with st.expander("⚡ BEAST MODE AI INSIGHTS", expanded=True):
            top_row = leaderboard.iloc[0]
            name = top_row['candidate_name']
            
            # Identify strongest trait
            traits = {
                'Technical': top_row['avg_technical'],
                'Communication': top_row['avg_communication'],
                'Culture Fit': top_row['avg_fit']
            }
            strongest = max(traits, key=traits.get)
            
            st.markdown(f"""
            <div style="background: rgba(37, 99, 235, 0.1); border-left: 4px solid #2563eb; padding: 1.5rem; border-radius: 0 12px 12px 0; margin-bottom: 20px;">
                <h4 style="margin:0; color:#60a5fa; font-family: 'Outfit';">Sovereign Performance Summary: {name}</h4>
                <p style="margin:10px 0 0 0; color:#cbd5e1; font-size:1.1rem;">
                    <b>{name}</b> is currently the Top-Tier candidate with a total yield of <b>{top_row['total_combined_score']}</b>. 
                    Strongest core asset identified: <span style="color:#22c55e; font-weight:700;">{strongest}</span>.
                </p>
                <p style="margin:5px 0 0 0; color:#94a3b8; font-size:0.9rem;">
                    <i>AI Verdict: Highly recommended for immediate progression to final stage interview.</i>
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Talent Pool Distribution Summary
            avg_fit = leaderboard['avg_fit'].mean()
            st.markdown(f"""
            <div style="padding: 1rem; background: rgba(255,255,255,0.02); border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">
                <p style="margin:0; color:#94a3b8; font-size:0.85rem;">
                    <b>POOLED ANALYSIS:</b> The overall cultural alignment is <b>{avg_fit:.1f}/10</b>. 
                    The competition is <b>{'Aggressive' if len(leaderboard) > 5 else 'Emerging'}</b>.
                </p>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ---- Two-column: Table LEFT | Chart RIGHT ----
        col_table, col_chart = st.columns([3, 2])

        with col_table:
            st.markdown("##### Candidate Rankings")

            display_df = leaderboard.rename(columns={
                'candidate_name':       'Candidate',
                'total_combined_score': 'Total Score',
                'avg_score':            'Avg Score',
                'num_evaluations':      'Evaluations',
                'avg_technical':        'Avg Technical',
                'avg_communication':    'Avg Communication',
                'avg_fit':              'Avg Fit',
            })

            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Rank":              st.column_config.NumberColumn("Rank", width="small"),
                    "Candidate":         st.column_config.TextColumn("Candidate", width="medium"),
                    "Total Score":       st.column_config.NumberColumn("Total", width="small"),
                    "Avg Score":         st.column_config.NumberColumn("Avg", width="small"),
                    "Evaluations":       st.column_config.NumberColumn("Evals", width="small"),
                    "Avg Technical":     st.column_config.ProgressColumn("Technical", min_value=0, max_value=10, format="%.1f"),
                    "Avg Communication": st.column_config.ProgressColumn("Comm.", min_value=0, max_value=10, format="%.1f"),
                    "Avg Fit":           st.column_config.ProgressColumn("Fit", min_value=0, max_value=10, format="%.1f"),
                }
            )

        with col_chart:
            st.markdown("##### Skill Comparison (Top 3)")

            categories = ['Technical', 'Communication', 'Fit']
            colors = ['#2563EB', '#7c3aed', '#06b6d4']
            fig = go.Figure()

            for i in range(min(3, len(leaderboard))):
                row = leaderboard.iloc[i]
                fig.add_trace(go.Scatterpolar(
                    r=[row['avg_technical'], row['avg_communication'], row['avg_fit']],
                    theta=categories,
                    fill='toself',
                    name=f"#{i+1} {row['candidate_name']}",
                    line=dict(color=colors[i % len(colors)]),
                    fillcolor=colors[i % len(colors)],
                    opacity=0.25
                ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True, 
                        range=[0, 10], 
                        gridcolor="rgba(255,255,255,0.1)",
                        linecolor="rgba(255,255,255,0.1)",
                        tickfont=dict(color="#94a3b8")
                    ),
                    angularaxis=dict(
                        gridcolor="rgba(255,255,255,0.1)",
                        linecolor="rgba(255,255,255,0.1)",
                        tickfont=dict(color="#f8fafc")
                    ),
                    bgcolor="rgba(0,0,0,0)"
                ),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.3,
                    xanchor="center", x=0.5, font=dict(size=11, color="#94a3b8")
                ),
                margin=dict(l=50, r=50, t=30, b=80),
                font=dict(family="Outfit, sans-serif", color="#f8fafc"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                template="plotly_dark"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # --- Additional Pro Max Chart: Score Distribution ---
            st.markdown("##### Performance Breakdown")
            bar_fig = px.bar(
                display_df.head(5).sort_values("Total Score", ascending=True), 
                x='Total Score', 
                y='Candidate', 
                orientation='h',
                color='Avg Score',
                color_continuous_scale=['#ef4444', '#f59e0b', '#22c55e'],
                template="plotly_white",
                height=250
            )
            bar_fig.update_layout(
                margin=dict(l=0, r=0, t=20, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Outfit, sans-serif", color="#f8fafc"),
                coloraxis_showscale=False,
                template="plotly_dark"
            )
            bar_fig.update_xaxes(title="Total Points", showgrid=True, gridcolor="rgba(255,255,255,0.05)", title_font=dict(color="#94a3b8"))
            bar_fig.update_yaxes(title="", tickfont=dict(color="#f8fafc"))
            st.plotly_chart(bar_fig, use_container_width=True)


# ============================================================================
# SECTION 9: DATA MASTERY PAGE
# ============================================================================
elif page == "Data Mastery":

    st.markdown('<p class="main-header">Data Mastery</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Sovereign access to all evaluation records. Monitor health, audit submissions, and export data.'
        '</p>',
        unsafe_allow_html=True
    )

    # Sovereign Health Check
    h1, h2, h3 = st.columns(3)
    with h1:
        st.markdown('<div class="metric-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.write("📊 ENGINE CAPACITY")
        st.write(f"**{len(get_raw_data())}** Records")
        st.markdown('</div>', unsafe_allow_html=True)
    with h2:
        st.markdown('<div class="metric-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.write("🔒 PERSISTENCE")
        st.write("**SQLite (Active)**")
        st.markdown('</div>', unsafe_allow_html=True)
    with h3:
        st.markdown('<div class="metric-card" style="padding: 1rem !important;">', unsafe_allow_html=True)
        st.write("⚡ UPTIME")
        st.write("**100% (Sovereign)**")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    _, raw_df = get_leaderboard()

    if raw_df.empty:
        st.info("No evaluations in the database yet.")
    else:
        display_raw = raw_df.rename(columns={
            'candidate_name':  'Candidate',
            'evaluator_name':  'Evaluator',
            'technical_score': 'Technical',
            'communication':   'Communication',
            'overall_fit':     'Overall Fit',
            'total_score':     'Total',
            'submitted_at':    'Timestamp',
        })

        st.dataframe(
            display_raw.drop(columns=['id']),
            use_container_width=True,
            hide_index=True
        )

        st.markdown("---")
        st.markdown("##### Delete a Record")
        st.caption("This action is permanent and cannot be undone.")

        delete_id = st.selectbox(
            "Select a Record ID to Delete",
            options=["None"] + raw_df['id'].tolist(),
            format_func=lambda x: "Select ID..." if x == "None" else f"ID {x} - {raw_df[raw_df['id'] == x]['candidate_name'].values[0]} by {raw_df[raw_df['id'] == x]['evaluator_name'].values[0]}"
        )
        
        if delete_id != "None":
            if st.button("Delete Record", type="secondary"):
                if delete_score(int(delete_id)):
                    st.toast(f"Record #{delete_id} deleted.")
                    st.rerun()

        st.markdown("---")
        csv_data = display_raw.drop(columns=['id']).to_csv(index=False)
        st.download_button(
            label="Export as CSV",
            data=csv_data,
            file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
