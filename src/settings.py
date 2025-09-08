import os

from dotenv import load_dotenv

load_dotenv()

settings = {
    "TELEGRAM_TOKEN": os.getenv("TELEGRAM_TOKEN"),
    "DB_STRING": os.getenv("DB_STRING"),
}
