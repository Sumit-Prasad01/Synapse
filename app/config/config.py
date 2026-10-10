import os 
from dotenv import load_dotenv

load_dotenv()


class Settings:

    groq_api_key : str = os.getenv("GROQ_API_KEY")
    port : str = os.getenv("PORT")
    database_name : str = os.getenv("DATABASE")
    host : str = os.getenv("HOST")
    user : str = os.getenv("USER")
    password : str = os.getenv("PASSWORD")


settings = Settings()