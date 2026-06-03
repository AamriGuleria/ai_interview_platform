from contextlib import asynccontextmanager, contextmanager
import logging
from typing import Optional
from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine
    )
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.orm import Session, sessionmaker

from core.config import config

logger = logging.getLogger(__name__)

class SessionManager():
    def __init__(
        self,
        database_url: Optional[str] = None,
        async_database_url: Optional[str] = None,
        echo: bool = False,  # Log all SQL statements
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        pool_pre_ping: bool = True,
        pool_use_lifo: bool = True,
    ):
        """
        Args:
            database_url: Sync database URL (e.g., postgresql://...)
            async_database_url: Async database URL (e.g., postgresql+asyncpg://...)
            echo: Log all SQL statements
            pool_size: Number of connections to keep pooled
            max_overflow: Maximum connections above pool_size
            pool_recycle: Recycle connections after N seconds
            pool_pre_ping: Check connection is alive before use
            pool_use_lifo: Use recently opened connections
        """
        self.database_url = database_url
        self.async_database_url = async_database_url
        self.echo = echo
        
        # Pool configuration
        self.pool_config = {
            "pool_size": pool_size,
            "max_overflow": max_overflow,
            "pool_recycle": pool_recycle,
            "pool_pre_ping": pool_pre_ping,
            "pool_use_lifo": pool_use_lifo,
        }

        self.sync_engine: Optional[Engine] = None
        self.async_engine: Optional[AsyncEngine] = None
        self.sync_session_factory: Optional[sessionmaker] = None
        self.async_session_factory: Optional[async_sessionmaker] = None

    def _setup_sync_engine(self) -> None:
        if self.sync_engine is not None:
            return 
        
        if not self.database_url:
            raise ValueError("database_url must be provided for sync operations")
        
        try:
            self.sync_engine = create_engine(
                self.database_url,
                echo=self.echo,
                autocommit=False,
                autoflush=False,
                **self.pool_config,
            )
            logger.info("Sync engine initialized successfully")
            
        except Exception as e:
            logger.error(f" Failed to create sync engine: {e}")
            raise

    def _setup_async_engine(self)-> None:
        if self.async_engine is not None:
            return
        
        if not self.async_database_url:
            raise ValueError("Async Database Url must be provided for Async Operation")
        
        try:
            self.async_engine = create_async_engine(
                self.async_database_url,
                echo=self.echo,
                autocommit=False,
                autoflush=False,
                poolclass=AsyncAdaptedQueuePool,
                **self.pool_config,
            )
            logger.info("Async engine initialized successfully")

        except Exception as e:
            logger.error(f"Failed to create async engine: {e}")
    def get_sync_session_factory(self) -> sessionmaker:
        if self.sync_session_factory is None:
            self._setup_sync_engine()
            self.sync_session_factory = sessionmaker(
                self.sync_engine,
                class_=Session,
                expire_on_commit=False,  # Keep objects accessible after commit
                autoflush=False,
                autocommit=False,
            )
        return self.sync_session_factory
    def get_async_session_factory(self) -> async_sessionmaker:
        if self.async_session_factory is None:
            self._setup_async_engine()
            self.async_session_factory = async_sessionmaker(
                self.async_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autoflush=False,
                autocommit=False,
            )
        return self.async_session_factory
    
    def get_sync_session(self)-> None:
        session_factory = self.get_sync_session_factory()
        return session_factory()
    
    @contextmanager
    def sync_session_scope(self):
        session = self.get_sync_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Sync session rolled back due to: {e}")
            raise
        finally:
            session.close()
            logger.debug("Sync session closed")

    def get_async_session(self) -> AsyncSession:
        """Get a new asynchronous session (use with context manager)."""
        session_factory = self.get_async_session_factory()
        return session_factory()
    @asynccontextmanager
    async def async_session_scope(self):
        async_session = self.get_async_session()
        try:
            yield async_session
            await async_session.commit()
        except Exception as e:
            await async_session.rollback()
            logger.error(f"Async session rolled back due to {e}")
            raise
        finally:
            await async_session.close()
            logger.debug(f"Async Session Closed")


db_manager = SessionManager(
    database_url=config.database_url,
    async_database_url=config.async_database_url,
    echo=config.echo,
    pool_size=config.pool_size,
    max_overflow=config.max_overflow,
    pool_recycle=config.pool_recycle,
    pool_pre_ping=config.pool_pre_ping,
    pool_use_lifo=config.pool_use_lifo,
)
def get_db():
    with db_manager.sync_session_scope() as db:
        yield db

async def get_async_db():
    async with db_manager.async_session_scope() as db:
        yield db