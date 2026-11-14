from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application
    APP_ENV: str = "development"

    # Security / JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    # 12 jam: cukup untuk satu hari pameran, tapi sesi tidak hidup selamanya.
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 720

    # Rate limiting (slowapi). Bisa dimatikan saat load-test lokal.
    RATE_LIMIT_ENABLED: bool = True

    # Database
    DATABASE_URL: str

    # WhatsApp Gateway (Fonnte)
    FONNTE_TOKEN: str = ""
    FONNTE_API_URL: str = "https://api.fonnte.com/send"

    # Admin Tools
    ADMIN_API_KEY: str = "sobatlambung_it_2026"

    # CORS (dipisah koma)
    CORS_ORIGINS: str = ("*")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        """Ubah string CORS_ORIGINS menjadi list yang siap dipakai middleware."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
