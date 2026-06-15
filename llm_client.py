import os
import requests
from typing import Optional, List, Dict

def call_llm(system_prompt: str, messages: List[Dict[str, str]]) -> str:
    """Invokes the configured LLM (Ollama, Hosted Models, Anthropic, or OpenAI) with conversation history."""
    # 1. Try local Ollama first as it requires no keys and is free
    try:
        resp = requests.get("http://localhost:11434/api/tags", timeout=2)
        if resp.status_code == 200:
            model = os.getenv("OLLAMA_MODEL", "llama3.2")
            return _call_ollama(system_prompt, messages, model)
    except Exception:
        # Ollama not running or failed, proceed to other LLMs
        pass

    # 2. Try Splunk Hosted Models
    endpoint = os.getenv("SPLUNK_HOSTED_MODEL_ENDPOINT")
    if endpoint:
        try:
            return _call_splunk_hosted(system_prompt, messages, endpoint)
        except Exception as e:
            print(f"Splunk Hosted Models call failed: {e}. Trying fallback LLMs...")

    # 3. Fallback: Anthropic
    if os.getenv("ANTHROPIC_API_KEY"):
        return _call_anthropic(system_prompt, messages)

    # 4. Fallback: OpenAI
    if os.getenv("OPENAI_API_KEY"):
        return _call_openai(system_prompt, messages)

    raise ValueError("No LLM configured. Please ensure Ollama is running, or set SPLUNK_HOSTED_MODEL_ENDPOINT, ANTHROPIC_API_KEY, or OPENAI_API_KEY in .env")

def _call_ollama(system: str, messages: List[Dict[str, str]], model: str) -> str:
    """Sends a chat request to the local Ollama API."""
    formatted_messages = [{"role": "system", "content": system}] + messages
    resp = requests.post(
        "http://localhost:11434/api/chat",
        json={
            "model": model,
            "messages": formatted_messages,
            "stream": False,
            "options": {"temperature": 0.0}
        },
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()

def _call_splunk_hosted(system: str, messages: List[Dict[str, str]], endpoint: str) -> str:
    """Sends a chat request to the Splunk Hosted Models endpoint."""
    formatted_messages = [{"role": "system", "content": system}] + messages
    resp = requests.post(
        endpoint,
        json={"messages": formatted_messages, "max_tokens": 250},
        headers={"Authorization": f"Bearer {os.getenv('SPLUNK_TOKEN')}"},
        timeout=30
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"].strip()

def _call_anthropic(system: str, messages: List[Dict[str, str]]) -> str:
    """Invokes Anthropic's Claude API with chat history."""
    import anthropic
    c = anthropic.Anthropic()
    msg = c.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=250,
        system=system,
        messages=messages
    )
    return msg.content[0].text.strip()

def _call_openai(system: str, messages: List[Dict[str, str]]) -> str:
    """Invokes OpenAI's GPT API with chat history."""
    from openai import OpenAI
    c = OpenAI()
    formatted_messages = [{"role": "system", "content": system}] + messages
    resp = c.chat.completions.create(
        model="gpt-4o-mini",
        max_tokens=250,
        messages=formatted_messages,
        temperature=0.0
    )
    return resp.choices[0].message.content.strip()
