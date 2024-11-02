import os



class Config:
    OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')
    SEARCH_KEY = os.environ.get('SEARCH_KEY')
    PUBLIC_LLM = "gpt-4o-mini"
    LOCAL_LLM = "llama3.2:1b"
    UPLOAD_PATH = os.path.join(os.path.dirname(__file__), 'uploads')
    SENDER_EMAIL = "arunimsamudra@gmail.com"
    SENDER_NAME = "Arunim Samudra"
    DEBUG = False
    TESTING = False
