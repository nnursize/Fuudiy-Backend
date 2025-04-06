from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME", "fuudiy")
SECRET_KEY = os.getenv("SECRET_KEY")

COLLECTION_FOOD = os.getenv("COLLECTION_FOOD")
COLLECTION_SURVEY = os.getenv("COLLECTION_SURVEY")
COLLECTION_USER_COMMENTS = os.getenv("COLLECTION_USER_COMMENTS")

CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")