"""
Factory Pattern: returns the correct LLM adapter based on system_config.
Callers do not need to know which adapter they are using.
"""

from app.llm.base_adapter import LLMAdapter

SUPPORTED_PROVIDERS = ("gemini", "groq")


def get_llm_adapter(db) -> LLMAdapter:
    """
    Loads provider and API key from the system_config table.
    Returns the appropriate LLMAdapter subclass.
    Raises ValueError if the provider is not supported or if the API key is missing.
    """
    config = _load_system_config(db)
    if not config:
        raise ValueError("System configuration not found.")

    if not config.llm_api_key or config.llm_api_key.strip() == "":
        raise ValueError("LLM API key is not set or is empty. Please configure it in System Configuration.")

    if config.llm_provider == "gemini":
        from app.llm.gemini_adapter import GeminiAdapter
        return GeminiAdapter(api_key=config.llm_api_key)

    if config.llm_provider == "groq":
        from app.llm.groq_adapter import GroqAdapter
        return GroqAdapter(api_key=config.llm_api_key)

    raise ValueError(
        f"Unknown LLM provider: '{config.llm_provider}'. "
        f"Supported: {', '.join(SUPPORTED_PROVIDERS)}"
    )


def _load_system_config(db):
    from app.models.system_config import SystemConfig
    return db.query(SystemConfig).filter(SystemConfig.id == 1).first()
