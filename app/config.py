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

EMAIL_USER = os.getenv("EMAIL_USERNAME")
EMAIL_PASS = os.getenv("EMAIL_PASSWORD")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
SERVER = os.getenv("SERVER")




