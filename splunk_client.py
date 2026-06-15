import splunklib.client as client
import splunklib.results as results_module
import os
import urllib3
from typing import Tuple, List, Dict, Optional

# Suppress unverified HTTPS request warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_service():
    """Establishes connection to the Splunk Enterprise instance REST API."""
    return client.connect(
        host=os.getenv("SPLUNK_HOST", "localhost"),
        port=int(os.getenv("SPLUNK_PORT", 8089)),
        username=os.getenv("SPLUNK_USERNAME", "admin"),
        password=os.getenv("SPLUNK_PASSWORD", "changeme"),
        verify=False  # Required for local self-signed SSL certificates
    )

def run_spl(spl_query: str, max_results: int = 50) -> Tuple[List[Dict], Optional[str]]:
    """Runs an SPL query against Splunk and returns (rows, error_message).
    
    If the query executes successfully, error_message is None.
    """
    try:
        service = get_service()
        
        # Splunk REST API search jobs require the query to start with "search " 
        # unless it starts with a generating command (e.g., "|", "inputlookup", "metadata").
        normalized_query = spl_query.strip()
        if not (normalized_query.startswith("search") or 
                normalized_query.startswith("|") or 
                normalized_query.startswith("inputlookup") or 
                normalized_query.startswith("metadata") or 
                normalized_query.startswith("pivot") or
                normalized_query.startswith("tstats")):
            normalized_query = "search " + normalized_query
            
        job = service.jobs.create(normalized_query, exec_mode="blocking")
        reader = results_module.JSONResultsReader(
            job.results(output_mode="json", count=max_results)
        )
        rows = [row for row in reader if isinstance(row, dict)]
        return rows, None
    except Exception as e:
        return [], str(e)
