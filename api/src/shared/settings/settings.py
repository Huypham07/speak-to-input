from __future__ import annotations

from urllib.parse import quote

from dotenv import find_dotenv
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic_settings import PydanticBaseSettingsSource
from pydantic_settings import YamlConfigSettingsSource

# Load .env file but don't override existing environment variables
load_dotenv(find_dotenv('.env'), override=False)


class PostgresSettings(BaseSettings):
    host: str = Field(default='localhost')
    port: int = Field(default=5432)
    database: str = Field(default='sti_db')
    username: str = Field(default='postgres')
    password: str = Field(default='postgres')
    pool_size: int = Field(default=10)
    min_connections: int = Field(default=5)
    max_connections: int = Field(default=20)

    @property
    def connection_url(self) -> str:
        encoded_password = quote(self.password)
        return f'postgresql+asyncpg://{self.username}:{encoded_password}@{self.host}:{self.port}/{self.database}'

    class Config:
        env_prefix = 'POSTGRES_'


class LLMSettings(BaseSettings):
    provider: str = Field(default='gemini', description='LLM provider: gemini or bedrock')
    api_key: str = Field(default='', description='Google Gemini API key')
    model: str = Field(default='gemini-2.5-flash', description='Gemini model name')

    # AWS Bedrock settings
    aws_region: str = Field(default='us-east-1', description='AWS region for Bedrock')
    aws_access_key_id: str = Field(default='', description='AWS access key ID for Bedrock')
    aws_secret_access_key: str = Field(default='', description='AWS secret access key for Bedrock')

    class Config:
        env_prefix = 'LLM_'


class WhisperSettings(BaseSettings):
    host: str = Field(default='')
    port: int = Field(default=8080)
    host2: str = Field(default='')
    port2: int = Field(default=8081)

    class Config:
        env_prefix = 'WHISPER_'


class Settings(BaseSettings):
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    secret_key: str = Field('secret_key', description='Secret key for JWT and other security operations')
    whisper: WhisperSettings = Field(default_factory=WhisperSettings)
    llm: LLMSettings = Field(default_factory=LLMSettings)

    class Config:
        env_nested_delimiter = '__'
        yaml_file = 'settings.yaml'

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(settings_cls),
        )
