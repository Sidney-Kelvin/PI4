from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", protected_namespaces=())

    database_url: str = "postgresql://finantrack:finantrack@localhost:5432/finantrack"
    secret_key: str = "dev-secret-key"
    environment: str = "development"
    app_name: str = "FinanTrack API"
    app_version: str = "2.0.0"

    # Origens liberadas no CORS (separadas por vírgula). Em Docker o frontend usa o
    # proxy do nginx (mesma origem), então isso só importa no desenvolvimento com Vite.
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    # Pasta com os CSVs brutos do Rossmann (train.csv, store.csv, test.csv)
    data_dir: str = "../data"
    # Pasta onde o modelo LSTM treinado é salvo/carregado
    model_dir: str = "../models/sales_lstm"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
