"""
==============================================================================
 EVENT EVALUATION APP — College Club Recruitment & Event Scoring Platform
==============================================================================
 A single-file Streamlit + SQLite application that replaces spreadsheet-based
 evaluation with a structured, real-time scoring system.

 Run with:  streamlit run app.py
 Requires:  pip install streamlit pandas
==============================================================================
"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime


# ============================================================================
# SECTION 1: DATABASE INITIALIZATION
# ============================================================================
# We use SQLite — a lightweight, file-based relational database that ships
# with Python's standard library (no extra install needed).
#
# The function below creates the database file ('evaluations.db') and the
# 'scores' table if they don't already exist. This is safe to call every
# time the app starts because of the "IF NOT EXISTS" clause.
# ============================================================================

def init_database():
    """
    Creates the SQLite database and the 'scores' table.

    TABLE STRUCTURE:
    ┌────────────────────────────────────────────────────────────────┐
    │                         scores                                 │
    ├──────────────────┬─────────┬───────────────────────────────────┤
    │ Column           │ Type    │ Purpose                           │
    ├──────────────────┼─────────┼───────────────────────────────────┤
    │ id               │ INTEGER │ Auto-incrementing primary key     │
    │ candidate_name   │ TEXT    │ Name of the person being scored   │
    │ evaluator_name   │ TEXT    │ Name of the judge/evaluator       │
    │ technical_score  │ INTEGER │ Technical ability rating (1-10)   │
    │ communication    │ INTEGER │ Communication skills rating (1-10)│
    │ overall_fit      │ INTEGER │ Cultural/team fit rating (1-10)   │
    │ total_score      │ INTEGER │ Sum of all three criteria         │
    │ submitted_at     │ TEXT    │ Timestamp of when score was saved │
    └──────────────────┴─────────┴───────────────────────────────────┘

    HOW IT WORKS (for explaining to your senior):
    -----------------------------------------------
    1. sqlite3.connect('evaluations.db')
       → Opens (or creates) a file called 'evaluations.db' in the same
         directory as this script. This IS the entire database — one file.

    2. cursor = conn.cursor()
       → A cursor is like a "pointer" that lets us send SQL commands to
         the database and read results back.

    3. CREATE TABLE IF NOT EXISTS scores (...)
       → This SQL command defines the table structure. "IF NOT EXISTS"
         means it only creates the table the first time — on subsequent
         runs, it safely does nothing.

    4. conn.commit()
       → Saves the changes to disk. Without this, the table creation
         would be lost when the connection closes.

    5. conn.close()
       → Releases the database file so other parts of the app can use it.
    """

    # Step 1: Open a connection to the SQLite database file
    conn = sqlite3.connect('evaluations.db')

    # Step 2: Create a cursor object to execute SQL commands
    cursor = conn.cursor()

    # Step 3: Execute the CREATE TABLE statement
    # - "id INTEGER PRIMARY KEY AUTOINCREMENT" means SQLite will automatically
    #   assign a unique ID (1, 2, 3, ...) to each new row — we never set this manually.
    # - "NOT NULL" means the field is required — the database will reject inserts
    #   that leave these fields empty.
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

    # Step 4: Commit (save) the transaction to disk
    conn.commit()

    # Step 5: Close the connection
    conn.close()


# ============================================================================
# SECTION 2: DATABASE INSERT OPERATION
# ============================================================================
# This function takes the form data and writes it as a new row in the
# 'scores' table. It uses PARAMETERIZED QUERIES (the ? placeholders)
# to prevent SQL injection attacks.
# ============================================================================

def insert_score(candidate_name, evaluator_name, technical, communication, fit):
    """
    Inserts a single evaluation record into the 'scores' table.

    HOW THE INSERT WORKS (for explaining to your senior):
    ------------------------------------------------------
    1. We calculate 'total_score' in Python before inserting.
       This is a DENORMALIZATION — we store a computed value to avoid
       recalculating it on every leaderboard query. The trade-off is
       slightly redundant data for much faster reads.

    2. The INSERT statement uses "?" placeholders instead of f-strings:
       SAFE:     cursor.execute("INSERT ... VALUES (?, ?, ?)", (a, b, c))
       UNSAFE:   cursor.execute(f"INSERT ... VALUES ('{a}', '{b}', '{c}')")

       The safe version prevents SQL injection — a security attack where
       a malicious user types SQL commands into the form fields.

    3. conn.commit() is called AFTER the insert to make it permanent.
       If the app crashes between execute() and commit(), the row is
       NOT saved — this is the "Atomicity" part of ACID guarantees.

    Parameters:
        candidate_name (str): Name of the candidate being evaluated
        evaluator_name (str): Name of the evaluator submitting the score
        technical (int):      Technical score (1-10)
        communication (int):  Communication score (1-10)
        fit (int):            Overall fit score (1-10)

    Returns:
        bool: True if insert succeeded, False if it failed
    """

    # Calculate the total score (sum of all three criteria)
    total_score = technical + communication + fit

    # Record the exact time of submission for the audit trail
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Open a fresh connection for this write operation
        conn = sqlite3.connect('evaluations.db')
        cursor = conn.cursor()

        # Execute the parameterized INSERT statement
        # Each "?" corresponds to one value in the tuple, in order:
        #   ?1 = candidate_name
        #   ?2 = evaluator_name
        #   ?3 = technical
        #   ?4 = communication
        #   ?5 = fit
        #   ?6 = total_score (calculated above)
        #   ?7 = timestamp
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

        # Commit the transaction — this makes the insert permanent on disk
        conn.commit()
        conn.close()
        return True

    except Exception as e:
        # If anything goes wrong, print the error and return False
        st.error(f"Database error: {e}")
        return False


# ============================================================================
# SECTION 3: DATABASE READ + PANDAS AGGREGATION
# ============================================================================
# This function reads ALL scores from the database into a Pandas DataFrame,
# then uses groupby().agg() to compute per-candidate statistics.
# ============================================================================

def get_leaderboard():
    """
    Queries all scores and aggregates them into a ranked leaderboard.

    HOW THE PANDAS AGGREGATION WORKS (for explaining to your senior):
    ------------------------------------------------------------------
    1. pd.read_sql_query(query, conn)
       → Executes a SQL SELECT and loads the result directly into a
         Pandas DataFrame. This is the bridge between SQL and Python.

    2. df.groupby('candidate_name')
       → Groups all rows by candidate name. If "Alice" was scored by
         3 different evaluators, those 3 rows become one group.

    3. .agg({ 'total_score': ['sum', 'mean', 'count'] })
       → For each group (each candidate), compute THREE statistics:
         - 'sum':   Total of all evaluators' scores combined
         - 'mean':  Average score across all evaluators
         - 'count': How many evaluators scored this candidate

       Example:
       ┌───────────┬─────────┬────────────┬──────────────┬───────┐
       │ Candidate │ Eval. 1 │ Eval. 2    │ Total (sum)  │ Mean  │
       ├───────────┼─────────┼────────────┼──────────────┼───────┤
       │ Alice     │ 24      │ 27         │ 51           │ 25.5  │
       │ Bob       │ 18      │ 21         │ 39           │ 19.5  │
       └───────────┴─────────┴────────────┴──────────────┴───────┘

    4. .sort_values(('total_score', 'sum'), ascending=False)
       → Sorts candidates by their total combined score, highest first.
         This produces the final leaderboard ranking.

    5. .reset_index()
       → Converts the grouped result back into a regular DataFrame
         with a simple integer index (0, 1, 2, ...) for clean display.

    Returns:
        tuple: (leaderboard_df, raw_scores_df)
               - leaderboard_df: Aggregated, ranked DataFrame
               - raw_scores_df:  All individual score entries
    """

    conn = sqlite3.connect('evaluations.db')

    # Read the entire scores table into a Pandas DataFrame
    # This is equivalent to: SELECT * FROM scores ORDER BY submitted_at DESC
    raw_df = pd.read_sql_query(
        "SELECT * FROM scores ORDER BY submitted_at DESC",
        conn
    )

    conn.close()

    # If the database is empty, return empty DataFrames
    if raw_df.empty:
        return pd.DataFrame(), raw_df

    # ---- AGGREGATION PIPELINE ----
    # Step 1: Group all score rows by candidate name
    # Step 2: For the 'total_score' column, calculate sum, mean, and count
    # Step 3: For individual criteria, calculate the average across evaluators
    leaderboard = raw_df.groupby('candidate_name').agg(
        # Total combined score from all evaluators
        total_combined_score=('total_score', 'sum'),

        # Average total score per evaluation
        avg_score=('total_score', 'mean'),

        # Number of evaluators who scored this candidate
        num_evaluations=('total_score', 'count'),

        # Average of each individual criterion across all evaluators
        avg_technical=('technical_score', 'mean'),
        avg_communication=('communication', 'mean'),
        avg_fit=('overall_fit', 'mean'),

    ).sort_values(
        # Sort by total combined score, descending (highest first)
        'total_combined_score', ascending=False

    ).reset_index()

    # Round the averages to 1 decimal place for clean display
    leaderboard['avg_score'] = leaderboard['avg_score'].round(1)
    leaderboard['avg_technical'] = leaderboard['avg_technical'].round(1)
    leaderboard['avg_communication'] = leaderboard['avg_communication'].round(1)
    leaderboard['avg_fit'] = leaderboard['avg_fit'].round(1)

    # Add a rank column (1st, 2nd, 3rd, ...)
    leaderboard.insert(0, 'Rank', range(1, len(leaderboard) + 1))

    return leaderboard, raw_df


# ============================================================================
# SECTION 4: CHECK FOR DUPLICATE SUBMISSIONS
# ============================================================================
# Prevents the same evaluator from scoring the same candidate twice.
# ============================================================================

def check_duplicate(candidate_name, evaluator_name):
    """
    Checks if this evaluator has already scored this candidate.

    Returns:
        bool: True if a duplicate exists, False otherwise
    """
    conn = sqlite3.connect('evaluations.db')
    cursor = conn.cursor()

    # Count how many rows match this exact evaluator-candidate pair
    cursor.execute('''
        SELECT COUNT(*) FROM scores
        WHERE candidate_name = ? AND evaluator_name = ?
    ''', (candidate_name, evaluator_name))

    count = cursor.fetchone()[0]
    conn.close()

    # If count > 0, this evaluator has already scored this candidate
    return count > 0


# ============================================================================
# SECTION 5: STREAMLIT UI — PAGE CONFIGURATION
# ============================================================================
# This section configures the Streamlit page and initializes the database.
# ============================================================================

# Set the browser tab title and page layout
st.set_page_config(
    page_title="Event Evaluation App",
    page_icon="E",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize the database on first run
# (safe to call multiple times — CREATE TABLE IF NOT EXISTS)
init_database()

# ---- CUSTOM STYLING ----
# Inject custom CSS to enhance the default Streamlit look
st.markdown("""
<style>
    /* ---- Main header styling ---- */
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6c757d;
        margin-bottom: 2rem;
    }

    /* ---- Metric cards ---- */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 1rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .metric-card h3 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    .metric-card p {
        margin: 0.3rem 0 0 0;
        font-size: 0.9rem;
        opacity: 0.85;
    }

    /* ---- Success banner ---- */
    .success-banner {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        padding: 1rem 1.5rem;
        border-radius: 10px;
        color: white;
        font-weight: 600;
        font-size: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
    }

    /* ---- Leaderboard rank badges ---- */
    .rank-gold   { color: #FFD700; font-weight: 800; font-size: 1.3rem; }
    .rank-silver { color: #C0C0C0; font-weight: 800; font-size: 1.3rem; }
    .rank-bronze { color: #CD7F32; font-weight: 800; font-size: 1.3rem; }

    /* ---- Sidebar polish ---- */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%);
    }
    [data-testid="stSidebar"] * {
        color: #e0e0e0 !important;
    }

    /* ---- Hide Streamlit branding ---- */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SECTION 6: SIDEBAR NAVIGATION
# ============================================================================
# The sidebar acts as the primary navigation between the two views.
# ============================================================================

with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("---")

    # Radio buttons for page selection
    # Streamlit reruns the entire script on every interaction,
    # so this variable is freshly set on each page load.
    page = st.radio(
        "Select a view:",
        ["Score Entry", "Live Leaderboard", "Raw Data"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("### About")
    st.markdown(
        "This app replaces manual Excel "
        "sheets for evaluating candidates "
        "at college club recruitment events."
    )
    st.markdown(
        f"**Database:** `evaluations.db`  \n"
        f"**Engine:** SQLite + Pandas"
    )


# ============================================================================
# SECTION 7: SCORE ENTRY PAGE
# ============================================================================
# This is the main form where evaluators submit their scores.
# ============================================================================

if page == "Score Entry":

    # ---- Page Header ----
    st.markdown('<p class="main-header">Score Entry</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Evaluate candidates on Technical Skills, Communication, and Overall Fit.'
        '</p>',
        unsafe_allow_html=True
    )

    # ---- Score Entry Form ----
    # st.form() groups inputs together so the app only reruns ONCE
    # when the "Submit" button is clicked (not on every slider change).
    with st.form("score_form", clear_on_submit=True):

        st.markdown("#### Identification")
        col1, col2 = st.columns(2)

        with col1:
            # Text input for the candidate's name
            candidate_name = st.text_input(
                "Candidate Name",
                placeholder="e.g., Priya Sharma"
            )

        with col2:
            # Text input for the evaluator's name
            evaluator_name = st.text_input(
                "Your Name (Evaluator)",
                placeholder="e.g., Rahul Verma"
            )

        st.markdown("---")
        st.markdown("#### Scoring Criteria")

        # Three columns for the three scoring sliders
        col_t, col_c, col_f = st.columns(3)

        with col_t:
            # Slider returns an integer between 1 and 10
            technical_score = st.slider(
                "Technical Skills",
                min_value=1, max_value=10, value=5,
                help="Rate the candidate's technical knowledge and problem-solving ability."
            )

        with col_c:
            communication_score = st.slider(
                "Communication",
                min_value=1, max_value=10, value=5,
                help="Rate the candidate's clarity, articulation, and presentation skills."
            )

        with col_f:
            overall_fit_score = st.slider(
                "Overall Fit",
                min_value=1, max_value=10, value=5,
                help="Rate how well the candidate aligns with the club's culture and goals."
            )

        # Show a live preview of the total score before submission
        total_preview = technical_score + communication_score + overall_fit_score
        st.markdown(f"**Preview — Total Score: `{total_preview}` / 30**")

        # The submit button — clicking this triggers the form submission
        submitted = st.form_submit_button(
            "Submit Evaluation",
            use_container_width=True
        )

    # ---- Form Submission Handler ----
    # This block runs ONLY when the submit button is clicked.
    if submitted:
        # Validation: Ensure both name fields are filled
        if not candidate_name.strip() or not evaluator_name.strip():
            st.warning("Please enter both the Candidate Name and your Name.")

        # Validation: Check for duplicate submissions
        elif check_duplicate(candidate_name.strip(), evaluator_name.strip()):
            st.error(
                f"**Duplicate detected!** "
                f"'{evaluator_name.strip()}' has already evaluated "
                f"'{candidate_name.strip()}'. Each evaluator can only "
                f"score a candidate once."
            )

        else:
            # All validations passed — insert into database
            success = insert_score(
                candidate_name.strip(),
                evaluator_name.strip(),
                technical_score,
                communication_score,
                overall_fit_score
            )

            if success:
                st.markdown(
                    f'<div class="success-banner">'
                    f'Score submitted! {evaluator_name.strip()} -> '
                    f'{candidate_name.strip()} '
                    f'(Total: {total_preview}/30)'
                    f'</div>',
                    unsafe_allow_html=True
                )
                # Trigger a rerun so the leaderboard updates if viewed next
                st.balloons()


# ============================================================================
# SECTION 8: LIVE LEADERBOARD PAGE
# ============================================================================
# Queries the database, aggregates scores with Pandas, and displays
# a ranked leaderboard.
# ============================================================================

elif page == "Live Leaderboard":

    st.markdown('<p class="main-header">Live Leaderboard</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Real-time candidate rankings based on all submitted evaluations.'
        '</p>',
        unsafe_allow_html=True
    )

    # Fetch aggregated leaderboard data from the database
    leaderboard, raw_df = get_leaderboard()

    if leaderboard.empty:
        # No data yet — show a friendly empty state
        st.info("No evaluations have been submitted yet. Go to **Score Entry** to add scores.")

    else:
        # ---- Summary Metrics ----
        # Display key statistics at the top of the leaderboard
        m1, m2, m3, m4 = st.columns(4)

        with m1:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(leaderboard)}</h3>'
                f'<p>Candidates Scored</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        with m2:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{int(raw_df["total_score"].sum())}</h3>'
                f'<p>Total Points Awarded</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        with m3:
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{len(raw_df)}</h3>'
                f'<p>Total Evaluations</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        with m4:
            # Count unique evaluator names
            unique_evaluators = raw_df['evaluator_name'].nunique()
            st.markdown(
                f'<div class="metric-card">'
                f'<h3>{unique_evaluators}</h3>'
                f'<p>Active Evaluators</p>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.markdown("---")

        # ---- Podium: Top 3 Candidates ----
        if len(leaderboard) >= 1:
            st.markdown("### Top Candidates")
            podium_cols = st.columns(min(3, len(leaderboard)))

            medals = ["#1", "#2", "#3"]
            colors = ["#FFD700", "#C0C0C0", "#CD7F32"]

            for i, col in enumerate(podium_cols):
                if i < len(leaderboard):
                    row = leaderboard.iloc[i]
                    with col:
                        st.markdown(
                            f"<div style='text-align:center; padding:1rem; "
                            f"border:2px solid {colors[i]}; border-radius:12px; "
                            f"background: rgba(255,255,255,0.05);'>"
                            f"<span style='font-size:2.5rem;'>{medals[i]}</span><br>"
                            f"<strong style='font-size:1.2rem;'>{row['candidate_name']}</strong><br>"
                            f"<span style='font-size:1.8rem; font-weight:700; color:{colors[i]};'>"
                            f"{int(row['total_combined_score'])}</span><br>"
                            f"<small>from {int(row['num_evaluations'])} evaluation(s) · "
                            f"avg {row['avg_score']}/30</small>"
                            f"</div>",
                            unsafe_allow_html=True
                        )

        st.markdown("---")

        # ---- Full Leaderboard Table ----
        st.markdown("### Full Rankings")

        # Rename columns for display-friendly headers
        display_df = leaderboard.rename(columns={
            'candidate_name':       'Candidate',
            'total_combined_score': 'Total Score',
            'avg_score':            'Avg Score',
            'num_evaluations':      'Evaluations',
            'avg_technical':        'Avg Technical',
            'avg_communication':    'Avg Communication',
            'avg_fit':              'Avg Fit',
        })

        # Display the DataFrame as an interactive, sortable table
        # use_container_width=True makes it fill the page width
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Rank":              st.column_config.NumberColumn("Rank", width="small"),
                "Candidate":         st.column_config.TextColumn("Candidate", width="medium"),
                "Total Score":       st.column_config.NumberColumn("Total", width="small"),
                "Avg Score":         st.column_config.NumberColumn("Avg", width="small"),
                "Evaluations":      st.column_config.NumberColumn("Evals", width="small"),
                "Avg Technical":     st.column_config.ProgressColumn("Technical", min_value=0, max_value=10, format="%.1f"),
                "Avg Communication": st.column_config.ProgressColumn("Communication", min_value=0, max_value=10, format="%.1f"),
                "Avg Fit":           st.column_config.ProgressColumn("Fit", min_value=0, max_value=10, format="%.1f"),
            }
        )

        # ---- Bar Chart: Total Scores ----
        st.markdown("### Score Distribution")
        chart_data = leaderboard.set_index('candidate_name')['total_combined_score']
        st.bar_chart(chart_data, color="#667eea")


# ============================================================================
# SECTION 9: RAW DATA PAGE
# ============================================================================
# Shows every individual score entry — useful for auditing and debugging.
# ============================================================================

elif page == "Raw Data":

    st.markdown('<p class="main-header">Raw Evaluation Data</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">'
        'Complete audit trail of all individual score submissions.'
        '</p>',
        unsafe_allow_html=True
    )

    _, raw_df = get_leaderboard()

    if raw_df.empty:
        st.info("No evaluations recorded yet.")
    else:
        # Show the raw data with clean column names
        display_raw = raw_df.rename(columns={
            'candidate_name':  'Candidate',
            'evaluator_name':  'Evaluator',
            'technical_score': 'Technical',
            'communication':   'Communication',
            'overall_fit':     'Overall Fit',
            'total_score':     'Total',
            'submitted_at':    'Submitted At',
        }).drop(columns=['id'])

        st.dataframe(
            display_raw,
            use_container_width=True,
            hide_index=True
        )

        # ---- Download as CSV ----
        # Convert the DataFrame to CSV format for download
        csv_data = display_raw.to_csv(index=False)
        st.download_button(
            label="Download as CSV",
            data=csv_data,
            file_name=f"evaluations_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
