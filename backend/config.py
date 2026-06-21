from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    mongodb_uri: str = "mongodb://localhost:27017"
    db_name: str = "upsc_quiz"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "gpt-oss:120b-cloud"
    ollama_api_key: str = ""
    upload_dir: str = "/tmp/upsc_uploads"

    class Config:
        env_file = ".env"

settings = Settings()
