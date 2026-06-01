"""
app/core/config.py
Configuration and settings for Nova-AI using pydantic-settings.
"""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    APP_NAME: str = "Nova-AI"
    VERSION: str = "1.0.0"


settings = Settings()
