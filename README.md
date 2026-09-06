# Script Supervisor — AI Screenplay Analysis & Continuity Engine

**Script Supervisor** is an AI-powered screenplay analysis engine and story-world tracking system built for screenwriters, script supervisors, and narrative development teams.

It automatically parses screenplays, extracts structured story memory (characters, facts, events, relationships, and character knowledge), monitors narrative continuity, conducts real-world web research for screenplay claims, and visualizes multi-track plot structure.

---

## 🌟 Key Capabilities & Modules

### 📄 1. Screenplay Document Import & Boundary Detection
* **Format Support**: Upload `.pdf` or `.txt` screenplay files.
* **Deterministic Boundary Parsing**: Detects scene headers, sluglines (`INT.`, `EXT.`), page numbers, and action blocks.
* **Interactive Import Preview**: Review extracted scene boundaries prior to importing. Supports **Append** (add to existing script) or **Replace** (fresh script import) modes.
* **Provenance Tracking**: Preserves exact source document and page number references for every imported scene.

### 🧠 2. Scene Understanding & Extraction Engine
* **Structured Extraction**: Powered by Gemini AI with strict JSON schemas.
* **Entities**: Identifies Characters, Locations, Physical Objects, and Organizations.
* **Facts & Events**: Extracts explicit story facts (status, properties) and meaningful narrative events (travel, acquisition, discovery, conflicts).
* **Character Knowledge State**: Tracks what specific characters learn, witness, or are told in each scene.
* **External Claims**: Flags claims made in dialogue or action that require real-world verification.

### 🏛️ 3. Story World Memory & Canonical Entity Resolution
* **Dynamic Story State**: Reconstructs complete story world state up to any scene $N-1$ in linear screenplay time.
* **Canonical Entity Resolution**: Merges character aliases, nicknames, and dialogue titles (e.g., "Dad" vs. "Rajesh Rao") into single canonical entities.
* **Fact & Relationship Graph**: Tracks changing physical locations, object ownership, and character relationships across the script.

### 🔍 4. Continuity Conflict Detection & Human Review
* **Two-Stage Analysis**: Combines deterministic candidate generation with LLM continuity evaluation.
* **Hybrid Context Retrieval**: Retrieves relevant prior facts, character knowledge, and active world rules using BM25 and structured entity matching.
* **Issue Fingerprinting & Suppression**: Generates deterministic fingerprints for issues to prevent duplicate warnings.
* **Full Writer Review Lifecycle**:
  * **ACCEPT**: Confirm a valid continuity issue.
  * **RESOLVE**: Mark as fixed or intentional (e.g., character moved between scenes).
  * **IGNORE**: Mark as false positive.
  * **REOPEN**: Re-evaluate previously resolved issues after script revisions.

### 🌐 5. Factual & Historical Research Engine
* **Real-World Claim Verification**: Automatically researches real-world assertions (e.g., travel times between cities, historical dates, scientific facts).
* **Parallel Web Search Integration**: Leverages Parallel API to retrieve live web sources.
* **Evidence Synthesis**: Gemini evaluates retrieved web sources against screenplay claims and assigns verdicts (`VERIFIED`, `LIKELY_TRUE`, `CONTRADICTED`, `UNVERIFIED`).

### 📈 6. Plot & Subplot Timeline Visualizer
* **Multi-Track Narrative Visualizer**: Categorizes narrative milestones into `MAIN_PLOT` and `SUBPLOT` threads.
* **Milestone Connections**: Tracks causal and thematic relationships between plot events (`TRIGGERS`, `REVEALS`, `CONTRADICTS`, `CONVERGES_WITH`).
* **On-Demand Execution**: Runs story structure analysis when manually triggered by the user.

### ⚙️ 7. Project Settings & Custom World Rules
* **Continuity Strictness**: Adjustable strictness slider (0 to 10) to control issue sensitivity.
* **Fictional Physics & World Rules**: Define active world rules (e.g., *"Teleportation exists in 2040"*) to permit fictional lore and prevent false continuity flags.

### 🛡️ 8. Security & Production Hardening
* **Rate Limiting & Abuse Prevention**: Sliding window IP rate limits and daily usage protection caps for LLM and research endpoints.
* **Untrusted Content Framing**: System prompts frame screenplay inputs inside `<UNTRUSTED_SCREENPLAY_CONTENT>` boundaries to prevent prompt injection attacks.
* **No Authentication Requirement**: Designed as a lean MVP ready for deployment without OAuth overhead.

