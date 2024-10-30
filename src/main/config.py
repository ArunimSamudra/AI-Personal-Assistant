import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'default_secret_key'
    SENDER_EMAIL = "arunimsamudra@gmail.com"
    SENDER_PW = "jslb mylh cshd nrqc"
    DEBUG = False
    TESTING = False
