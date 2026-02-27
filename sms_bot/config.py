from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str  # Twilio sender number, E.164 e.g. +18005551234
    MY_PHONE_NUMBER: str      # your personal number, E.164 e.g. +14081234567
    ANTHROPIC_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
