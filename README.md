<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.56+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/Pandas-2.0+-150458?style=for-the-badge&logo=pandas&logoColor=white" alt="Pandas"/>
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">Event Evaluation App</h1>

<p align="center">
  <strong>A real-time candidate scoring platform built to replace Excel sheets at college club recruitment events.</strong>
</p>

<p align="center">
  <a href="#features">Features</a> &middot;
  <a href="#tech-stack">Tech Stack</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#architecture">Architecture</a> &middot;
  <a href="#deployment">Deployment</a> &middot;
  <a href="#contributing">Contributing</a>
</p>

---

## The Problem

College clubs and hackathon organizers still rely on **shared Excel spreadsheets** to evaluate candidates. This creates real, recurring failures:

| Issue | What Happens |
|---|---|
| **Edit Conflicts** | Two evaluators score simultaneously — one silently overwrites the other |
| **No Audit Trail** | A mistyped score is indistinguishable from a deliberate one |
| **Manual Aggregation** | Someone spends 30–60 minutes building SUMIF formulas after judging ends |
| **Single Point of Failure** | One corrupted file can wipe an entire event's data |

## The Solution

**Event Evaluation App** is a single-file Python web application that gives every evaluator a structured, validated scoring form and computes leaderboards instantly — no formulas, no conflicts, no data loss.

---

## Features

### Score Entry
- Clean, validated input form with candidate name, evaluator name, and three scoring criteria
- Sliders (1–10) for **Technical Skills**, **Communication**, and **Overall Fit**
- Live score preview before submission
- **Duplicate detection** — prevents the same evaluator from scoring a candidate twice
- Server-side input validation with clear error messages

### Live Leaderboard
- Real-time ranked standings computed with Pandas aggregation
- Summary metric cards: candidates scored, total points, evaluations count, active evaluators
- **Top 3 podium display** with ranked cards
- Interactive, sortable data table with progress bars for each criterion
- Bar chart visualization of score distribution

### Raw Data & Export
- Full audit trail of every individual score submission with timestamps
- **One-click CSV export** for post-event analysis and record-keeping

### Design
- Dark gradient sidebar with clean navigation
- Gradient metric cards and success banners
- Mobile-responsive layout — evaluators can score from their phones
- Streamlit branding hidden for a professional presentation

---

## Tech Stack

| Layer | Technology | Role |
|---|---|---|
| **Frontend + Backend** | [Streamlit](https://streamlit.io/) | Unified Python framework — reactive UI + server logic in one file |
| **Database** | [SQLite](https://sqlite.org/) | Zero-config, file-based relational database with ACID guarantees |
| **Aggregation** | [Pandas](https://pandas.pydata.org/) | Real-time score grouping, averaging, ranking via `groupby().agg()` |
| **Language** | Python 3.11+ | Single runtime, single codebase, single deployment unit |

**Why this stack?** A solo developer (or small team) can build, understand, and deploy the entire application without touching HTML, CSS, JavaScript, Docker, or a separate database server. The entire app is **one Python file**.

---

## Quick Start

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/manishbollikonda-318/event-evaluation-app.git
cd event-evaluation-app

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run app.py
```

The app will open at **http://localhost:8501**.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     BROWSER (Client)                    │
│                                                         │
│   Evaluator opens the app on phone / laptop / tablet    │
│   Fills scoring form → clicks Submit                    │
│                                                         │
├─────────────────────────┬───────────────────────────────┤
│                         │ HTTP                          │
│                         ▼                               │
├─────────────────────────────────────────────────────────┤
│                  STREAMLIT SERVER                       │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │  Score Entry     │ Leaderboard   │ Raw Data     │   │
│   │  (st.form)       │ (st.dataframe)│ (st.dataframe│   │
│   │                  │ + st.bar_chart│ + CSV export) │   │
│   └──────────────────┴──────────────┴──────────────┘   │
│                         │                               │
│   ┌─────────────────────▼─────────────────────────┐    │
│   │         Pandas Aggregation Engine              │    │
│   │  groupby() → agg(sum, mean, count) → rank()   │    │
│   └─────────────────────┬─────────────────────────┘    │
│                         │ SQL                           │
├─────────────────────────▼───────────────────────────────┤
│                    SQLite (evaluations.db)               │
│                                                         │
│   scores: id | candidate | evaluator | tech | comm |    │
│           fit | total | timestamp                       │
└─────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
event-evaluation-app/
├── app.py               # Complete application (single file)
├── requirements.txt     # Python dependencies
├── .gitignore           # Excludes venv, db, cache
├── README.md            # This file
└── evaluations.db       # Auto-created on first run (gitignored)
```

---

## How It Works

### Database Insert (Simplified)

```python
# Parameterized query prevents SQL injection
cursor.execute('''
    INSERT INTO scores (candidate_name, evaluator_name,
                        technical_score, communication,
                        overall_fit, total_score, submitted_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
''', (candidate, evaluator, tech, comm, fit, total, timestamp))

conn.commit()  # ACID — atomic write to disk
```

### Pandas Aggregation (Simplified)

```python
# Group by candidate → compute stats → sort by total → rank
leaderboard = raw_df.groupby('candidate_name').agg(
    total_combined_score = ('total_score', 'sum'),
    avg_score            = ('total_score', 'mean'),
    num_evaluations      = ('total_score', 'count'),
).sort_values('total_combined_score', ascending=False)
```

---

## Deployment

### Streamlit Community Cloud (Recommended — Free)

1. Push code to GitHub (already done)
2. Go to [share.streamlit.io](https://share.streamlit.io/)
3. Sign in with GitHub → **New App** → Select this repo
4. Set main file to `app.py` → **Deploy**

### Manual Server

```bash
# On any Linux server with Python 3.11+
pip install -r requirements.txt
streamlit run app.py --server.port 80 --server.headless true
```

---

## Configuration

The app works with **zero configuration** out of the box. Optional Streamlit settings can be added in `.streamlit/config.toml`:

```toml
[server]
headless = true
port = 8501

[theme]
primaryColor = "#667eea"
backgroundColor = "#f0f2f6"
secondaryBackgroundColor = "#1a1a2e"
textColor = "#1a1a2e"
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-criteria`)
3. Commit your changes (`git commit -m 'Add new scoring criteria'`)
4. Push to the branch (`git push origin feature/new-criteria`)
5. Open a Pull Request

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

<p align="center">
  Built with Streamlit + SQLite + Pandas<br/>
  <sub>Designed for college clubs, hackathons, and recruitment events</sub>
</p>
