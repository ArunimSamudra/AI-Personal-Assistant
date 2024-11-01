import os


class Config:
    OPEN_AI_KEY = os.environ.get('OPEN_AI_KEY')
    SEARCH_KEY = os.environ.get('SEARCH_KEY')
    SENDER_EMAIL = "arunimsamudra@gmail.com"
    DEBUG = False
    TESTING = False
