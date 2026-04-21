"""
==============================================================================
 EVENT EVALUATION APP — Enterprise Scoring Platform
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
    Uses timeout=15 to handle multiple concurrent users safely.
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
    """
    total_score = technical + communication + fit
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # timeout=15 prevents "database is locked" errors during simultaneous submissions
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
        ''', (candidate_name, evaluator_name, technical, communication, fit, total_score, timestamp))

        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"System Error: {e}")
        return False


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
    try:
        conn = sqlite3.connect('evaluations.db', timeout=15)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM scores WHERE id = ?', (score_id,))
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        st.error(f"Deletion Failed: {e}")
        return False


# ============================================================================
# SECTION 5: STREAMLIT UI — PAGE CONFIGURATION & ENTERPRISE CSS
# ============================================================================
st.set_page_config(
    page_title="Evaluation Terminal",
    layout="wide",
    initial_sidebar_state="expanded"
)

init_database()

st.markdown("""
<style>
    /* ---- Main Typography ---- */
    .main-header {
        font-size: 2.2rem;
        font-weight: 600;
        color: #e0e0e0;
        margin-bottom: 0.2rem;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    .sub-header {
        font-size: 1rem;
        color: #888888;
        margin-bottom: 2rem;
    }

    /* ---- Enterprise Metric Cards (Bloomberg Style) ---- */
    .metric-card {
        background: #111111;
        border: 1px solid #333333;
        border-left: 4px solid #00ffcc;
        padding: 1.5rem;
        border-radius: 4px;
        color: white;
        text-align: left;
        margin-bottom: 1rem;
        transition: all 0.2s ease;
        cursor: default;
    }
    .metric-card:hover {
        background: #1a1a1a;
        border-left: 4px solid #00ccaa;
        transform: translateY(-2px);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        color: #00ffcc;
        font-family: 'Courier New', Courier, monospace;
    }
    .metric-card p {
        margin: 0.3rem 0 0 0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #888888;
    }

    /* ---- Sidebar polish ---- */
    [data-testid="stSidebar"] {
        background: #0e1117;
        border-right: 1px solid #333333;
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }

    /* ---- Hide Streamlit branding ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* ---- Page fade-in animation ---- */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(5px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    .block-container {
        animation: fadeIn 0.3s ease-out;
    }

    /* ---- Modern slider styling ---- */
    .stSlider > div > div > div > div {
        background: #00ffcc !important;
    }
    .stSlider [role="slider"] {
        background-color: #ffffff !important;
        border: 2px solid #00ffcc !important;
        box-shadow: none !important;
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
# SECTION 7: SCORE ENTRY PAGE (REAL-TIME UPDATES)
# ============================================================================
def clear_form():
    """Callback to clear inputs after submission"""
    st.session_state.cand_name = ""
    st.session_state.eval_name = ""
    st.session_state.tech_slider = 5
    st.session_state.comm_slider = 5
    st.session_state.fit_slider = 5

if page == "Score Entry":
    st.markdown('<p class="main-header">Evaluation Terminal</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">System ready. Awaiting candidate metrics.</p>', unsafe_allow_html=True)

    st.markdown("#### Identity Matrix")
    col1, col2 = st.columns(2)

    with col1:
        candidate_name = st.text_input(
            "Candidate Identifier",
            key="cand_name"
        )

    with col2:
        evaluator_name = st.text_input(
            "Evaluator Identifier",
            key="eval_name"
        )

    st.markdown("---")
    st.markdown("#### Performance Metrics")

    col_t, col_c, col_f = st.columns(3)

    with col_t:
        technical_score = st.slider(
            "Technical Capacity",
            min_value=1, max_value=10, value=5,
            key="tech_slider"
        )

    with col_c:
        communication_score = st.slider(
            "Communication Interface",
            min_value=1, max_value=10, value=5,
            key="comm_slider"
        )

    with col_f:
        overall_fit_score = st.slider(
            "Organizational Fit",
            min_value=1, max_value=10, value=5,
            key="fit_slider"
        )

    total_preview = technical_score + communication_score + overall_fit_score
    
    st.markdown(f"**Computed Total:** <span style='color:#00ffcc; font-size: 1.2rem; font-family: monospace;'>{total_preview}</span> / 30", unsafe_allow_html=True)

    if st.button("Transmit Evaluation", use_container_width=True):
        if not candidate_name.strip() or not evaluator_name.strip():
            st.warning("Identity matrices cannot be empty.")
        else:
            success = insert_score(
                candidate_name.strip(),
                evaluator_name.strip(),
                technical_score,
                communication_score,
                overall_fit_score
            )

            if success:
                # Professional toast notification replaces balloons
                st.toast("Evaluation successfully recorded into database.")
                clear_form()
                st.rerun()


# ============================================================================
# SECTION 8: LIVE LEADERBOARD PAGE
# ============================================================================
elif page == "Live Leaderboard":
    st.markdown('<p class="main-header">Leaderboard Analytics</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Aggregated candidate performance rankings.</p>', unsafe_allow_html=True)

    leaderboard, raw_df = get_leaderboard()

    if leaderboard.empty:
        st.info("System awaiting initial data inputs.")
    else:
        # ---- Summary Metrics ----
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(leaderboard)}</h3>'
                f'<p>Candidates Analyzed</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{int(raw_df["total_score"].sum())}</h3>'
                f'<p>Points Distributed</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m3:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(raw_df)}</h3>'
                f'<p>Data Points</p>'
                f'</div>',
                unsafe_allow_html=True
            )
        with m4:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{raw_df["evaluator_name"].nunique()}</h3>'
                f'<p>Active Evaluators</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # ---- Advanced Plotly Radar Chart ----
        st.markdown("### Top Candidates: Skill Variance Analysis")
        
        categories = ['Technical', 'Communication', 'Fit']
        fig = go.Figure()

        # Add trace for top 3 candidates
        for i in range(min(3, len(leaderboard))):
            row = leaderboard.iloc[i]
            fig.add_trace(go.Scatterpolar(
                r=[row['avg_technical'], row['avg_communication'], row['avg_fit']],
                theta=categories,
                fill='toself',
                name=f"#{i+1} {row['candidate_name']}"
            ))

        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], gridcolor='#333333'),
                bgcolor='rgba(0,0,0,0)',
                angularaxis=dict(gridcolor='#333333')
            ),
            showlegend=True,
            margin=dict(l=40, r=40, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#e0e0e0")
        )
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # ---- Full Leaderboard Table ----
        st.markdown("### Ranking Index")

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
                "Avg Communication": st.column_config.ProgressColumn("Communication", min_value=0, max_value=10, format="%.1f"),
                "Avg Fit":           st.column_config.ProgressColumn("Fit", min_value=0, max_value=10, format="%.1f"),
            }
        )


# ============================================================================
# SECTION 9: RAW DATA PAGE
# ============================================================================
elif page == "Raw Data":
    st.markdown('<p class="main-header">System Audit Log</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Immutable record of all evaluations and deletions.</p>', unsafe_allow_html=True)

    _, raw_df = get_leaderboard()

    if raw_df.empty:
        st.info("System database is empty.")
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
        st.markdown("#### Data Pruning")
        st.caption("WARNING: Deletion removes the evaluation from all aggregations permanently.")

        for idx, row in raw_df.iterrows():
            col_info, col_btn = st.columns([5, 1])
            with col_info:
                st.text(
                    f"{row['candidate_name']} [Authored by: {row['evaluator_name']}] "
                    f"| Total: {row['total_score']} | {row['submitted_at']}"
                )
            with col_btn:
                if st.button("Delete Record", key=f"del_{row['id']}", type="secondary"):
                    if delete_score(int(row['id'])):
                        st.toast(f"Record {row['id']} securely deleted.")
                        st.rerun()

        st.markdown("---")
        csv_data = display_raw.drop(columns=['id']).to_csv(index=False)
        st.download_button(
            label="Export Audit Log (.CSV)",
            data=csv_data,
            file_name=f"evaluation_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
