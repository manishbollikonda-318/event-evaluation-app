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
    /* Google Fonts Integration */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;800&display=swap');

    /* Global Overrides */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background: radial-gradient(circle at top left, #0f172a 0%, #020617 100%) !important;
        color: #f8fafc !important;
    }

    /* Transparent Sidebar with Blur */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        min-width: 300px !important;
    }

    [data-testid="stSidebarNav"] {
        background-color: transparent !important;
    }

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: #94a3b8 !important;
        font-weight: 500;
        font-size: 1rem;
    }

    /* Typography: Beast Mode Headers */
    .main-header {
        font-family: 'Outfit', sans-serif;
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(to right, #60a5fa, #2563eb);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
        letter-spacing: -0.02em;
        filter: drop-shadow(0 10px 20px rgba(37, 99, 235, 0.2));
    }

    .sub-header {
        font-size: 1.25rem;
        color: #94a3b8;
        margin-bottom: 3rem;
        font-weight: 300;
        line-height: 1.6;
    }

    /* Glassmorphism 2.0 Cards */
    .metric-card, .stMetric, div[data-testid="stForm"], .score-preview, .tutorial-card {
        background: rgba(30, 41, 59, 0.4) !important;
        backdrop-filter: blur(12px) !important;
        -webkit-backdrop-filter: blur(12px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 24px !important;
        padding: 1.5rem !important;
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3) !important;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    .metric-card:hover, div[data-testid="stForm"]:hover {
        transform: translateY(-8px);
        border-color: rgba(59, 130, 246, 0.3) !important;
        box-shadow: 0 30px 60px rgba(59, 130, 246, 0.1) !important;
        background: rgba(30, 41, 59, 0.6) !important;
    }

    .metric-card h3 {
        color: #60a5fa !important;
        font-family: 'Outfit', sans-serif;
        font-size: 2.8rem !important;
        margin: 0 !important;
        font-weight: 800 !important;
    }

    .metric-card p {
        color: #94a3b8 !important;
        font-size: 0.85rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.15em !important;
        margin: 0.5rem 0 0 0 !important;
        font-weight: 700 !important;
    }

    /* Premium Button Stack */
    .stButton > button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important;
        border: none !important;
        padding: 0.8rem 2rem !important;
        border-radius: 14px !important;
        font-weight: 700 !important;
        width: 100% !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2) !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-family: 'Outfit', sans-serif !important;
    }

    .stButton > button:hover {
        transform: scale(1.02) !important;
        box-shadow: 0 15px 30px rgba(37, 99, 235, 0.4) !important;
        filter: brightness(1.1);
    }

    /* Slider Beast Mode */
    .stSlider label p {
        color: #f8fafc !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
    }
    
    /* Live Indicator */
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background: #22c55e;
        border-radius: 50%;
        margin-right: 12px;
        box-shadow: 0 0 15px rgba(34, 197, 94, 0.6);
        animation: beacon 2s infinite;
    }

    @keyframes beacon {
        0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); }
        70% { transform: scale(1.2); opacity: 0.8; box-shadow: 0 0 0 15px rgba(34, 197, 94, 0); }
        100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); }
    }

    /* Success Popup */
    .custom-popup {
        position: fixed;
        top: 30px;
        right: 30px;
        background: rgba(16, 185, 129, 0.95);
        backdrop-filter: blur(10px);
        color: white;
        padding: 1.5rem 2.5rem;
        border-radius: 20px;
        box-shadow: 0 30px 60px rgba(0,0,0,0.5);
        z-index: 9999;
        border: 1px solid rgba(255,255,255,0.2);
        animation: slideInRight 0.6s cubic-bezier(0.23, 1, 0.32, 1) both, fadeOut 0.5s 4.5s forwards;
    }

    @keyframes slideInRight {
        0% { transform: translateX(100%); opacity: 0; }
        100% { transform: translateX(0); opacity: 1; }
    }

    @keyframes fadeOut {
        to { opacity: 0; transform: translateY(-20px); }
    }

    /* Mobile UX */
    @media (max-width: 768px) {
        .main-header { font-size: 2.2rem; margin-top: 2rem !important; }
        .block-container { padding: 2rem 1rem !important; }
        [data-testid="stSidebar"] { width: 85% !important; }
    }

    /* Scrollbar */
    ::-webkit-scrollbar { width: 8px; }
    ::-webkit-scrollbar-track { background: rgba(0,0,0,0.1); }
    ::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.1); border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(255,255,255,0.2); }

    /* Hide UI Noise */
    #MainMenu, footer, header { visibility: hidden; }
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
                    st.experimental_rerun()
            with b_right:
                if st.button("Next", key="tut_next", type="primary",
                             use_container_width=True):
                    st.session_state.tutorial_step += 1
                    st.experimental_rerun()

        elif current < total - 1:
            # Middle steps: Back | Skip | Next
            b1, b2, b3 = st.columns(3)
            with b1:
                if st.button("Back", key="tut_back",
                             use_container_width=True):
                    st.session_state.tutorial_step -= 1
                    st.experimental_rerun()
            with b2:
                if st.button("Skip", key="tut_skip",
                             use_container_width=True):
                    st.session_state.tutorial_done = True
                    st.experimental_rerun()
            with b3:
                if st.button("Next", key="tut_next", type="primary",
                             use_container_width=True):
                    st.session_state.tutorial_step += 1
                    st.experimental_rerun()

        else:
            # Last step: Back | Get Started
            b_left, b_right = st.columns(2)
            with b_left:
                if st.button("Back", key="tut_back",
                             use_container_width=True):
                    st.session_state.tutorial_step -= 1
                    st.experimental_rerun()
            with b_right:
                if st.button("Get Started", key="tut_finish", type="primary",
                             use_container_width=True):
                    st.session_state.tutorial_done = True
                    st.experimental_rerun()

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
        
        # Render a beautiful custom animated popup
        st.markdown(f"""
        <style>
        .custom-popup {{
            position: fixed;
            top: -150px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(59, 130, 246, 0.5);
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
            padding: 20px 30px;
            border-radius: 24px;
            z-index: 1000000;
            width: 90%;
            max-width: 400px;
            display: flex;
            align-items: center;
            gap: 20px;
            animation: popupBeast 3s cubic-bezier(0.23, 1, 0.32, 1) forwards;
            font-family: 'Outfit', sans-serif;
        }}
        @keyframes popupBeast {{
            0%   {{ top: -150px; opacity: 0; transform: translateX(-50%) scale(0.9); }}
            15%  {{ top: 40px; opacity: 1; transform: translateX(-50%) scale(1); }}
            85%  {{ top: 40px; opacity: 1; transform: translateX(-50%) scale(1); }}
            100% {{ top: -150px; opacity: 0; transform: translateX(-50%) scale(0.9); }}
        }}
        .popup-icon {{
            background: linear-gradient(135deg, #22c55e, #10b981);
            width: 50px; height: 50px;
            border-radius: 15px;
            display: flex; align-items: center; justify-content: center;
            font-size: 24px;
            box-shadow: 0 10px 20px rgba(34, 197, 94, 0.3);
        }}
        .popup-text h4 {{ margin: 0; color: white; font-size: 1.1rem; font-weight: 700; }}
        .popup-text p {{ margin: 4px 0 0 0; color: #94a3b8; font-size: 0.9rem; }}
        </style>
        <div class="custom-popup">
            <div class="popup-icon">✅</div>
            <div class="popup-text">
                <h4>Submission Recorded</h4>
                <p><b>{eval_name_display}</b> successfully evaluated <b>{cand_name_display}</b></p>
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
                st.experimental_rerun()


# ============================================================================
# SECTION 8: LIVE LEADERBOARD PAGE
# ============================================================================
# Layout: Metric summary cards on top, then LEFT = Ranking Table,
# RIGHT = Radar Chart for visual analysis.
# ============================================================================

elif page == "Live Leaderboard":

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
                    st.experimental_rerun()

        st.markdown("---")
        csv_data = display_raw.drop(columns=['id']).to_csv(index=False)
        st.download_button(
            label="Export as CSV",
            data=csv_data,
            file_name=f"evaluations_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
