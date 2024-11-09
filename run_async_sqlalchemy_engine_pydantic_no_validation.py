import asyncio
import tracemalloc

from helpers import print_current_memory_usage, print_tracemalloc_top

print_current_memory_usage("Start")

import sqlalchemy as sa
import sqlalchemy.ext.asyncio as sa_asyncio

from models import DbModel, DomainModel

print_current_memory_usage("After imports")
tracemalloc.start()


async def main():
    engine = sa_asyncio.create_async_engine(
        "postgresql+psycopg://user:password@localhost:5432/db"
    )

    storage = {}
    async with engine.connect() as conn:
        print_current_memory_usage("Engine connected")
        query_result = await conn.stream(sa.select(DbModel))
        index = -1
        async for row in query_result:
            index += 1
            if index == 0:
                print_current_memory_usage("Result iteration start")
            storage[row.id] = DomainModel.model_construct(row)
        print_current_memory_usage("Result iteration end")

    print_tracemalloc_top()


asyncio.run(main())
