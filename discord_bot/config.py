from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DISCORD_BOT_TOKEN: str
    DISCORD_USER_ID: str   # Your numeric Discord user ID
    ANTHROPIC_API_KEY: str
    SUPABASE_URL: str
    SUPABASE_KEY: str

    class Config:
        env_file = ".env"


settings = Settings()
