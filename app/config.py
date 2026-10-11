from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    nebius_api_key: str = ""
    nebius_base_url: str = "https://api.tokenfactory.nebius.com/v1"
    reasoning_model: str = "nvidia/Nemotron-3-Ultra-550b-a55b"
    fallback_model: str = "nvidia/nemotron-3-super-120b-a12b"
    model_timeout_s: float = 30.0
    # "nebius" = Ultra, then Super, then keyword rules; "mock" = keyword rules only, no API calls.
    provider: str = "nebius"
    tavily_api_key: str = ""

    # Email (alerts + "Is this you?"), any SMTP; defaults are Gmail with an app password.
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_pass: str = ""
    # Demo contacts use @example.com (no real inbox): their mail goes here instead, if set.
    email_demo_redirect_to: str = ""
    # Emails go ONLY to these addresses (comma-separated) plus the demo redirect. Closed by
    # default, so a public server can't be used to email strangers from this account.
    email_allowed_to: str = ""
    # Where links in emails point (the "Is this you?" answer page).
    public_base_url: str = "http://localhost:5180"

    # Live calls at once (each one runs model checks on our credits).
    max_live_calls: int = 3

    # Speech service on the Nebius GPU (asr/server.py): Parakeet + Sortformer. Empty = off.
    asr_url: str = ""
    asr_token: str = ""
    asr_timeout_s: float = 120.0

    # Vobiz phone line. Empty secret = the line is off (its routes answer 404).
    vobiz_secret: str = ""
    vobiz_number: str = ""  # shown on the dashboard while it waits for a call


settings = Settings()
