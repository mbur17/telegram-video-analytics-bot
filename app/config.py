import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    def __init__(self):
        # Telegram Bot
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')

        # PostgreSQL - Admin credentials for migrations and data load
        self.POSTGRES_ADMIN_USER = os.getenv('POSTGRES_ADMIN_USER', 'admin')
        self.POSTGRES_ADMIN_PASSWORD = os.getenv(
            'POSTGRES_ADMIN_PASSWORD', 'admin_password'
        )

        # PostgreSQL - Readonly credentials for bot
        self.POSTGRES_READONLY_USER = os.getenv(
            'POSTGRES_READONLY_USER', 'readonly_user'
        )
        self.POSTGRES_READONLY_PASSWORD = os.getenv(
            'POSTGRES_READONLY_PASSWORD', 'readonly_password'
        )

        # PostgreSQL - Common settings
        self.POSTGRES_DB = os.getenv('POSTGRES_DB', 'video_analytics')
        self.POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'postgres')
        self.POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', '5432'))

        # Ollama
        self.OLLAMA_BASE_URL = os.getenv(
            'OLLAMA_BASE_URL', 'http://ollama:11434'
        )
        self.OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'sqlcoder:latest')

        self.validate()

    def validate(self):
        """Validate that required settings are present."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError('TELEGRAM_BOT_TOKEN is required')
        if not self.OLLAMA_BASE_URL:
            raise ValueError('OLLAMA_BASE_URL is required')
        if not self.OLLAMA_MODEL:
            raise ValueError('OLLAMA_MODEL is required')

    @property
    def DATABASE_URL_ADMIN(self) -> str:
        """Database URL with admin credentials for migrations and data load."""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_ADMIN_USER}:'
            f'{self.POSTGRES_ADMIN_PASSWORD}@'
            f'{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/'
            f'{self.POSTGRES_DB}'
        )

    @property
    def DATABASE_URL_READONLY(self) -> str:
        """Database URL with readonly credentials for bot queries."""
        return (
            f'postgresql+asyncpg://{self.POSTGRES_READONLY_USER}:'
            f'{self.POSTGRES_READONLY_PASSWORD}@'
            f'{self.POSTGRES_HOST}:'
            f'{self.POSTGRES_PORT}/'
            f'{self.POSTGRES_DB}'
        )


settings = Settings()
