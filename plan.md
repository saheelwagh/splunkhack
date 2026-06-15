# SPL Query Generator — Agent Build Plan
**Hackathon:** Splunk Agentic Ops Hackathon  
**Track:** Platform & Developer Experience  
**Special prizes targeted:** Best Use of Splunk Hosted Models + Best Use of Splunk MCP Server  
**Deadline:** June 15, 2026 @ 9:00am PDT

---

## What We're Building

A web app where a user types a plain English question — "show me all failed logins in the last 6 hours" — and the agent:
1. Translates it to a valid SPL query using Splunk Hosted Models
2. Executes the query via the Splunk MCP Server
3. Returns results + a plain English explanation of what the query does and what the results mean

**Demo loop (must fit in 3 minutes):**  
Type question → see SPL generated → see results → see explanation

---

## Tech Stack

| Layer | Tool |
|---|---|
| Backend | Python 3.11, FastAPI |
| Splunk SDK | `splunk-sdk` (Python) |
| Splunk interface | REST API (port 8089) + Splunk MCP Server |
| LLM | Splunk Hosted Models (for SPL generation + explanation) |
| Frontend | Single HTML file, vanilla JS (no framework — keeps scope tight) |
| Sample data | Splunk's built-in tutorial dataset + sample security logs |

---

## Project File Structure

```
spl-generator/
├── main.py                  # FastAPI app, all routes
├── splunk_client.py         # Splunk REST API wrapper
├── mcp_client.py            # Splunk MCP Server interface
├── hosted_models.py         # Splunk Hosted Models calls
├── prompts.py               # All prompt templates (keep separate for easy iteration)
├── static/
│   └── index.html           # Single-page UI
├── data/
│   └── sample_queries.json  # Few-shot examples for the prompt
├── architecture.png         # Required by submission — draw last
├── README.md                # Setup instructions
├── requirements.txt
└── .env.example             # Show required env vars, never commit .env
```

---

## Environment Variables

```bash
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=your_password
SPLUNK_TOKEN=your_api_token        # Alternative to user/pass
SPLUNK_MCP_ENDPOINT=http://localhost:PORT  # from Splunk MCP Server setup
SPLUNK_HOSTED_MODEL=splunk-hosted-llm      # verify exact model name in Splunk UI
```

---

## Prerequisites Checklist (Before Day 1 Tasks)

- [ ] Splunk Enterprise installed and running
- [ ] Developer license applied and active
- [ ] Can log into Splunk Web at `http://localhost:8000`
- [ ] Port 8089 (REST API) is accessible — test with `curl -k https://localhost:8089/services`

---

## Day 1 — Foundation
**Goal:** Splunk is talking to your code. A hardcoded SPL query fires and returns results. Nothing intelligent yet — just confirm the plumbing works.

### Step 1 — Install dependencies
```bash
pip install fastapi uvicorn splunk-sdk python-dotenv requests httpx
```

Create `requirements.txt`:
```
fastapi
uvicorn
splunk-sdk
python-dotenv
requests
httpx
```

### Step 2 — Load sample data into Splunk
1. In Splunk Web → Settings → Add Data → Upload
2. Upload the built-in tutorial data: `$SPLUNK_HOME/share/splunk/search_tutorial/tutorialdata.zip`
3. Set source type to `access_combined_wcookie`
4. Index: `main`
5. Confirm data is visible: run `index=main | head 10` in the Splunk search bar

