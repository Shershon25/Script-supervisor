# Script Supervisor

A continuity and reality-checking assistant for screenwriters.

Script Supervisor parses screenplays scene by scene, builds a persistent story memory, and checks each new scene for contradictions against everything established earlier. Real-world claims in dialogue can be researched using live web sources. The writer reviews every finding and decides what to do with it.

---

## 🤔 Why Script Supervisor?

A screenplay distributes information across dozens or hundreds of scenes. Characters move, acquire and lose objects, learn things, and form relationships — all of which must stay consistent as the script evolves. Manual tracking becomes unreliable past a certain length.

Not everything unusual is an error. A screenplay might establish that teleportation exists, or that a character deliberately changes their story. The system must distinguish between:

1. **Continuity errors** — contradictions against established story facts
2. **Real-world claims** — assertions about external reality that can be verified
3. **Fictional world rules** — intentional rules the writer defines for their universe
4. **Writer decisions** — issues already reviewed and accepted, resolved, or dismissed

---

## ✨ What It Does

### 🧠 Story Memory

Each scene is analyzed by Gemini, which extracts:

- **Entities** — characters, locations, physical objects, organizations
- **Facts** — explicit properties and statuses (e.g., "John's father is deceased")
- **Events** — meaningful plot actions (travel, acquisition, loss, discovery, death)
- **Relationships** — connections between entities (owns, parent_of, friend_of, etc.)
- **Character knowledge** — what specific characters learn, witness, or are told

This structured data is stored in CockroachDB. Every item carries a scene number so later analysis can reconstruct exactly what the story world looked like at any point.

> Character knowledge is tracked separately from story facts. "Alex *knows* the vault is empty" is different from "the vault is empty."

### 🔍 Continuity Checking

When a scene is analyzed, the system builds the story state up to scene N-1 and checks the new scene against it in two stages:

1. **Candidate generation** — SQL queries find potential conflicts (fact contradictions, location conflicts, object ownership changes, relationship conflicts, character knowledge conflicts)
2. **Gemini evaluation** — candidates are passed to Gemini with retrieved context, world rules, and past writer decisions; Gemini assigns a verdict and confidence score

Findings include evidence showing which prior scene established the conflicting information. Duplicates are suppressed using deterministic fingerprinting.

### 🌐 Reality Checking & Research

Gemini identifies claims in dialogue or action that assert something about the real world and classifies them:

| Claim Type | Color | Meaning |
|---|---|---|
| `REAL_WORLD_CLAIM` | 🟡 Amber | Verifiable external fact — research triggered |
| `FICTIONAL_WORLD_RULE` | — | Intentional fictional rule — no research needed |
| `STORY_FACT` | — | Internal story information — no research needed |

For claims that require research, the pipeline is:

1. Gemini generates a research objective
2. Parallel API retrieves live web sources
3. Gemini evaluates the evidence and assigns a verdict:

| Verdict | Color | Meaning |
|---|---|---|
| `VERIFIED` | 🟢 Emerald | Confirmed by external sources |
| `LIKELY_TRUE` | 🟢 Emerald | Supported but not definitively confirmed |
| `CONTRADICTED` | 🔴 Rose | Evidence contradicts the claim |
| `INCONCLUSIVE` | 🟡 Amber | Insufficient evidence to decide |
| `UNVERIFIED` | 🟡 Amber | Research not yet run |

Sources and reasoning are stored alongside the verdict so the writer can inspect them.

### 🌍 Fictional World Rules

Writers can define rules for their fictional universe in project settings (e.g., *"Teleportation exists in 2040"*). Active rules are retrieved during every continuity and reality check, preventing valid fictional behavior from being flagged as an error. Rules are explicitly fed into Gemini context before evaluation.

### 📈 Plot & Timeline Analysis

When triggered manually, Gemini analyzes all analyzed scenes and extracts plot events classified into named tracks (`MAIN_PLOT`, `SUBPLOT`). Events can be linked with connection types (`TRIGGERS`, `REVEALS`, `CONTRADICTS`, `CONVERGES_WITH`). Results are displayed as a multi-track timeline view.

### ✍️ Writer Review

Every finding has a status. Writers can:

| Action | Color | Result |
|---|---|---|
| **Accept** | 🟡 Amber | Confirmed as a real problem |
| **Resolve** | 🟢 Emerald | Fixed or intentional |
| **Ignore** | ⚫ Gray | Dismissed as false positive |
| **Reopen** | 🟣 Purple | Revisit a previously resolved issue |

Past review decisions are retrieved during future analysis so the system can respect writer intent and avoid raising the same issues again.