---

## 🏗️ Architecture Overview

```text
                               ┌───────────────────────────────────┐
                               │       Browser UI (Next.js 14)     │
                               └─────────────────┬─────────────────┘
                                                 │ REST API / HTTP
                                                 ▼
                               ┌───────────────────────────────────┐
                               │       FastAPI Backend Engine      │
                               └────────┬─────────────────┬────────┘
                                        │                 │
                ┌───────────────────────┘                 └───────────────────────┐
                ▼                                                                 ▼
   ┌──────────────────────────┐                                    ┌──────────────────────────┐
   │    Gemini AI Engine      │                                    │    Parallel Web Search   │
   │ (Vertex AI / Dev API)    │                                    │  (External Fact Engine)  │
   └────────────┬─────────────┘                                    └────────────┬─────────────┘
                │ Structured JSON                                               │ Live Web Sources
                └───────────────────────┐                 ┌─────────────────────┘
                                        ▼                 ▼
                               ┌───────────────────────────────────┐
                               │     CockroachDB / PostgreSQL      │
                               │  (Projects, Scenes, Story State,  │
                               │   Issues, Research & Timelines)   │
                               └───────────────────────────────────┘
```

---

## 🛠️ Prerequisites

- **Python**: 3.10 or higher
- **Node.js**: 18.x or higher (npm / npx)
- **Database**: CockroachDB (Local or Cloud) / PostgreSQL (or SQLite for local dev)
- **API Keys**:
  - **Gemini API Key** (or Google Cloud Vertex AI credentials)
  - **Parallel API Key** (for external web research features)

---

## 🚀 Quick Start Guide

### 1. Environment Configuration

Copy `.env.example` to `.env` in the repository root:

```bash
cp .env.example .env
```

Configure your environment variables in `.env`:

```ini
# Database Connection
DATABASE_URL=postgresql://root@localhost:26257/script_supervisor?sslmode=disable

# Application Transport & CORS
ENVIRONMENT=production
DEBUG=false
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Gemini API Credentials
GEMINI_PROVIDER=developer
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Parallel API Key (External Web Research)
PARALLEL_API_KEY=your_parallel_api_key_here
```

---

### 2. Backend Setup

Navigate to the `backend` directory, create a virtual environment, and install dependencies:

```bash
cd backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### 3. Database Migration

Initialize database tables and run schema migrations using Alembic:

```bash
alembic upgrade head
```

---

### 4. Run Backend Server

Start the FastAPI application with Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

* **API Server**: `http://localhost:8000`
* **Interactive Swagger Documentation**: `http://localhost:8000/docs`

---

### 5. Frontend Setup

In a separate terminal, navigate to the `frontend` directory and start the Next.js development server:

```bash
cd frontend

# Install Node dependencies
npm install

# Start development server
npm run dev
```

* **Web UI**: `http://localhost:3000`

---

## 🧪 Verification & Testing

Run the full automated test suite using `pytest`:

```bash
cd backend
.venv\Scripts\pytest tests/ -v
```

---

## 📁 Repository Structure

```text
├── backend/
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── api/              # FastAPI API routes (scenes, issues, research, timeline, etc.)
│   │   ├── db/               # SQLAlchemy database models & session setup
│   │   ├── schemas/          # Pydantic schemas & response models
│   │   ├── services/         # Core business logic (gemini, parallel, continuity, research, etc.)
│   │   ├── config.py         # Application settings & environment configuration
│   │   └── main.py           # FastAPI application entry point
│   ├── tests/                # Automated pytest suite
│   └── requirements.txt      # Python dependencies
├── frontend/
│   ├── app/                  # Next.js 14 App Router pages & layout
│   ├── components/           # React UI components (Editor, Timeline, Issues, Research, etc.)
│   ├── lib/                  # API client & TypeScript interfaces
│   └── package.json          # Node dependencies
├── .env.example              # Environment configuration template
├── .gitignore                # Production git ignore rules
└── README.md                 # Project documentation
```

---

## 📄 License

Distributed under the MIT License. See `LICENSE` for more information.
