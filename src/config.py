from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "sports"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Pydantic config 
    model_config: SettingsConfigDict = SettingsConfigDict(
        env_file=".env",          
        env_file_encoding="utf-8",
        case_sensitive=False,     
        extra="ignore",          
    )


settings = Settings() 
