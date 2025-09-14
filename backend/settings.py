import os
from dotenv import load_dotenv
load_dotenv()

class Settings:
    ENV = os.getenv("AURORA_ENV", "dev")
    INDEX_VERSION = os.getenv("AURORA_INDEX_VERSION", "v1")

    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # DB: MySQL (via PyMySQL for SSL support)
    DB_URL = os.getenv("AURORA_DB_URL", "mysql+pymysql://aurora_user:aurora_pass@localhost:3306/aurora_db?charset=utf8mb4")

    # Security / integrity
    HMAC_KEY = os.getenv("AURORA_HMAC_KEY", "dev-only-not-secret")

    SERVICE_NAME = "aurora-api"

settings = Settings()