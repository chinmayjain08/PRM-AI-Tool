"""
Abstract base class for all LLM adapters.

Adapter Pattern: all LLM providers implement the same interface.
Open/Closed Principle: add a new provider without modifying existing adapters.
"""


class LLMAdapter:
    """Defines the contract every LLM adapter must follow."""

    def complete(self, prompt: str) -> str:
        """
        Sends the prompt to the LLM and returns the response text.
        Subclasses must implement this method.
        """
        raise NotImplementedError("Subclasses must implement complete()")
