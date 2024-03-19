from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    eventlog_server: str
    kerio_server: str
    kerio_username: str
    kerio_password: str
    read_event_timeout_sec: int
    model_config = SettingsConfigDict(env_file=('.env'))
