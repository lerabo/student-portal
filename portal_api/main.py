"""Застосунок FastAPI: маршрути для інших систем університету."""

import secrets
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query, Request
from fastapi.security import APIKeyHeader
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from portal_api import orm
from portal_api.schemas import GradeIn, GradeOut, RankingItem, StudentOut, StudentPage
from portal_api.settings import Settings
from student_portal.group import Group

api_key_header = APIKeyHeader(
    name="X-API-Key", description="Ключ з PORTAL_API_KEY", auto_error=False
)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Сесія бази даних на один запит; закривається після відповіді."""
    async with request.app.state.sessions() as session:
        yield session


async def check_api_key(
    request: Request, key: Annotated[str | None, Depends(api_key_header)]
) -> None:
    expected = request.app.state.settings.api_key.get_secret_value()
    if key is None or not secrets.compare_digest(key, expected):
        raise HTTPException(401, "Неправильний ключ API")


SessionDep = Annotated[AsyncSession, Depends(get_session)]
NOT_FOUND = {404: {"description": "Студента немає"}}

router = APIRouter(dependencies=[Depends(check_api_key)])


@router.get("/students")
async def list_students(
    session: SessionDep,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> StudentPage:
    """Студенти сторінками разом з оцінками, за id."""
    count = await session.scalar(select(func.count()).select_from(orm.Student))
    students = await session.scalars(
        select(orm.Student)
        .options(selectinload(orm.Student.grades))
        .order_by(orm.Student.id)
        .limit(limit)
        .offset(offset)
    )
    return StudentPage(
        count=count or 0,
        items=[StudentOut.model_validate(s) for s in students],
    )


async def find_student(session: AsyncSession, student_id: int) -> orm.Student:
    student = await session.get(
        orm.Student, student_id, options=[selectinload(orm.Student.grades)]
    )
    if student is None:
        raise HTTPException(404, f"Студента з id={student_id} немає")
    return student


@router.get("/students/{student_id}", responses=NOT_FOUND)
async def get_student(student_id: int, session: SessionDep) -> StudentOut:
    """Картка студента з оцінками і середнім балом."""
    return StudentOut.model_validate(await find_student(session, student_id))


@router.post("/students/{student_id}/grades", status_code=201, responses=NOT_FOUND)
async def add_grade(student_id: int, grade: GradeIn, session: SessionDep) -> GradeOut:
    """Нова оцінка студента, наприклад за тест у системі дистанційного навчання."""
    await find_student(session, student_id)
    record = orm.Grade(student_id=student_id, **grade.model_dump())
    session.add(record)
    await session.commit()
    return GradeOut.model_validate(record)


async def load_group(session: AsyncSession) -> Group:
    """Усі студенти бази даних як група ядра: правила лишаються в ядрі."""
    students = await session.scalars(
        select(orm.Student).options(selectinload(orm.Student.grades))
    )
    group = Group("усі студенти")
    for student in students:
        group.add(orm.to_core(student))
    return group


@router.get("/ranking")
async def ranking(
    session: SessionDep, limit: Annotated[int, Query(ge=1, le=100)] = 10
) -> list[RankingItem]:
    """Рейтинг за середнім балом, як на сайті; студенти без оцінок - у кінці."""
    group = await load_group(session)
    return [
        RankingItem(place=place, id=s.id, full_name=s.full_name, average=s.average())
        for place, s in enumerate(group.ranking()[:limit], start=1)
    ]


@router.get("/stats/ects")
async def ects_stats(session: SessionDep) -> dict[str, int]:
    """Варіант 2: скільки оцінок кожної літери ECTS; порожня база - порожній словник."""
    group = await load_group(session)
    return group.ects_distribution()


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
    app.include_router(router)
    return app


app = create_app()
