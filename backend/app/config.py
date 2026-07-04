from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    perenual_api_key: str = ""
    perenual_free_tier_max_page: int = 100
    trefle_api_key: str = ""
    session_secret: str
    family_invite_code: str
    environment: str = "development"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()
