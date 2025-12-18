import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
)

from app.config import settings

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""

    def __init__(self):
        self.engine: AsyncEngine | None = None
        self.session_factory: async_sessionmaker[AsyncSession] | None = None

    def init(self):
        """Initialize database engine and session factory."""
        if self.engine is not None:
            return
        logger.info(
            f'Connecting to database: {settings.DATABASE_URL.split("@")[-1]}'
        )
        self.engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
        logger.info("Database connection initialized")

    async def close(self):
        """Close database connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info('Database connection closed')

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if self.session_factory is None:
            raise RuntimeError('Database not initialized. Call init() first.')
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    async def execute_raw_query(self, query: str) -> int:
        """Execute a raw SQL query and return a single numeric result."""
        async with self.session() as session:
            result = await session.execute(text(query))
            row = result.fetchone()
            if row is None:
                return 0
            # Return the first column of the first row
            return int(row[0]) if row[0] is not None else 0


db = Database()
