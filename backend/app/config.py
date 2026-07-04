from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    database_url: str
    cors_origins: str = "http://localhost:5173"
    # Cola de tareas pesadas (Redis + RQ). Default apunta al Redis local de docker-compose.
    redis_url: str = "redis://localhost:6379/0"
    # Servicio de conversión a PDF (Gotenberg, contenedor con LibreOffice). El worker
    # le hace POST HTTP; no se instala LibreOffice en el host. Default = docker-compose.
    gotenberg_url: str = "http://localhost:3000"
    # Reverse geocoding (Nominatim/OpenStreetMap). Su política EXIGE un User-Agent
    # que identifique la app con un contacto. Cambiar el correo por uno real.
    nominatim_user_agent: str = "GRIN-Inspector/1.0 (contacto@energreen.pe)"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
