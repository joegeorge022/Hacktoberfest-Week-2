import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    app_name: str = "HustlePulse AI"
    app_version: str = "1.0.0"
    app_description: str = "Open-Source AI Copilot for Indie Sellers & Side-Hustlers"
    
    # Gemma settings
    gemma_provider: str = os.getenv("GEMMA_PROVIDER", "auto")  # auto, ollama, huggingface, fallback
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    gemma_model: str = os.getenv("GEMMA_MODEL", "gemma2:2b")
    hf_token: Optional[str] = os.getenv("HF_TOKEN", None)
    hf_model_id: str = os.getenv("HF_MODEL_ID", "google/gemma-2-2b-it")
    
    # TabPFN settings
    tabpfn_api_key: Optional[str] = os.getenv("TABPFN_API_KEY", None)
    use_local_tabpfn: bool = True
    
    # ElevenLabs settings
    elevenlabs_api_key: Optional[str] = os.getenv("ELEVENLABS_API_KEY", None)
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
    
    # Sentry instrumentation
    sentry_dsn: Optional[str] = os.getenv("SENTRY_DSN", None)
    environment: str = os.getenv("ENVIRONMENT", "development")

    model_config = {"env_file": ".env", "extra": "ignore"}

settings = Settings()
