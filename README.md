# SPL Generator 🔍

Translate plain English questions into clean Splunk Search Processing Language (SPL) queries and run them instantly against your Splunk instance. Designed for analysts, engineers, and developers who need to query Splunk without memorizing complex SPL syntax.

Built for the **Splunk Agentic Ops Hackathon (Platform & Developer Experience track)**.

---

## Features

- **Natural Language Translation:** Type plain English and receive fully functional, optimized SPL queries.
- **Instant Execution:** Run the generated queries directly against your Splunk REST API.
- **Interactive Dashboard:** View, sort, search, and analyze your Splunk search results in a clean, modern web interface.
- **Interactive Quick Suggestions:** Fast-track search with preset popular questions.
- **Search History:** Quickly reuse previously executed searches from the sidebar.
- **CSV Export:** Download search data instantly for reporting or external analysis.

---

## Architecture

```
                 +--------------------------+
                 |   User Browser (UI)      |
                 |      (Streamlit)         |
                 +------------+-------------+
                              |
                              | Natural Language Question
                              v
                 +------------+-------------+
                 |       llm_client.py      |
                 |  (OpenAI / Anthropic /   |
                 |      Hosted Models)      |
                 +------------+-------------+
                              |
                              | Generated SPL Query
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

---

## Setup & Ingestion

### 1. Prerequisites
- **Python 3.9+**
- **Splunk Enterprise** (with Developer License activated)

### 2. Load Sample Data
1. Log in to your Splunk Web Console (usually at `http://localhost:8000`).
2. Go to **Settings** → **Add Data** → **Upload**.
3. Select or download the Splunk search tutorial dataset (`tutorialdata.zip`).
4. Set the **Source type** to `access_combined_wcookie` and **Index** to `main`.

*Alternatively, you can load the data via the Splunk CLI:*
```bash
/Applications/Splunk/bin/splunk add oneshot "/path/to/tutorialdata.zip" -index main -sourcetype access_combined_wcookie -auth admin:changeme
```

### 3. Clone & Install Dependencies
```bash
# Clone the repository
git clone <your-repo-url>
cd splunkai

# Install Python packages
pip install -r requirements.txt
```

### 4. Configuration (`.env`)
Create a `.env` file in the root directory (a template is provided in the repository) and fill in your credentials:
```env
SPLUNK_HOST=localhost
SPLUNK_PORT=8089
SPLUNK_USERNAME=admin
SPLUNK_PASSWORD=changeme

# Fallback LLM API Keys (Fill at least one)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### 5. Launch the Web Application
```bash
streamlit run app.py
```
This will open the application in your default browser at `http://localhost:8501`.

---

## Verification & Manual Testing Scenarios

Try the following questions to verify the application functionality:
1. *"Show me the top 10 pages by visits"*
2. *"How many errors happened each hour today"*
3. *"Which IP addresses made the most requests"*
4. *"Show me all 404 errors in the last hour"*

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
