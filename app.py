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


# ============================================================================
# SECTION 1: DATABASE INITIALIZATION
# ============================================================================
@st.cache_resource
def init_database():
    """
    Creates the SQLite database and the 'scores' table.
    Uses timeout=15 to handle multiple concurrent users safely and
    prevent OperationalError: database is locked.
    """
    conn = sqlite3.connect('evaluations.db', timeout=15)
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
    conn.close()


# ============================================================================
# SECTION 2: DATABASE INSERT OPERATION
# ============================================================================
def insert_score(candidate_name, evaluator_name, technical, communication, fit):
    """
    Inserts a single evaluation record into the 'scores' table.
    timeout=15 prevents 'database is locked' OperationalError when
    multiple evaluators submit simultaneously.
    """
    total_score = technical + communication + fit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = None
    try:
        conn = sqlite3.connect('evaluations.db', timeout=15)
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
        st.error(f"Database busy — please try again in a moment. ({e})")
        return False
    except Exception as e:
        st.error(f"Submission Error: {e}")
        return False
    finally:
        if conn:
            conn.close()


# ============================================================================
# SECTION 3: DATABASE READ + PANDAS AGGREGATION
# ============================================================================
@st.cache_data(ttl=60)
def get_raw_data():
    conn = sqlite3.connect('evaluations.db', timeout=15)
    raw_df = pd.read_sql_query(
        "SELECT * FROM scores ORDER BY submitted_at DESC",
        conn
    )
    conn.close()
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
    Deletes a single evaluation record from the 'scores' table by ID.
    """
    conn = None
    try:
        conn = sqlite3.connect('evaluations.db', timeout=15)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scores WHERE id = ?', (score_id,))
        conn.commit()
        if 'get_raw_data' in globals():
            get_raw_data.clear()
        return True

    except Exception as e:
        st.error(f"Deletion Failed: {e}")
        return False
    finally:
        if conn:
            conn.close()


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
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    /* ---- Global Reset ---- */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* ---- Main Typography ---- */
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        color: #3b82f6; /* Changed from transparent gradient to solid blue for visibility in all themes */
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #9ca3af;
        margin-bottom: 1.5rem;
    }

    /* ---- Metric Cards: Clean & Minimal ---- */
    .metric-card {
        background: transparent;
        border: 1px solid rgba(128, 128, 128, 0.4);
        padding: 1.2rem 1.5rem;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 0.8rem;
        transition: all 0.2s ease;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .metric-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2.4rem;
        font-weight: 700;
        color: #2563EB;
    }
    .metric-card p {
        margin: 0.25rem 0 0 0;
        font-size: 1rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: inherit;
        opacity: 0.8;
        font-weight: 600;
    }

    /* ---- Score Preview Card ---- */
    .score-preview {
        background: transparent;
        border: 1px solid rgba(128, 128, 128, 0.4);
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .score-preview .total-number {
        font-size: 3.5rem;
        font-weight: 700;
        color: #2563EB;
        line-height: 1;
    }
    .score-preview .total-label {
        font-size: 1.1rem;
        color: inherit;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
    .score-breakdown {
        display: flex;
        justify-content: space-around;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid rgba(128, 128, 128, 0.2);
    }
    .score-breakdown .item {
        text-align: center;
    }
    .score-breakdown .item .value {
        font-size: 1.6rem;
        font-weight: 600;
        color: #2563EB;
    }
    .score-breakdown .item .label {
        font-size: 0.9rem;
        color: inherit;
        opacity: 0.8;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    /* ---- Success Banner ---- */
    .success-banner {
        background: #f0fdf4;
        border: 1px solid #bbf7d0;
        border-left: 4px solid #22c55e;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        color: #166534;
        font-weight: 500;
        font-size: 1rem;
        margin: 0.8rem 0;
    }



    /* ---- Primary Button: Solid Blue ---- */
    [data-testid="stAppViewContainer"] .stButton > button[kind="primary"],
    [data-testid="stAppViewContainer"] .stButton > button:not([kind]) {
        background-color: #2563EB !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 0.6rem 1.5rem !important;
        transition: all 0.2s ease !important;
    }
    [data-testid="stAppViewContainer"] .stButton > button[kind="primary"]:hover,
    [data-testid="stAppViewContainer"] .stButton > button:not([kind]):hover {
        background-color: #1d4ed8 !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3) !important;
    }
    /* Secondary buttons (delete) — red outline */
    [data-testid="stAppViewContainer"] .stButton > button[kind="secondary"] {
        background-color: transparent !important;
        color: #dc2626 !important;
        border: 1px solid #dc2626 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    [data-testid="stAppViewContainer"] .stButton > button[kind="secondary"]:hover {
        background-color: #fef2f2 !important;
        box-shadow: 0 2px 6px rgba(220,38,38,0.15) !important;
    }
    /* Download button */
    [data-testid="stDownloadButton"] > button {
        background-color: #2563EB !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
        background-color: #1d4ed8 !important;
    }

    /* ---- Hide Streamlit branding ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ---- Page fade-in disabled to prevent mobile lag ---- */
    .block-container {
        /* animation removed for better performance */
    }

    /* ---- Slider: Blue accent ---- */
    .stSlider > div > div > div > div {
        background: #2563EB !important;
    }
    .stSlider [role="slider"] {
        background-color: #2563EB !important;
        border: 3px solid #ffffff !important;
        box-shadow: 0 1px 4px rgba(37,99,235,0.4) !important;
    }

    /* ---- Mobile Responsiveness ---- */
    @media (max-width: 768px) {
        footer {visibility: hidden !important;}
        .block-container {padding-top: 4rem !important;}
        .score-preview .total-number { font-size: 2.8rem; }
        .score-breakdown { flex-wrap: wrap; gap: 0.5rem; }
    }

    /* ---- Mobile Menu Hint ---- */
    .mobile-menu-hint {
        display: none;
        position: fixed;
        top: 12px;
        left: 60px;
        background: #2563EB;
        color: #ffffff;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        z-index: 9999;
        box-shadow: 0 2px 10px rgba(37,99,235,0.35);
        animation: pulseHint 2s ease-in-out infinite;
        pointer-events: none;
        font-family: 'Inter', sans-serif;
    }
    .mobile-menu-hint::before {
        content: '\2190 ';
        font-size: 0.85rem;
    }
    @keyframes pulseHint {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.8; transform: scale(1.04); }
    }
    @media (max-width: 768px) {
        .mobile-menu-hint { display: block; }
    }

    /* ---- Onboarding Tutorial (Streamlit-native card) ---- */
    .tutorial-wrapper {
        display: flex;
        align-items: center;
        justify-content: center;
        min-height: 60vh;
    }
    .tutorial-card {
        background: transparent;
        border: 1px solid rgba(128, 128, 128, 0.4);
        border-radius: 16px;
        padding: 2.5rem 2rem 2rem;
        max-width: 420px;
        width: 100%;
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
        text-align: center;
        font-family: 'Inter', sans-serif;
    }
    .tutorial-card .step-icon {
        font-size: 3.5rem;
        margin-bottom: 1rem;
        display: block;
    }
    .tutorial-card h3 {
        margin: 0 0 0.6rem 0;
        font-size: 1.5rem;
        font-weight: 700;
        color: inherit;
    }
    .tutorial-card p {
        margin: 0 0 1.5rem 0;
        font-size: 1.1rem;
        color: inherit;
        opacity: 0.8;
        line-height: 1.6;
    }
    .tutorial-dots {
        display: flex;
        justify-content: center;
        gap: 6px;
        margin-bottom: 0.5rem;
    }
    .tutorial-dots .dot {
        width: 8px; height: 8px;
        border-radius: 50%;
        background: #d1d5db;
        transition: all 0.2s ease;
    }
    .tutorial-dots .dot.active {
        background: #2563EB;
        width: 24px;
        border-radius: 4px;
    }
    .tutorial-step-counter {
        font-size: 0.75rem;
        color: #9ca3af;
        margin-top: 0.3rem;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SECTION 6: SIDEBAR NAVIGATION
# ============================================================================
with st.sidebar:
    page = st.radio(
        "Navigation",
        ["Score Entry", "Live Leaderboard", "Raw Data"]
    )


# ============================================================================
# SECTION 6b: MOBILE MENU HINT + ONBOARDING TUTORIAL
# ============================================================================
# Mobile users can't see the sidebar by default. We show:
# 1. A floating blue pill next to the hamburger icon saying "Menu"
# 2. A first-time onboarding tutorial explaining how to use the app.
#
# ARCHITECTURE NOTE:
#   Streamlit cannot reliably layer fixed HTML overlays over its own buttons
#   (z-index conflicts). Instead, we use a Streamlit-native approach:
#   render a centered tutorial card, then call st.stop() to prevent the
#   rest of the app from rendering.  The user must complete or skip the
#   tutorial before they can interact with the main app.
# ============================================================================

# ---- Persistent floating menu hint for mobile (always visible) ----
st.markdown('<div class="mobile-menu-hint">Menu</div>', unsafe_allow_html=True)

# ---- Onboarding Tutorial ----
TUTORIAL_STEPS = [
    {
        "icon": "\U0001F44B",
        "title": "Welcome to the Evaluation App",
        "body": "This quick guide will show you how to score candidates. Takes just 10 seconds."
    },
    {
        "icon": "\u2630",
        "title": "Open the Menu",
        "body": "Tap the menu icon at the top-left corner to switch between Score Entry, Live Leaderboard, and Raw Data."
    },
    {
        "icon": "\U0001F4DD",
        "title": "Submit a Score",
        "body": "Enter the candidate name and your name, drag the sliders to rate them (1-10), then tap Submit Scores."
    },
    {
        "icon": "\U0001F4CA",
        "title": "View the Leaderboard",
        "body": "Open the Menu and select Live Leaderboard to see real-time rankings and comparison charts."
    },
    {
        "icon": "\U0001F680",
        "title": "You're All Set!",
        "body": "That's everything you need. Your scores are saved automatically. Happy evaluating!"
    },
]

# Initialize tutorial state
if "tutorial_done" not in st.session_state:
    st.session_state.tutorial_done = False
if "tutorial_step" not in st.session_state:
    st.session_state.tutorial_step = 0

# Show the tutorial if not dismissed — then st.stop() to block the main app
if not st.session_state.tutorial_done:
    step = TUTORIAL_STEPS[st.session_state.tutorial_step]
    total = len(TUTORIAL_STEPS)
    current = st.session_state.tutorial_step

    # Build dot indicators
    dots_html = ""
    for i in range(total):
        cls = "dot active" if i == current else "dot"
        dots_html += f'<div class="{cls}"></div>'

    # ---- Centered tutorial card (Streamlit-native) ----
    spacer_top, card_col, spacer_bottom = st.columns([1, 2, 1])

    with card_col:
        st.markdown(
            f'<div class="tutorial-wrapper">'
            f'  <div class="tutorial-card">'
            f'    <span class="step-icon">{step["icon"]}</span>'
            f'    <h3>{step["title"]}</h3>'
            f'    <p>{step["body"]}</p>'
            f'    <div class="tutorial-dots">{dots_html}</div>'
            f'    <div class="tutorial-step-counter">STEP {current + 1} OF {total}</div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # ---- Navigation buttons (inside the same column, below the card) ----
        if current == 0:
            # First step: Skip | Next
            b_left, b_right = st.columns(2)
            with b_left:
                if st.button("Skip Tutorial", key="tut_skip",
                             use_container_width=True):
                    st.session_state.tutorial_done = True
                    st.rerun()
            with b_right:
                if st.button("Next", key="tut_next", type="primary",
                             use_container_width=True):
                    st.session_state.tutorial_step += 1
                    st.rerun()

        elif current < total - 1:
            # Middle steps: Back | Skip | Next
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Back", key="tut_back",
                             use_container_width=True):
                    st.session_state.tutorial_step -= 1
                    st.rerun()
            with b2:
                if st.button("Skip", key="tut_skip",
                             use_container_width=True):
                    st.session_state.tutorial_done = True
                    st.rerun()
            with b3:
                if st.button("Next", key="tut_next", type="primary",
                             use_container_width=True):
                    st.session_state.tutorial_step += 1
                    st.rerun()

        else:
            # Last step: Back | Get Started
            b_left, b_right = st.columns(2)
            with b_left:
                if st.button("Back", key="tut_back",
                             use_container_width=True):
                    st.session_state.tutorial_step -= 1
                    st.rerun()
            with b_right:
                if st.button("Get Started", key="tut_finish", type="primary",
                             use_container_width=True):
                    st.session_state.tutorial_done = True
                    st.rerun()

    # Block the rest of the app from rendering during the tutorial
    st.stop()


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
#     1. On submit  -> set flag to True, call st.rerun()
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
        
        # Render a beautiful custom animated popup
        st.markdown(f"""
        <style>
        .custom-popup {{
            position: fixed;
            bottom: -150px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #1e293b, #0f172a);
            border: 1px solid #3b82f6;
            box-shadow: 0 10px 30px rgba(59, 130, 246, 0.3);
            padding: 16px 24px;
            border-radius: 16px;
            z-index: 999999;
            width: 90%;
            max-width: 350px;
            display: flex;
            align-items: center;
            gap: 16px;
            animation: popupAnim 2.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            font-family: 'Inter', sans-serif;
        }}
        @keyframes popupAnim {{
            0%   {{ bottom: -150px; opacity: 0; }}
            15%  {{ bottom: 40px; opacity: 1; }}
            85%  {{ bottom: 40px; opacity: 1; }}
            100% {{ bottom: -150px; opacity: 0; }}
        }}
        .custom-popup-icon {{
            font-size: 32px;
        }}
        .custom-popup-content {{
            display: flex;
            flex-direction: column;
        }}
        .custom-popup-title {{
            font-weight: 700;
            color: #ffffff;
            margin: 0;
            font-size: 16px;
            line-height: 1.3;
        }}
        .custom-popup-subtitle {{
            color: #94a3b8;
            margin: 4px 0 0 0;
            font-size: 13px;
        }}
        </style>
        <div class="custom-popup">
            <div class="custom-popup-icon">🎉</div>
            <div class="custom-popup-content">
                <p class="custom-popup-title">Thank you, {eval_name_display}!</p>
                <p class="custom-popup-subtitle">Successfully submitted {cand_name_display}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

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
    col_left, col_spacer, col_right = st.columns([3, 0.3, 2])

    with col_left:
        st.markdown("##### Candidate Details")
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

        st.markdown("---")
        st.markdown("##### Scoring Criteria")

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

        st.markdown("")  # spacing

        # ---- Submit Button (renamed from "Transmit Evaluation") ----
        submitted = st.button("Submit Scores", use_container_width=True, type="primary")

    # ---- RIGHT Column: Live Score Preview ----
    with col_right:
        total_preview = technical_score + communication_score + overall_fit_score

        st.markdown("##### Live Score Preview")
        st.markdown(
            f'<div class="score-preview">'
            f'  <div class="total-number">{total_preview}</div>'
            f'  <div class="total-label">out of 30</div>'
            f'  <div class="score-breakdown">'
            f'    <div class="item">'
            f'      <div class="value">{technical_score}</div>'
            f'      <div class="label">Technical</div>'
            f'    </div>'
            f'    <div class="item">'
            f'      <div class="value">{communication_score}</div>'
            f'      <div class="label">Communication</div>'
            f'    </div>'
            f'    <div class="item">'
            f'      <div class="value">{overall_fit_score}</div>'
            f'      <div class="label">Overall Fit</div>'
            f'    </div>'
            f'  </div>'
            f'</div>',
            unsafe_allow_html=True
        )

        # Visual score quality indicator
        if total_preview >= 24:
            quality = ("Excellent", "#22c55e")
        elif total_preview >= 18:
            quality = ("Good", "#2563EB")
        elif total_preview >= 12:
            quality = ("Average", "#f59e0b")
        else:
            quality = ("Below Average", "#ef4444")

        st.markdown(
            f'<p style="text-align:center; margin-top:0.5rem;">'
            f'<span style="background:{quality[1]}; color:white; padding:0.3rem 0.8rem; '
            f'border-radius:20px; font-size:0.8rem; font-weight:600;">'
            f'{quality[0]}</span></p>',
            unsafe_allow_html=True
        )

    # ---- Submission Handler (below both columns) ----
    if submitted:
        if not candidate_name.strip() or not evaluator_name.strip():
            st.warning("Please enter both the Candidate Name and your Name.")
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
# SECTION 8: LIVE LEADERBOARD PAGE
# ============================================================================
# Layout: Metric summary cards on top, then LEFT = Ranking Table,
# RIGHT = Radar Chart for visual analysis.
# ============================================================================

