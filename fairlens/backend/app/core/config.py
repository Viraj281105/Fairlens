from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    env: str = "development"
    secret_key: str = "default-secret-key"
    
    # External API Keys
    gemini_api_key: str = ""
    
    # GCP / Firebase
    firebase_project_id: str = ""
    firebase_private_key: str = ""
    firebase_client_email: str = ""
    gcs_bucket_name: str = ""
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
