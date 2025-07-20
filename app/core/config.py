import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # * langsmith setting
    langsmith_tracing: str
    langsmith_endpoint: str
    langsmith_api_key: str
    langsmith_project: str

    # * llm api settings
    openai_api_key: str
    google_api_key: str
    mistral_api_key: str

    embedding_model: str = "models/text-embedding-004"
    chat_model: str = "gemini-2.5-flash-preview-05-20"
    # * huggingface token
    huggingface_token: str

    # * postgresql - sql database
    postgres_server: str = "localhost"
    postgres_port: str = "5432"
    postgres_user: str = "myuser"
    postgres_password: str = "mypassword"
    postgres_db: str = "simple-rag-db"

    # * qdrant - vector database settings
    qdrant_server: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url: str = f"http://{qdrant_server}:{qdrant_port}"
    qdrant_collection_name: str = "demo_collection"
    embedding_size: int = 768

    # * chunking settings
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5

    # * api settings
    api_host: str = "0.0.0.0"
    api_port: int = 8080

    # * file settings
    root_dir: str
    data_dir: str
    upload_dir: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        os.makedirs(self.upload_dir, exist_ok=True)


settings = Settings()