---

## 💡 Example

**Scene 8:** Maya loses her access card.

**Scene 31:** Maya uses the access card to enter the lab.

→ Script Supervisor flags: *"Object ownership conflict: Maya's access card was established as lost in Scene 8."* The evidence references Scene 8 directly.

---

**Scene 14:** A character states: *"The railway line was built in 1887."*

→ Script Supervisor extracts this as a `REAL_WORLD_CLAIM`. Parallel retrieves sources. Gemini evaluates them and returns a verdict of `LIKELY_TRUE` with source links.

---

**Scene 3, world rule defined:** *"Objects inside the temporal field age backward."*

→ A later scene showing an object becoming younger is not flagged, because the active world rule covers this behavior.

---

## ⚙️ How It Works

```
Writer writes or imports screenplay
            ↓
Scene-by-scene analysis (Gemini)
  → Entities, facts, events, relationships, character knowledge
  → Real-world claims identified and classified
            ↓
Story memory stored in CockroachDB
            ↓
Hybrid retrieval for continuity checking
  → SQL queries for relevant prior facts, events, knowledge
  → Writer decisions and world rules included in context
            ↓
Gemini evaluates candidate conflicts
  → Findings with evidence and confidence score
            ↓
Real-world claims → Parallel web search → Gemini evaluates sources
            ↓
Writer reviews findings (Accept / Resolve / Ignore / Reopen)
  → Decisions stored and retrieved in future analysis
```

---

## 🏗️ Architecture

### Technology Stack & Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                     Writer's Browser                            │
│          Next.js 14 / React / TypeScript (Vercel)               │
└───────────────────────────┬─────────────────────────────────────┘
                            │ REST API (JWT)
                            ▼
┌────────────────────────────────────────────────────────────────┐
│                FastAPI Backend (Google Cloud Run)              │
│           Python 3.10 · Uvicorn · SQLAlchemy · Alembic         │
│                                                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Scene       │  │  Retriever   │  │  Research Service    │  │
│  │  Processor   │  │  (SQL +      │  │  (Claims → Parallel  │  │
│  │  (Gemini)    │  │  Keyword)    │  │   → Gemini Eval)     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
│         │                 │                     │              │
└─────────┼─────────────────┼─────────────────────┼──────────────┘
          │                 │                     │
          ▼                 ▼                     ▼
┌──────────────────┐  ┌───────────────┐  ┌──────────────────────┐
│   Gemini API     │  │  CockroachDB  │  │    Parallel API      │
│ (Vertex AI or    │  │  (All story   │  │  (Live web search    │
│  Developer API)  │  │   state)      │  │   for fact-checking) │
└──────────────────┘  └───────────────┘  └──────────────────────┘
```

### Component Responsibilities

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Web app | Next.js 14 / React / TypeScript | Screenplay editor, continuity panel, research view, timeline |
| Backend API | Python / FastAPI / Uvicorn | Orchestration, routing, rate limiting, auth |
| LLM | Gemini (Developer API or Vertex AI) | Scene extraction, continuity reasoning, claim classification, research evaluation, timeline |
| Web research | Parallel API | Live web search for real-world claim verification |
| Database | CockroachDB | All persistent story state, issues, research, world rules |
| ORM | SQLAlchemy 2.x + Alembic | Database models and migrations |
| Auth | JWT (PyJWT) + PBKDF2-SHA256 | User accounts and session tokens |
| Deployment | Vercel + Google Cloud Run | Frontend hosting and backend containerized service |
| CI/CD | Google Cloud Build | Build and deploy backend on push to main |

Gemini can be used via the Developer API (key-based) or Google Cloud Vertex AI (ADC / service account), configured by `GEMINI_PROVIDER`.

---

## 🔎 Why Parallel?

Parallel is the web research backbone of the reality-checking system. When a screenplay makes a verifiable real-world claim, the system needs live, sourced, external evidence — not an LLM guessing from training data.

Here is exactly how Parallel is used ([`research_service.py`](backend/app/services/research_service.py), [`parallel.py`](backend/app/services/parallel.py)):

```
1. Gemini analyzes the scene and classifies each claim:
   REAL_WORLD_CLAIM / FICTIONAL_WORLD_RULE / STORY_FACT
           ↓
2. For each REAL_WORLD_CLAIM flagged for research,
   the backend formulates a targeted objective, e.g:
   "Determine whether 'Mumbai Central opened in 1930' is factually accurate."
           ↓
3. execute_parallel_search(objective)
   → POST https://api.parallel.ai/v1/search
   → Returns sources: title, URL, domain, excerpt, relevance score
           ↓
