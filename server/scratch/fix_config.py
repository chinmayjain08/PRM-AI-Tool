import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.system_config import SystemConfig

def fix_config():
    db = SessionLocal()
    try:
        config = db.query(SystemConfig).filter(SystemConfig.id == 1).first()
        if config:
            config.llm_provider = "ollama"
            db.commit()
            print("Successfully updated system config back to 'ollama'!")
    finally:
        db.close()

if __name__ == "__main__":
    fix_config()