Also load a security-flavored dataset for a more compelling demo:
- Go to Splunkbase → download "Splunk Security Essentials" sample data or use [Boss of the SOC dataset](https://github.com/splunk/botsv1)
- Alternatively generate fake auth logs with a Python script (included below)

**Fake auth log generator** — save as `data/generate_logs.py` and run once:
```python
import random, datetime

users = ["alice", "bob", "carol", "dan", "eve"]
ips = ["192.168.1.10", "10.0.0.5", "203.0.113.42", "198.51.100.7"]
outcomes = ["success"] * 8 + ["failure"] * 2  # 80/20 split

with open("auth_logs.csv", "w") as f:
    f.write("timestamp,user,src_ip,action\n")
    for i in range(500):
        ts = datetime.datetime.now() - datetime.timedelta(hours=random.randint(0, 48))
        f.write(f"{ts.isoformat()},{random.choice(users)},{random.choice(ips)},{random.choice(outcomes)}\n")
```
Upload `auth_logs.csv` to Splunk, source type `csv`, index `main`.

### Step 3 — Splunk REST API wrapper
Create `splunk_client.py`:
```python
import splunklib.client as client
import splunklib.results as results
import os, time

def get_service():
    return client.connect(
        host=os.getenv("SPLUNK_HOST", "localhost"),
        port=int(os.getenv("SPLUNK_PORT", 8089)),
        username=os.getenv("SPLUNK_USERNAME"),
        password=os.getenv("SPLUNK_PASSWORD"),
    )

def run_spl(spl_query: str, max_results: int = 100) -> list[dict]:
    service = get_service()
    job = service.jobs.create(spl_query, exec_mode="blocking")
    reader = results.JSONResultsReader(job.results(output_mode="json", count=max_results))
    return [row for row in reader if isinstance(row, dict)]
```

### Step 4 — Enable and connect Splunk MCP Server
1. In Splunk Web → Apps → find Splunk MCP Server (install from Splunkbase if not present)
2. Note the MCP Server endpoint URL from its configuration page
3. Test connectivity:
```python
# Quick connectivity test — run from Python REPL
import httpx, os
resp = httpx.get(os.getenv("SPLUNK_MCP_ENDPOINT") + "/health")
print(resp.status_code)  # expect 200
```

Create `mcp_client.py`:
```python
import httpx, os

MCP_BASE = os.getenv("SPLUNK_MCP_ENDPOINT")

def mcp_search(spl_query: str) -> dict:
    """Execute SPL via MCP Server instead of direct REST — required for MCP prize."""
    payload = {
        "tool": "splunk_search",
        "parameters": {"query": spl_query, "max_results": 100}
    }
    resp = httpx.post(f"{MCP_BASE}/tools/call", json=payload, timeout=30)
    resp.raise_for_status()
    return resp.json()
```
> **Note:** Verify exact MCP tool names and payload shape from your Splunk MCP Server docs. The above is a reference pattern — adjust to match actual API.

### Step 5 — Day 1 smoke test
Create `test_day1.py` and run it. All three must pass before Day 2:
```python
from splunk_client import run_spl
from mcp_client import mcp_search

# Test 1: Direct REST API
results = run_spl("index=main | head 5")
assert len(results) > 0, "REST API: no results returned"
print("✅ REST API works")

# Test 2: MCP Server
mcp_results = mcp_search("index=main | head 5")
assert mcp_results is not None, "MCP Server: no response"
print("✅ MCP Server works")

# Test 3: Verify sample data exists
auth_results = run_spl("index=main action=failure | stats count")
print(f"✅ Sample data loaded — {auth_results} failure events found")
```

**Day 1 is done when all three tests print ✅.**

---

## Day 2 — Core Agent Loop
**Goal:** User types English → agent returns SPL + executes it + returns results. The full product loop works end to end.

### Step 1 — Connect Splunk Hosted Models
1. In Splunk Web → Settings → AI / Machine Learning → Hosted Models
2. Note the model name and inference endpoint
3. If Hosted Models require an API key or token, add it to `.env`

Create `hosted_models.py`:
```python
import httpx, os, json

HOSTED_MODEL_ENDPOINT = os.getenv("SPLUNK_HOSTED_MODEL_ENDPOINT")
HOSTED_MODEL_NAME = os.getenv("SPLUNK_HOSTED_MODEL", "splunk-llm")

def call_hosted_model(system_prompt: str, user_message: str) -> str:
    """
    Call Splunk Hosted Models inference endpoint.
    Adjust payload structure to match your specific Splunk version's API.
    Verify exact request format in: Splunk Docs → AI/ML → Hosted Models → API Reference
    """
    payload = {
        "model": HOSTED_MODEL_NAME,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "max_tokens": 500,
        "temperature": 0.1  # Low temp = more deterministic SPL output
    }
    headers = {"Authorization": f"Bearer {os.getenv('SPLUNK_TOKEN')}"}
    resp = httpx.post(HOSTED_MODEL_ENDPOINT, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
```

### Step 2 — Build the prompt templates
Create `prompts.py`. This is the most important file — iterate heavily on this:

```python
FEW_SHOT_EXAMPLES = [
    {
        "question": "show me all failed logins in the last 6 hours",
        "spl": 'index=main action=failure earliest=-6h | stats count by user, src_ip | sort -count'
    },
    {
        "question": "which users have the most activity today",
        "spl": 'index=main earliest=-24h | stats count by user | sort -count | head 10'
    },
    {
        "question": "show me errors by hour for the last day",
        "spl": 'index=main (action=failure OR status=error) earliest=-24h | timechart span=1h count by action'
    },
    {
        "question": "find IP addresses with more than 50 requests",
        "spl": 'index=main | stats count by src_ip | where count > 50 | sort -count'
    },
    {
        "question": "what happened in the last 30 minutes",
        "spl": 'index=main earliest=-30m | head 50'
    }
]

def build_examples_block() -> str:
    return "\n".join([
        f'User: "{ex["question"]}"\nSPL: {ex["spl"]}'
        for ex in FEW_SHOT_EXAMPLES
    ])

SPL_GENERATION_SYSTEM_PROMPT = f"""You are an expert Splunk SPL (Search Processing Language) query generator.

Your ONLY job is to convert natural language questions into valid SPL queries.
Return ONLY the SPL query. No explanation. No markdown. No backticks. Just the raw SPL string.

Rules:
- Always include a time range (earliest/latest or relative like -24h)
- Default to index=main unless the question implies a specific index
- Use `stats`, `timechart`, `table`, `top`, or `head` to shape results appropriately
- Keep queries efficient — avoid `*` wildcards on large fields
- If the question is ambiguous, make a reasonable assumption

Examples:
{build_examples_block()}
"""

SPL_EXPLANATION_SYSTEM_PROMPT = """You are a helpful Splunk assistant explaining SPL queries to non-technical users.

Given an SPL query and its results, provide:
1. A one-sentence plain English summary of what the query searched for
2. A one-sentence summary of what the results show
3. One suggested follow-up question the user might want to ask next

Be concise. No jargon. Write as if explaining to someone who has never used Splunk.
Format as JSON: {"summary": "...", "results_insight": "...", "follow_up": "..."}
"""

def build_explanation_prompt(spl: str, results: list[dict]) -> str:
    results_preview = str(results[:5])  # Send first 5 rows to keep tokens low
    return f"SPL Query:\n{spl}\n\nResults (first 5 rows):\n{results_preview}"
```

### Step 3 — Wire the agent loop
Create `agent.py`:
```python
from hosted_models import call_hosted_model
from mcp_client import mcp_search
from prompts import SPL_GENERATION_SYSTEM_PROMPT, SPL_EXPLANATION_SYSTEM_PROMPT, build_explanation_prompt
import json, re

def sanitize_spl(raw: str) -> str:
    """Strip any markdown fences or extra whitespace the model might add."""
    cleaned = re.sub(r"```[\w]*", "", raw).strip()
    return cleaned

def generate_and_run(natural_language_query: str) -> dict:
    # Step 1: Generate SPL
    raw_spl = call_hosted_model(SPL_GENERATION_SYSTEM_PROMPT, natural_language_query)
    spl = sanitize_spl(raw_spl)

    # Step 2: Execute via MCP Server
    try:
        mcp_response = mcp_search(spl)
        rows = mcp_response.get("results", [])
        error = None
    except Exception as e:
        rows = []
        error = str(e)

    # Step 3: Explain results
    explanation_raw = call_hosted_model(
        SPL_EXPLANATION_SYSTEM_PROMPT,
        build_explanation_prompt(spl, rows)
    )
    try:
        explanation = json.loads(explanation_raw)
    except json.JSONDecodeError:
        explanation = {"summary": explanation_raw, "results_insight": "", "follow_up": ""}

    return {
        "natural_language": natural_language_query,
        "spl": spl,
        "results": rows,
        "result_count": len(rows),
        "explanation": explanation,
        "error": error
    }
```

### Step 4 — FastAPI backend
Create `main.py`:
```python
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agent import generate_and_run
from dotenv import load_dotenv

load_dotenv()
app = FastAPI(title="SPL Generator")
app.mount("/static", StaticFiles(directory="static"), name="static")

class QueryRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.post("/query")
def query(req: QueryRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    return generate_and_run(req.question)

@app.get("/health")
def health():
    return {"status": "ok"}
```

### Step 5 — Minimal frontend
Create `static/index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>SPL Generator</title>
  <style>
    body { font-family: monospace; max-width: 800px; margin: 40px auto; padding: 0 20px; background: #0f0f0f; color: #e0e0e0; }
    h1 { color: #ff6b35; }
    input { width: 100%; padding: 12px; font-size: 16px; background: #1a1a1a; color: #e0e0e0; border: 1px solid #333; border-radius: 4px; }
    button { margin-top: 10px; padding: 10px 24px; background: #ff6b35; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 14px; }
    .card { background: #1a1a1a; border: 1px solid #333; border-radius: 8px; padding: 16px; margin-top: 16px; }
    .label { color: #888; font-size: 12px; text-transform: uppercase; margin-bottom: 6px; }
    .spl { color: #7ec8e3; white-space: pre-wrap; }
    .insight { color: #a8e6cf; }
    .follow-up { color: #ffd93d; cursor: pointer; text-decoration: underline; }
    table { width: 100%; border-collapse: collapse; font-size: 13px; }
    th { background: #333; padding: 8px; text-align: left; }
    td { padding: 8px; border-bottom: 1px solid #222; }
    .loading { color: #888; font-style: italic; }
    .error { color: #ff4444; }
  </style>
</head>
<body>
  <h1>🔍 SPL Generator</h1>
  <p>Ask a question about your Splunk data in plain English.</p>

  <input id="question" type="text" placeholder="e.g. show me all failed logins in the last 6 hours" />
  <button onclick="submit()">Generate & Run</button>

  <div id="output"></div>

  <script>
    document.getElementById("question").addEventListener("keydown", e => {
      if (e.key === "Enter") submit();
    });

    async function submit() {
      const question = document.getElementById("question").value.trim();
      if (!question) return;
      const out = document.getElementById("output");
      out.innerHTML = '<p class="loading">Generating SPL and running query...</p>';

      try {
        const resp = await fetch("/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question })
        });
        const data = await resp.json();
        render(data);
      } catch (err) {
        out.innerHTML = `<p class="error">Error: ${err.message}</p>`;
      }
    }

    function render(data) {
      const rows = data.results.slice(0, 20);
      const headers = rows.length ? Object.keys(rows[0]) : [];
      const tableRows = rows.map(r =>
        `<tr>${headers.map(h => `<td>${r[h] ?? ""}</td>`).join("")}</tr>`
      ).join("");

      document.getElementById("output").innerHTML = `
        <div class="card">
          <div class="label">Generated SPL</div>
          <code class="spl">${data.spl}</code>
        </div>
        <div class="card">
          <div class="label">What this query does</div>
          <p class="insight">${data.explanation.summary}</p>
          <div class="label" style="margin-top:12px">What the results show</div>
          <p class="insight">${data.explanation.results_insight}</p>
          <div class="label" style="margin-top:12px">Try next</div>
          <p class="follow-up" onclick="ask('${data.explanation.follow_up}')">${data.explanation.follow_up}</p>
        </div>
        ${data.error ? `<div class="card"><p class="error">Query error: ${data.error}</p></div>` : ""}
        <div class="card">
          <div class="label">Results (${data.result_count} rows, showing ${rows.length})</div>
          ${headers.length ? `<table>
            <thead><tr>${headers.map(h => `<th>${h}</th>`).join("")}</tr></thead>
            <tbody>${tableRows}</tbody>
          </table>` : "<p style='color:#888'>No results returned.</p>"}
        </div>
      `;
    }

    function ask(question) {
      document.getElementById("question").value = question;
      submit();
    }
  </script>
</body>
</html>
```

### Step 6 — Run it
```bash
uvicorn main:app --reload --port 8080
# Open http://localhost:8080
```

**Day 2 is done when:**
- You type a question and get SPL back
- The SPL executes and results appear in the table
- The explanation renders below the results
- Clicking the follow-up suggestion fires a new query

---

## Day 3 — Polish + Submit
**Goal:** Submitted before noon. Everything else is secondary.

### Step 1 — Error handling pass (1 hr)
Add these guards to `agent.py`:

```python
# If SPL fails to execute, ask the model to fix it
def generate_and_run(natural_language_query: str) -> dict:
    raw_spl = call_hosted_model(SPL_GENERATION_SYSTEM_PROMPT, natural_language_query)
    spl = sanitize_spl(raw_spl)

    try:
        mcp_response = mcp_search(spl)
        rows = mcp_response.get("results", [])
        error = None
    except Exception as first_error:
        # Self-healing: ask model to fix the broken SPL
        fix_prompt = f"This SPL query failed with error '{first_error}':\n{spl}\n\nRewrite it to fix the error. Return only the corrected SPL."
        fixed_spl = sanitize_spl(call_hosted_model(SPL_GENERATION_SYSTEM_PROMPT, fix_prompt))
        try:
            mcp_response = mcp_search(fixed_spl)
            rows = mcp_response.get("results", [])
            spl = fixed_spl + "  # (auto-corrected)"
            error = None
        except Exception as second_error:
            rows = []
            error = f"Original: {first_error} | After fix attempt: {second_error}"
    ...
```

### Step 2 — Architecture diagram (45 min)
Use [Excalidraw](https://excalidraw.com) or draw.io. Must show:

```
User (Browser)
    ↓ natural language question
FastAPI Backend (main.py)
    ↓ prompt + question
Splunk Hosted Models
    ↓ SPL query string
Splunk MCP Server ──→ Splunk Enterprise (index=main)
    ↓ query results
FastAPI Backend
    ↓ SPL + results
Splunk Hosted Models
    ↓ explanation JSON
FastAPI Backend
    ↓ full response
User (Browser) — displays SPL + table + explanation
```

Save as `architecture.png` in repo root. Required by submission rules.

### Step 3 — README (45 min)
`README.md` must include:

```markdown
# SPL Query Generator

Translate plain English questions into Splunk SPL queries using Splunk Hosted Models,
execute them via the Splunk MCP Server, and get results with plain English explanations.

## Requirements
- Splunk Enterprise with Developer License
- Splunk MCP Server installed
- Splunk Hosted Models enabled
- Python 3.11+

## Setup
1. Clone the repo
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and fill in your Splunk credentials
4. Load sample data (see `/data/generate_logs.py`)
5. `uvicorn main:app --reload --port 8080`
6. Open http://localhost:8080

## Architecture
See `architecture.png`

## License
MIT
```

### Step 4 — Demo video script (1.5 hrs)
Record one take. Keep it under 3 minutes. Follow this script exactly:

**0:00–0:20** — State the problem: "Splunk is powerful but SPL is a barrier. Non-technical analysts can't query their own data."

**0:20–0:40** — Show the UI. Type: *"show me all failed logins in the last 6 hours"*

**0:40–1:10** — Walk through the output: the SPL that was generated, the results table, the plain English explanation

**1:10–1:30** — Click the suggested follow-up question to show the conversational loop

**1:30–2:00** — Show the architecture briefly — point to Hosted Models + MCP Server as the key Splunk components

**2:00–2:30** — Type a harder question: *"which users failed login more than 10 times and haven't had a success"* — show it handles complex queries

**2:30–3:00** — Wrap up: "Any analyst, no SPL knowledge required. Built on Splunk Hosted Models and Splunk MCP Server."

Upload to YouTube (unlisted is fine) before submitting.

### Step 5 — Devpost submission checklist
- [ ] Public GitHub repo with open-source license (MIT)
- [ ] `architecture.png` in repo root
- [ ] `README.md` with setup instructions
- [ ] `.env.example` committed (not `.env`)
- [ ] YouTube video link ready
- [ ] Devpost form filled: select **Platform & Developer Experience** track
- [ ] Check **Best Use of Splunk MCP Server** prize
- [ ] Check **Best Use of Splunk Hosted Models** prize
- [ ] Submit before June 15 @ 9:00am PDT

---

## Key Resources

| Resource | URL |
|---|---|
| Splunk REST API reference | https://docs.splunk.com/Documentation/Splunk/latest/RESTREF/RESTprolog |
| Splunk Python SDK | https://dev.splunk.com/enterprise/docs/devtools/python/sdk-python |
| Splunk MCP Server docs | https://splunkbase.splunk.com (search "MCP Server") |
| Splunk Hosted Models | https://docs.splunk.com/Documentation/Splunk/latest/AI/hostedmodels |
| SPL quick reference | https://docs.splunk.com/Documentation/SCS/current/SearchReference/Introduction |
| Devpost submission | https://splunk.devpost.com |

---

## Risk Log

| Risk | Mitigation |
|---|---|
| Hosted Models API shape unknown until setup | Check docs on Day 1; `hosted_models.py` is isolated so easy to swap |
| MCP Server tool names differ from plan | MCP client is in one file — update payload shape only |
| SPL generation quality poor | Add more few-shot examples to `prompts.py`; lower temperature |
| Demo data too sparse for compelling results | Run `generate_logs.py` with `n=2000` instead of 500 |