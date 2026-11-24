
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

    # Application
    APP_ENV: str = "development"

    # Security / JWT
    SECRET_KEY: str = Field(min_length=32)
    ALGORITHM: str = "HS256"

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 1

    # Cookie security
    COOKIE_SECURE: Optional[bool] = None
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    TRUST_PROXY_HEADERS: bool = False

    # Database
    DATABASE_URL: str

    # WhatsApp Gateway
    FONNTE_TOKEN: str = ""
    FONNTE_API_URL: str = "https://api.fonnte.com/send"

    # Admin Tools
    ADMIN_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=True,
    )

    @field_validator("APP_ENV")
    @classmethod
    def validate_app_env(cls, value: str) -> str:
        value = value.strip().lower()

        allowed = {"development", "testing", "production"}

        if value not in allowed:
            raise ValueError(
                "APP_ENV must be development, testing, or production"
            )

        return value

    @field_validator("ALGORITHM")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        if value != "HS256":
            raise ValueError("Only HS256 is currently supported")

        return value

    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES")
    @classmethod
    def validate_access_expiry(cls, value: int) -> int:
        if value < 1:
            raise ValueError(
                "ACCESS_TOKEN_EXPIRE_MINUTES must be positive"
            )

        return value

    @field_validator("REFRESH_TOKEN_EXPIRE_DAYS")
    @classmethod
    def validate_refresh_expiry(cls, value: int) -> int:
        if value < 1:
            raise ValueError(
                "REFRESH_TOKEN_EXPIRE_DAYS must be positive"
            )

        return value

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in {"lax", "strict", "none"}:
            raise ValueError(
                "COOKIE_SAMESITE must be lax, strict, or none"
            )

        return value

    @field_validator("COOKIE_DOMAIN")
    @classmethod
    def validate_cookie_domain(
        cls,
        value: Optional[str],
    ) -> Optional[str]:
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        if "://" in value or "/" in value:
            raise ValueError(
                "COOKIE_DOMAIN must be a hostname, not a URL"
            )

        return value.lstrip(".")

    @field_validator("ADMIN_API_KEY")
    @classmethod
    def validate_admin_api_key(cls, value: str) -> str:
        return value.strip()

    @model_validator(mode="after")
    def validate_cookie_security(self):
        if self.APP_ENV == "production" and self.COOKIE_SECURE is False:
            raise ValueError(
                "COOKIE_SECURE cannot be false in production"
            )

        if self.COOKIE_SAMESITE == "none" and not self.cookie_secure:
            raise ValueError(
                "COOKIE_SAMESITE=none requires COOKIE_SECURE=true"
            )

        return self

    @property
    def cookie_secure(self) -> bool:
        if self.APP_ENV == "production":
            return True

        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE

        return False

    @property
    def cors_origins_list(self) -> list[str]:
        return [
            origin.strip().rstrip("/")
            for origin in self.CORS_ORIGINS.split(",")
            if origin.strip()
        ]


settings = Settings()
