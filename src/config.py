from pydantic import BaseModel, Field
from pydantic_settings import SettingsConfigDict
from typing import ClassVar

CONF_PATH = "config/config.json"

class Config(BaseModel):
    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        json_file=CONF_PATH
    )
    database_url: str = Field(default="server_data/db.sqlite3", env="MPV_SYNC_DATABASE_URL")
    host: str = Field(default="0.0.0.0", env="MPV_SYNC_SERVER_HOST")
    port: int = Field(default=8961, env="MPV_SYNC_SERVER_PORT")
    debug: bool = Field(default=False, env="MPV_SYNC_SERVER_DEBUG")

settings = Config()