elif page == "Live Leaderboard":

    st.markdown('<p class="main-header">Live Leaderboard</p>', unsafe_allow_html=True)
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
                f'<p>Candidates</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{int(raw_df["total_score"].sum())}</h3>'
                f'<p>Total Points</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(raw_df)}</h3>'
                f'<p>Evaluations</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m4:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{raw_df["evaluator_name"].nunique()}</h3>'
                f'<p>Evaluators</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

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
                    radialaxis=dict(visible=True, range=[0, 10])
                ),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.2,
                    xanchor="center", x=0.5, font=dict(size=11)
                ),
                margin=dict(l=50, r=50, t=30, b=60),
                font=dict(family="Inter, sans-serif"),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)"
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
                margin=dict(l=0, r=0, t=0, b=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif"),
                coloraxis_showscale=False
            )
            bar_fig.update_xaxes(title="Total Points", showgrid=True, gridcolor="rgba(128,128,128,0.2)")
            bar_fig.update_yaxes(title="")
            st.plotly_chart(bar_fig, use_container_width=True)


# ============================================================================
# SECTION 9: RAW DATA PAGE
# ============================================================================
elif page == "Raw Data":

    st.markdown('<p class="main-header">Raw Evaluation Data</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Complete record of all submitted evaluations. Delete or export as needed.'
        '</p>',
        unsafe_allow_html=True
    )

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
