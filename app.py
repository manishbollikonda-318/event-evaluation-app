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


# ============================================================================
# SECTION 1: DATABASE INITIALIZATION
# ============================================================================
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
def get_leaderboard():
    """
    Queries all scores and aggregates them into a ranked leaderboard.
    """
    conn = sqlite3.connect('evaluations.db', timeout=15)

    raw_df = pd.read_sql_query(
        "SELECT * FROM scores ORDER BY submitted_at DESC",
        conn
    )
    conn.close()

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

init_database()

# ---------- CLEAN LIGHT-MODE DESIGN SYSTEM ----------
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
        font-size: 1.9rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 1.5rem;
    }

    /* ---- Metric Cards: Clean & Minimal ---- */
    .metric-card {
        background: #ffffff;
        border: 1px solid #e5e7eb;
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
        font-size: 2rem;
        font-weight: 700;
        color: #2563EB;
    }
    .metric-card p {
        margin: 0.25rem 0 0 0;
        font-size: 0.8rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #9ca3af;
        font-weight: 500;
    }

    /* ---- Score Preview Card ---- */
    .score-preview {
        background: #f0f4ff;
        border: 1px solid #dbeafe;
        border-radius: 10px;
        padding: 1.5rem;
        text-align: center;
        margin-bottom: 1rem;
    }
    .score-preview .total-number {
        font-size: 3rem;
        font-weight: 700;
        color: #2563EB;
        line-height: 1;
    }
    .score-preview .total-label {
        font-size: 0.85rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-top: 0.3rem;
    }
    .score-breakdown {
        display: flex;
        justify-content: space-around;
        margin-top: 1rem;
        padding-top: 1rem;
        border-top: 1px solid #dbeafe;
    }
    .score-breakdown .item {
        text-align: center;
    }
    .score-breakdown .item .value {
        font-size: 1.4rem;
        font-weight: 600;
        color: #1e40af;
    }
    .score-breakdown .item .label {
        font-size: 0.7rem;
        color: #9ca3af;
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
        font-size: 0.9rem;
        margin: 0.8rem 0;
    }

    /* ---- Sidebar: Light & Clean ---- */
    [data-testid="stSidebar"] {
        background: #f8fafc;
        border-right: 1px solid #e5e7eb;
    }
    [data-testid="stSidebar"] * {
        color: #374151 !important;
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
        background-color: #ffffff !important;
        color: #dc2626 !important;
        border: 1px solid #fecaca !important;
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

    /* ---- Page fade-in ---- */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: fadeIn 0.3s ease-out;
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
        #MainMenu {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header[data-testid="stHeader"] {display: none !important;}
        .block-container {padding-top: 1rem !important;}
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SECTION 6: SIDEBAR NAVIGATION
# ============================================================================
with st.sidebar:
    page = st.radio(
        "Select a view:",
        ["Score Entry", "Live Leaderboard", "Raw Data"],
        label_visibility="collapsed"
    )


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

    # ---- Pre-widget state reset (runs BEFORE any widget is created) ----
    if st.session_state.get("form_submitted", False):
        st.session_state.cand_name = ""
        st.session_state.eval_name = ""
        st.session_state.tech_slider = 5
        st.session_state.comm_slider = 5
        st.session_state.fit_slider = 5
        del st.session_state["form_submitted"]

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
            key="cand_name"
        )
        evaluator_name = st.text_input(
            "Your Name (Evaluator)",
            placeholder="e.g., Rahul Verma",
            key="eval_name"
        )

        st.markdown("---")
        st.markdown("##### Scoring Criteria")

        technical_score = st.slider(
            "Technical Skills",
            min_value=1, max_value=10, value=5,
            key="tech_slider",
            help="Rate the candidate's technical knowledge and problem-solving ability."
        )
        communication_score = st.slider(
            "Communication",
            min_value=1, max_value=10, value=5,
            key="comm_slider",
            help="Rate the candidate's clarity, articulation, and presentation skills."
        )
        overall_fit_score = st.slider(
            "Overall Fit",
            min_value=1, max_value=10, value=5,
            key="fit_slider",
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
                st.toast("Score submitted successfully.")
                # Flag-based reset: set flag, then rerun.
                # The flag is detected at the TOP of this page section
                # on the next run, BEFORE widgets are instantiated.
                st.session_state["form_submitted"] = True
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
                    radialaxis=dict(
                        visible=True, range=[0, 10],
                        gridcolor='#e5e7eb', linecolor='#d1d5db'
                    ),
                    bgcolor='#ffffff',
                    angularaxis=dict(gridcolor='#e5e7eb', linecolor='#d1d5db')
                ),
                showlegend=True,
                legend=dict(
                    orientation="h", yanchor="bottom", y=-0.2,
                    xanchor="center", x=0.5, font=dict(size=11)
                ),
                margin=dict(l=50, r=50, t=30, b=60),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#ffffff",
                font=dict(color="#374151", family="Inter, sans-serif")
            )
            st.plotly_chart(fig, use_container_width=True)


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

        for idx, row in raw_df.iterrows():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.text(
                    f"{row['candidate_name']} by {row['evaluator_name']} "
                    f"| Total: {row['total_score']} | {row['submitted_at']}"
                )
            with col_btn:
                if st.button("Delete", key=f"del_{row['id']}", type="secondary"):
                    if delete_score(int(row['id'])):
                        st.toast(f"Record #{row['id']} deleted.")
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
