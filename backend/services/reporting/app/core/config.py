import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "A11ySense Reporting Service"
    ALLURE_RESULTS_DIR: str = os.getenv("ALLURE_RESULTS_DIR", "storage/reports/allure-results")
    
    class Config:
        env_file = ".env"

settings = Settings()
