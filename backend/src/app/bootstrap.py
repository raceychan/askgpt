from sqlalchemy.ext import asyncio as sa_aio

from src.infra.schema import EventSchema, UserSchema


async def bootstrap(aioengine: sa_aio.AsyncEngine):
    await EventSchema.create_table_async(aioengine)
    await EventSchema.assure_table_exist(aioengine)
    await UserSchema.create_table_async(aioengine)
    await UserSchema.assure_table_exist(aioengine)
