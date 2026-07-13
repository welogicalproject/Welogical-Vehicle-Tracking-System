import os
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# App settings configuration
class Settings(BaseSettings):
    # App settings
    APP_NAME: str = "Vehicle Tracking System Backend"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Telemetry Simulator settings
    SIMULATOR_ENABLED: bool = False
    SIMULATOR_MODE: str = "cloud"
    SIMULATOR_DEVICE_UIDS: str = "ESP32-DEMO-001,ESP32-DEMO-002,ESP32-DEMO-003"
    SIMULATOR_SEND_INTERVAL: float = 10.0
    SIMULATOR_SPEED_MULTIPLIER: float = 1.0
    SIMULATOR_LOOP_ROUTE: bool = True
    # Auto-register vehicle DB records on startup when missing
    SIMULATOR_AUTO_REGISTER: bool = True
    # Seconds between health watchdog checks (restarts crashed twins)
    SIMULATOR_HEALTH_CHECK_INTERVAL: int = 30

    # Database settings
    DATABASE_URL: str = "postgresql://postgres.pjeghxryyftkljhrglfw:atyainno%40123@aws-0-ap-northeast-1.pooler.supabase.com:5432/postgres"
    ASYNC_DATABASE_URL: str = ""

    # Logging settings
    LOG_LEVEL: str = "INFO"

    # Trip configuration thresholds
    TRIP_START_SPEED_THRESHOLD: float = 5.0
    TRIP_END_SPEED_THRESHOLD: float = 1.5
    TRIP_END_TIMEOUT: int = 300
    TRIP_GAP_TIMEOUT: int = 600
    DEFAULT_SPEED_LIMIT: float = 80.0

    # Trip analytics thresholds
    TRIP_STOP_SPEED: float = 3.0
    TRIP_STOP_DURATION: int = 120
    OVERSPEED_LIMIT: float = 80.0

    # Driving score penalties
    DRIVING_SCORE_START: int = 100
    DRIVING_SCORE_OVERSPEED_PENALTY: int = 5
    DRIVING_SCORE_IDLE_PENALTY: int = 2
    DRIVING_SCORE_MIN: int = 0

    # Google Routes integration settings (Phase 1: configuration only)
    GOOGLE_ROUTES_ENABLED: bool = False
    GOOGLE_ROUTES_API_KEY: str = ""
    GOOGLE_ROUTES_MONTHLY_LIMIT: int = 9500
    GOOGLE_ROUTES_WARNING_THRESHOLD: int = 8000
    GOOGLE_ROUTES_TIMEOUT_SECONDS: int = 5
    GOOGLE_ROUTES_PROVIDER: str = "google"
    SAVE_RAW_GOOGLE_RESPONSES: bool = False


    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def validate_database_urls(self) -> "Settings":
        # 1. Standardize DATABASE_URL schema: replace postgres:// with postgresql:// if needed
        # SQLAlchemy 1.4/2.0 requires postgresql:// instead of postgres://
        if self.DATABASE_URL.startswith("postgres://"):
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
        # 2. Derive ASYNC_DATABASE_URL if empty or not set
        if not self.ASYNC_DATABASE_URL:
            if self.DATABASE_URL.startswith("postgresql://"):
                self.ASYNC_DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
            elif self.DATABASE_URL.startswith("postgres://"):
                self.ASYNC_DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
            else:
                self.ASYNC_DATABASE_URL = self.DATABASE_URL
        else:
            # Standardize ASYNC_DATABASE_URL schema
            if self.ASYNC_DATABASE_URL.startswith("postgres://"):
                self.ASYNC_DATABASE_URL = self.ASYNC_DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
            elif self.ASYNC_DATABASE_URL.startswith("postgresql://"):
                self.ASYNC_DATABASE_URL = self.ASYNC_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self


settings = Settings()

