
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
    # Refresh token memakai sliding window: setiap kali /auth/refresh
    # dipanggil, masa berlakunya diperpanjang lagi. Default 7 hari agar
    # pengguna tidak terus-menerus diminta login ulang.
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Cookie security
    # COOKIE_SECURE:
    #   - None  -> otomatis: true di production, false di development
    #   - true  -> paksa Secure (wajib untuk SameSite=None dan HTTPS)
    #   - false -> hanya untuk development (ditolak di production)
    COOKIE_SECURE: Optional[bool] = None
    # COOKIE_SAMESITE:
    #   - "auto" -> pilih "lax" untuk same-site, "none" untuk cross-site
    #   - "lax" / "strict" / "none"
    # SameSite=None otomatis memakai Secure + Partitioned (CHIPS).
    COOKIE_SAMESITE: str = "auto"
    # Isi hanya bila frontend & backend berbagi parent domain,
    # contoh: ".sobatlambung.id". Jangan isi IP/URL/port.
    COOKIE_DOMAIN: Optional[str] = None
    # None -> otomatis (true saat SameSite=None).
    COOKIE_PARTITIONED: Optional[bool] = None

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

        # "test" adalah alias yang dipakai CI, samakan dengan "testing".
        if value == "test":
            return "testing"

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

    @field_validator("COOKIE_SECURE", "COOKIE_PARTITIONED", mode="before")
    @classmethod
    def empty_bool_to_none(cls, value):
        if isinstance(value, str) and not value.strip():
            return None

        return value

    @field_validator("COOKIE_SAMESITE")
    @classmethod
    def validate_cookie_samesite(cls, value: str) -> str:
        value = value.strip().lower()

        if value not in {"auto", "lax", "strict", "none"}:
            raise ValueError(
                "COOKIE_SAMESITE must be auto, lax, strict, or none"
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
