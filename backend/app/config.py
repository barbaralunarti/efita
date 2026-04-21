# backend/app/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Database
    DATABASE_URL: str = "sqlite:///./efita.db"

    # JWT
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # SMTP
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "EFITA Coordenação <efita@ita.br>"

    # App
    PIX_CODE: str = ""
    AGENDA_URL: str = "https://efita.ita.br/agenda"
    FRONTEND_ORIGIN: str = "http://localhost:5173"

    def __init__(self, **data):
        super().__init__(**data)
        # Validar SECRET_KEY em tempo de inicialização
        if self.SECRET_KEY in ["change-me-in-production", "troque-por-uma-chave-secreta-forte"]:
            raise ValueError(
                "⚠️  SEGURANÇA CRÍTICA: SECRET_KEY não pode ser o valor padrão! "
                "Configure uma chave segura em .env (use: secrets.token_urlsafe(32))"
            )


settings = Settings()
