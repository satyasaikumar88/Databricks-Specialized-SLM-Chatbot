from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore', protected_namespaces=())

    project_name: str = Field(default='databricks-slm')
    model_name: str = Field(default='Qwen/Qwen2.5-0.5B-Instruct')
    base_model_path: str = Field(default=str(ROOT_DIR / 'model' / 'base_model'))
    fine_tuned_model_path: str = Field(default=str(ROOT_DIR / 'model' / 'qwen2.5-0.5B-databricks-lora'))
    rag_index_path: str = Field(default=str(ROOT_DIR / 'model' / 'faiss_index.bin'))
    docs_path: str = Field(default=str(ROOT_DIR / 'data' / 'docs' / 'databricks_docs.json'))
    dataset_path: str = Field(default=str(ROOT_DIR / 'data' / 'databricks_qa.jsonl'))
    use_gpu: bool = Field(default=False)
    api_host: str = Field(default='0.0.0.0')
    api_port: int = Field(default=8000)
    frontend_url: str = Field(default='http://localhost:3000')
    hf_home: str = Field(default=str(ROOT_DIR / '.cache' / 'huggingface'))
    hf_token: str | None = Field(default=None)
    database_path: str = Field(default=str(ROOT_DIR / 'data' / 'users.db'))
    jwt_secret: str = Field(default='change-this-development-secret')
    jwt_algorithm: str = Field(default='HS256')
    access_token_expire_minutes: int = Field(default=480)


settings = Settings()
