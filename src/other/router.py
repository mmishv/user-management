from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from logs.logs import configure_logger
from src.database import create_async_session, get_db
from src.models import Group

router = APIRouter()
logger = configure_logger(__name__)


@router.get("/healthcheck/")
async def health_check():
    logger.info("Health check endpoint accessed")
    return {"result": "You've successfully checked your health!"}


@router.get("/groups/")
async def read_groups(db_session: AsyncSession = Depends(create_async_session)):
    logger.info("Read all groups endpoint accessed")
    async with db_session as conn:
        query = select(Group).options(selectinload(Group.users))
        result = await conn.execute(query)
    return result.scalars().all()


@router.get("/groups/{group_id}")
async def read_group(
    group_id: int, db_session: AsyncSession = Depends(create_async_session)
):
    logger.info(f"Read group with id = {group_id} endpoint accessed")
    async with db_session as conn:
        group = await conn.execute(select(Group).filter(Group.id == group_id))
        group = group.scalar()
        if group is None:
            raise HTTPException(status_code=404)
        return group


@router.post("/groups/")
async def create_group(
    name: str, db_session: AsyncSession = Depends(create_async_session)
):
    logger.info("Create group endpoint accessed")
    async with db_session as conn:
        group = Group(name=name, created_at=datetime.utcnow())
        conn.add(group)
        await conn.commit()
        return group


@router.patch("/groups/{group_id}")
async def update_group_name(
    group_id: int, new_name: str, db_connection: AsyncSession = Depends(get_db)
):
    logger.info(f"Update group with id = {group_id} endpoint accessed")
    query = 'UPDATE "group" SET name = $1 WHERE id = $2 RETURNING *'
    async with db_connection as conn:
        result = await conn.fetchrow(query, new_name, group_id)
        if result is None:
            logger.info(f"Update group with id = {group_id} failed: group not found")
            raise HTTPException(status_code=404)
    return result


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int, db_session: AsyncSession = Depends(create_async_session)
):
    logger.info(f"Delete group with id = {group_id} endpoint accessed")
    async with db_session as conn:
        group = await conn.execute(select(Group).filter(Group.id == group_id))
        group = group.scalar()
        if group is None:
            logger.info(f"Delete group with id = {group_id} failed: group not found")
            raise HTTPException(status_code=404)
        await conn.delete(group)
        await conn.commit()
        return {"message": "Group deleted successfully"}
