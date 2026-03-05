import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
GROQ_API_KEY: str = os.environ["GROQ_API_KEY"]
DATABASE_URL: str = os.environ["DATABASE_URL"]
WEBHOOK_URL: str = os.environ["WEBHOOK_URL"]
PORT: int = int(os.getenv("PORT", 8080))

WEBHOOK_PATH = "/webhook"
WEBAPP_HOST = "0.0.0.0"

# New users start with this many free messages
FREE_MESSAGES = 10

# Premium weekly top-up
PREMIUM_WEEKLY_MESSAGES = 150

GROQ_MODEL = "llama-3.3-70b-versatile"
