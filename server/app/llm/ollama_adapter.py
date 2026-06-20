"""
Ollama implementation of LLMAdapter.

Works with any Ollama-compatible endpoint (local or hosted).
Hosted Gemma endpoint: http://164.52.211.238/api/generate

The /api/generate endpoint accepts:
  POST { "model": "gemma", "prompt": "...", "stream": false }
  Returns: { "response": "...", ... }

If an API key is configured it is sent as:
  Authorization: Bearer <key>
"""

import requests
from app.llm.base_adapter import LLMAdapter
from app.core.config import settings


class OllamaAdapter(LLMAdapter):
    """Calls any Ollama-compatible /api/generate endpoint."""

    def __init__(self, api_key: str = "") -> None:
        self.api_key  = api_key or ""
        self.host     = settings.OLLAMA_HOST        # e.g. http://164.52.211.238/api/generate
        self.model    = settings.OLLAMA_MODEL       # e.g. "gemma"
        self.timeout  = 60                          # seconds

    def complete(self, prompt: str) -> str:
        """
        Sends the prompt to the Ollama /api/generate endpoint and returns the response text.
        Uses mock responses when api_key == 'mock-key' (for unit tests — no HTTP call made).
        """
        # ── Fast-path for unit tests ──────────────────────────────────────
        if self.api_key == "mock-key":
            if "Project Requirement:" in prompt:
                return (
                    '[{"name": "Developer Employee One", '
                    '"reason": "Has advanced Python skills and 40 hrs/week capacity.", '
                    '"suggested_allocation_pct": 50}]'
                )
            return (
                "The project has an overdue milestone and low effort logged last week. "
                "The manager should prioritise addressing these blockers immediately."
            )

        # ── Real HTTP call ────────────────────────────────────────────────
        headers = {"Content-Type": "application/json"}
        if self.api_key.strip():
            headers["apikey"] = self.api_key

        payload = {
            "model":  self.model,
            "prompt": prompt,
            "stream": False,       # get the full response in one HTTP response
        }

        response = requests.post(
            self.host,
            json    = payload,
            headers = headers,
            timeout = self.timeout,
        )
        response.raise_for_status()          # raises HTTPError on 4xx / 5xx
        data = response.json()
        return data.get("response", "").strip()