4. Sources are persisted in CockroachDB (ResearchResult records)
           ↓
5. Gemini receives the sources inside <UNTRUSTED_RESEARCH_EVIDENCE> delimiters
   and evaluates them against the claim
   → Returns: verdict, confidence, reasoning, supporting/contradicting source IDs
           ↓
6. Verdict and evaluation stored (ResearchEvaluation record)
   Claim status updated: VERIFIED / LIKELY_TRUE / CONTRADICTED / INCONCLUSIVE
```

**Parallel retrieves sources — Gemini decides the verdict.** The evaluation is always grounded in real web evidence with source URLs the writer can inspect, not inference from training data alone.

Research results are also cached: if the same claim has already been researched within the same project, the existing completed task is reused without calling Parallel again.

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- CockroachDB running locally (default port 26257) or a CockroachDB Cloud connection string
- Gemini API key (or Google Cloud project with Vertex AI enabled)
- Parallel API key (for web research)

### 1. Environment

Copy the example environment file to the repository root:

```bash
cp .env.example .env
```

Edit `.env` with your values:

```ini
DATABASE_URL=postgresql://root@localhost:26257/script_supervisor?sslmode=disable

ENVIRONMENT=development
DEBUG=true
FRONTEND_URL=http://localhost:3000
NEXT_PUBLIC_API_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Use 'developer' for API key, 'vertexai' for GCP credentials
GEMINI_PROVIDER=developer
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash

# Google Cloud (only needed when GEMINI_PROVIDER=vertexai)
GCP_PROJECT_ID=your_gcp_project_id
GCP_LOCATION=global

PARALLEL_API_KEY=your_parallel_api_key_here

# Demo user for quick access (loaded by backend, never sent to the browser)
DEMO_USER_USERNAME=your_demo_username
DEMO_USER_PASSWORD=your_demo_password
```

### 2. Backend

```bash
cd backend

python -m venv .venv

# Windows
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn app.main:app --reload --port 8000
```

API available at `http://localhost:8000` — Swagger docs at `http://localhost:8000/docs`.

### 3. Frontend

In a separate terminal:

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:3000`.

### Importing a Screenplay

The import flow supports `.pdf`, `.docx`, and `.fountain` files (up to 15 MB). After upload, the backend detects scene boundaries and presents a preview for review before committing scenes to the project.

---

## 🧪 Testing

```bash
cd backend
pytest tests/ -v
```

The test suite (18 files) covers: auth, continuity detection, claims and research, document parsing, document import API, issue reviews, project settings and world rules, retrieval and reasoning, scene processor, story state, security hardening, screenplay export, and the unified supervisor flow.

---

## 🚀 Deployment

The backend is containerized and deployed to Google Cloud Run via Cloud Build on push to `main`. The frontend is deployed to Vercel.

```
Vercel (Next.js)
  → Google Cloud Run (FastAPI, europe-west1)
      → Gemini API / Vertex AI
      → Parallel API
      → CockroachDB Cloud
```

---


## 🔒 Security

- API keys and the database URL are server-side only, never exposed to the browser
- Per-minute sliding window rate limits and 24-hour daily caps per IP for analysis, research, and import endpoints
- Screenplay text sent to Gemini is wrapped in `<UNTRUSTED_SCREENPLAY_CONTENT>` delimiters; system prompts instruct the model to treat it as untrusted data
- File uploads are checked for extension (`.pdf`, `.docx`, `.fountain`), file size (15 MB max), and decompressed character count (2M max)
- CORS restricted to configured origins
- JWT tokens expire after 1 hour

---

## 📁 Repository Structure

```
script-supervisor/
├── backend/
│   ├── alembic/              # Database migrations
│   ├── app/
│   │   ├── api/              # FastAPI routes
│   │   ├── core/             # Auth and security utilities
│   │   ├── db/               # SQLAlchemy models and session
│   │   ├── schemas/          # Pydantic request/response models
│   │   ├── services/         # Core logic (gemini, continuity, retriever, research, etc.)
│   │   └── config.py         # Settings loaded from environment
│   ├── tests/                # pytest test suite (18 test files)
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── app/                  # Next.js App Router pages
│   ├── components/           # React UI components
│   ├── context/              # Auth context
│   └── lib/                  # API client and TypeScript types
├── cloudbuild.yaml           # Google Cloud Build pipeline
├── .env.example              # Environment variable template
├── DEPLOYMENT.md             # Production deployment guide
└── README.md
```

---

## 📄 License

MIT License. See [`LICENSE`](LICENSE) for details.
