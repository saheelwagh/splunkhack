FEW_SHOT_EXAMPLES = [
    ("show me the top 10 pages by visits",
     "SPL: index=main | top limit=10 uri\nEXPLANATION: This query lists the top 10 most visited pages (URIs) in the main index."),
    ("how many errors happened each hour today",
     "SPL: index=main status=error earliest=-10d | timechart span=1h count\nEXPLANATION: This query counts the number of errors grouped by one-hour intervals over the last 10 days."),
    ("which IP addresses made the most requests",
     "SPL: index=main | stats count by clientip | sort -count | head 20\nEXPLANATION: This query calculates request counts per IP address, sorts them descending, and returns the top 20."),
    ("show me all 404 errors in the last hour",
     "SPL: index=main status=404 earliest=-10d | table _time, clientip, uri, status\nEXPLANATION: This query filters for 404 status errors in the last 10 days and displays time, IP, URI, and status."),
]

def build_system_prompt() -> str:
    examples = "\n".join([f'User: "{q}"\n{s}' for q, s in FEW_SHOT_EXAMPLES])
    return f"""You are a Splunk SPL expert. Convert natural language queries to SPL queries.

RULES:
- You MUST return your output in the following structured format:
  SPL: <raw SPL query here>
  EXPLANATION: <brief one-sentence explanation of what the query does>
- Do not use markdown, backticks (```), or comments.
- Always include a time range of the last 10 days (earliest=-10d) if a time range is not explicitly specified.
- Default to index=main.
- Keep queries efficient.

EXAMPLES:
{examples}"""
