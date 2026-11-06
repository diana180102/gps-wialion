from typing import List

from anyio.functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    wialon_host: str
    wialon_token: str = Field(repr=False)  # repr=False: el token no sale en logs
    database_url: str = ""
    jwt_secret: str = Field(default="", repr=False)
    admin_email: str = ""
    admin_password: str = Field(default="", repr=False)
    cors_origins: str = "http://localhost:3000"

    def cors_origins_list(self) -> List[str]:
        return [ o.strip() for o in self.cors_origins.split(",") if o.strip()]

@lru_cache
def get_settings() -> Settings:
    return Settings()