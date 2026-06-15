# SPL Generator — Devpost Submission Article

## Inspiration


---

## What it does
*   **Natural Language Translation:** Translate plain English requests into optimized SPL queries instantly.
*   **Structured Query Explanations:** Displays a clean, one-sentence explanation alongside the code block to demystify what the generated query does.
*   **Conversational Query Refinement (Agentic AI):** Iterate on queries using natural, chat-like commands (e.g., *"limit to the top 5 hours"*, *"filter for status=404"*). The assistant maintains context of the conversation and dynamically adapts the query.
*   **Dynamic Auto-Visualisation:** Automatically analyzes Splunk's result shape and renders the most appropriate chart:
    *   *Line Charts* for time-series trend data (e.g., `_time` and numerical metrics).
    *   *Bar Charts* for categories/distributions (e.g., visits by page or requests by IP).
    *   *Interactive Data Tables* as the default fallback.
*   **Instant REST Execution:** Connects directly to local Splunk Enterprise (port 8089) and runs queries in real time.
*   **Diagnostics Dashboard:** Displays live connectivity statuses for both the Splunk REST API and the LLM endpoint.
*   **Search History & CSV Export:** Replay recent searches from the sidebar and export results to CSV with one click.

---

### Setup & Ingestion

#### 1. Prerequisites
- **Python 3.9+**
- **Splunk Enterprise** (with Developer License activated)

#### 2. Load Sample Data
1. Log in to your Splunk Web Console (usually at `http://localhost:8000`).
2. Go to **Settings** → **Add Data** → **Upload**.
3. Select or download the Splunk search tutorial dataset (`tutorialdata.zip`).
4. Set the **Source type** to `access_combined_wcookie` and **Index** to `main`.

*Alternatively, you can load the data via the Splunk CLI:*
```bash
/Applications/Splunk/bin/splunk add oneshot "/path/to/tutorialdata.zip" -index main -sourcetype access_combined_wcookie -auth admin:changeme
```

#### 3. Clone & Install Dependencies
```bash
# Clone the repository
git clone <your-repo-url>
cd splunkai

# Install Python packages
pip install -r requirements.txt
```

#### 4. Configuration (`.env`)
Create a `.env` file in the root directory (a template is provided in the repository) and fill in your credentials:
```env
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=changeme

# Fallback LLM API Keys (Fill at least one or run local Ollama)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

#### 5. Launch the Web Application
```bash
streamlit run app.py
```
This will open the application in your default browser at `http://localhost:8501`.

---

### Verification & Manual Testing Scenarios

Try the following questions to verify the application functionality:
1.  *"Show me the top 10 pages by visits"*
2.  *"How many errors happened each hour today"*
3.  *"Which IP addresses made the most requests"*
4.  *"Show me all 404 errors in the last hour"*

---

## How we built it
### Architecture

```
                 +--------------------------+
                 |   User Browser (UI)      |
                 |      (Streamlit)         |
                 +------------+-------------+
                              |
                              | Natural Language Question / Refinements
                              v
                 +------------+-------------+
                 |       llm_client.py      |
                 |   (Ollama / OpenAI /     |
                 |  Anthropic / Hosted)     |
                 +------------+-------------+
                              |
                              | Generated SPL + Explanation
                              v
                 +------------+-------------+
                 |     splunk_client.py     |
                 |  (Splunk Python SDK)     |
                 +------------+-------------+
                              |
                              | REST API call (Port 8089)
                              v
                 +------------+-------------+
                 |    Splunk Enterprise     |
                 |      (Data Index)        |
                 +--------------------------+
```



## Challenges we ran into


## Accomplishments that we're proud of


## What we learned


## What's next for SPL Generator
