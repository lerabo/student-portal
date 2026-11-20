"""Застосунок FastAPI: маршрути для інших систем університету."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from portal_api.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = create_async_engine(settings.database_url, echo=settings.echo_sql)
        app.state.sessions = async_sessionmaker(engine, expire_on_commit=False)
        yield
        await engine.dispose()

    app = FastAPI(
        title="Student Portal API",
        version="0.10.0",
        summary="Студенти й оцінки для інших систем університету",
        lifespan=lifespan,
    )
    app.state.settings = settings
    return app


app = create_app()
