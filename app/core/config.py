from dataclasses import dataclass
from os import getenv


@dataclass(frozen=True)
class Settings:
    app_name: str = getenv("APP_NAME", "quant-lab")
    app_env: str = getenv("APP_ENV", "local")
    auth_secret: str = getenv("AUTH_SECRET", "change-this-demo-secret")
    demo_username: str = getenv("DEMO_USERNAME", "demo")
    demo_password: str = getenv("DEMO_PASSWORD", "demo-pass")
    token_expire_seconds: int = int(getenv("TOKEN_EXPIRE_SECONDS", "3600"))


settings = Settings()
