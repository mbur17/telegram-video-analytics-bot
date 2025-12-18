import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = os.getenv('TELEGRAM_BOT_TOKEN', '')
    # Database
    DATABASE_URL: str = os.getenv(
        'DATABASE_URL',
        'postgresql+asyncpg://user:password@localhost:5432/video_analytics'
    )
    # LLM Configuration
    LLM_PROVIDER: str = os.getenv('LLM_PROVIDER', 'anthropic')
    ANTHROPIC_API_KEY: str = os.getenv('ANTHROPIC_API_KEY', '')
    LLM_MODEL: str = os.getenv('LLM_MODEL', 'claude-sonnet-4-20250514')

    def validate(self):
        """Validate that required settings are present."""
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError('TELEGRAM_BOT_TOKEN is required')
        if not self.ANTHROPIC_API_KEY:
            raise ValueError(
                'ANTHROPIC_API_KEY is required when using Anthropic'
            )


settings = Settings()
