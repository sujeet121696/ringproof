from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1"
    reasoning_model: str = "nvidia/Nemotron-3-Ultra-550b-a55b"
    fallback_model: str = "nvidia/nemotron-3-super-120b-a12b"
    model_timeout_s: float = 30.0
    # "nebius" = Ultra with Super fallback; "mock" = deterministic rules, no API calls.
    provider: str = "nebius"
    tavily_api_key: str = ""


settings = Settings()
