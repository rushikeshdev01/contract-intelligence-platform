# 📄 Multi-Agent Contract Intelligence Platform

A multi-agent AI system that analyzes legal contracts — automatically classifying the document type, segmenting it into clauses, flagging risky terms from _your_ side of the deal, checking for silently missing protections, and comparing key terms against industry-standard benchmarks.

Built with **LangGraph**, **FastAPI**, **Streamlit**, and **Groq**.

---

## Why this exists

Reading and reviewing contracts manually is slow, and risk often hides in what's _missing_ just as much as what's written. A single generic "summarize this contract" prompt misses structure, ignores whose side you're on, and can't tell you whether a clause is actually unusual. This project solves that by splitting the work across five specialized agents that each do one job well, so the output is structured, explainable, and grounded — not just a wall of AI-generated prose.

---

## Features

- **Document-Type Classification** — detects whether the contract is an NDA, SaaS Agreement, Employment Agreement, Vendor Agreement, Lease, or general commercial agreement, and applies a checklist built for that specific type.
- **Position-Aware Risk Analysis** — you specify which party you are (e.g. Vendor vs. Customer), and every risk assessment is reasoned from that side. The same clause can be favorable for one party and risky for the other.
- **Missing-Provision Detection** — flags critical protections that are silently absent from the contract (e.g. no liability cap), which is often riskier than a clause that states a weak term explicitly.
- **Market Standard Benchmarks** — extracts real numeric terms (notice periods, liability caps, non-compete duration, etc.) and compares them against industry-standard ranges with a clear green / yellow / red status.
- **Transparent Agent Reasoning** — an expandable trace shows exactly what each agent did and found, so the analysis isn't a black box.
- **Downloadable Report** — export the full analysis as a formatted `.docx` file.

---

## Architecture

```
Upload contract (PDF/DOCX)
        │
        ▼
[Document Classifier]  → identifies contract type (NDA, SaaS, Lease, etc.)
        │
        ▼
[Clause Segmenter]     → splits raw text into individual clauses
        │
        ▼
[Risk Analyzer]        → flags risky clauses (position-aware) +
        │                 checks type-specific checklist for missing protections
        ▼
[Benchmark Analyzer]   → extracts key durations, compares to industry standards
        │
        ▼
[Summarizer]           → produces a plain-English executive summary
        │
        ▼
Streamlit UI ← FastAPI backend
(risk flags, benchmarks, missing protections, reasoning trace, DOCX export)
```

Each agent is a node in a **LangGraph** state graph — every agent reads from and writes to a shared state object, passing structured data (not just raw text) to the next step.

---

## Tech Stack

| Layer               | Tool                             |
| ------------------- | -------------------------------- |
| LLM inference       | Groq (`llama-3.3-70b-versatile`) |
| Agent orchestration | LangGraph                        |
| Backend             | FastAPI                          |
| Frontend            | Streamlit                        |
| Document parsing    | `pypdf`, `python-docx`           |
| Report generation   | `python-docx`                    |

---

## Project Structure

```
contract-intelligence-platform/
├── main.py                        # FastAPI app — /analyze endpoint
├── streamlit_app.py                # Frontend UI
├── requirements.txt
│
├── agents/
│   ├── state.py                   # Shared LangGraph state schema
│   ├── doc_classifier.py          # Document-Type Classifier agent
│   ├── clause_segmenter.py        # Clause Segmentation agent
│   ├── risk_analyzer.py           # Position-aware Risk Analyzer agent
│   ├── benchmark_analyzer.py      # Market Benchmark agent
│   ├── summarizer.py              # Summary agent
│   └── graph.py                   # Wires all agents into the LangGraph pipeline
│
└── services/
    ├── extraction_service.py      # PDF/DOCX text extraction
    ├── groq_client.py             # Shared Groq API client
    ├── benchmarks.py              # Industry-standard benchmark reference table
    ├── checklists.py              # Per-document-type missing-provision checklists
    └── report_generator.py        # Builds the downloadable .docx report
```

---

## Getting Started

### 1. Clone and install

```bash
git clone https://github.com/rushikeshdev01/contract-intelligence-platform.git
cd contract-intelligence-platform
pip install -r requirements.txt
```

### 2. Set up your API key

```bash
cp .env.example .env
```

Add your [Groq API key](https://console.groq.com) to `.env`:

```
GROQ_API_KEY=your_key_here
```

### 3. Run the backend

```bash
uvicorn main:app --reload
```

### 4. Run the frontend (in a new terminal)

```bash
streamlit run streamlit_app.py
```

Open `http://localhost:8501`, upload a contract, select which party you are, and click **Analyze Contract**.

---

## Limitations

- This tool provides an **AI-assisted first-pass review**, not a substitute for review by a qualified attorney.
- Benchmark ranges are general industry references, not legal standards, and may not fit every jurisdiction or deal type.
- Accuracy depends on the underlying LLM and can vary with unusual contract formatting or non-English text.

---

## License

MIT
