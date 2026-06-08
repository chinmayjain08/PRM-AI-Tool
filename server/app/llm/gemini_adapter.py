"""
Google Gemini implementation of LLMAdapter.
"""

from app.llm.base_adapter import LLMAdapter


class GeminiAdapter(LLMAdapter):
    def __init__(self, api_key: str) -> None:
        self.api_key = api_key
        if api_key != "mock-key":
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel("gemini-pro")

    def complete(self, prompt: str) -> str:
        """Sends prompt to Gemini and returns the response text."""
        if self.api_key == "mock-key":
            if "Project Requirement:" in prompt:
                return '[{"name": "Developer Employee One", "reason": "Has advanced Python skills and 40 hrs/week capacity.", "suggested_allocation_pct": 50}]'
            else:
                return "Project Alpha Portal has an overdue milestone and developer logging low effort. The project manager needs to act on the Design Review milestone immediately."

        response = self._model.generate_content(prompt)
        return response.text
