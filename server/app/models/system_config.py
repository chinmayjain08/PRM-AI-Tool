from sqlalchemy import Column, Integer, String, Text
from app.core.database import Base


class SystemConfig(Base):
    """Single-row configuration table. Always id = 1."""
    __tablename__ = "system_config"

    id                 = Column(Integer, primary_key=True, default=1)
    llm_provider       = Column(String(50), default="gemini")
    llm_api_key        = Column(Text)
    scheduler_interval = Column(Integer, default=4)    # hours
    max_weekly_hours   = Column(Integer, default=40)
