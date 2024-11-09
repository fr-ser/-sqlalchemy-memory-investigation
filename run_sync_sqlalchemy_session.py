import tracemalloc

from helpers import print_current_memory_usage, print_tracemalloc_top

print_current_memory_usage("Start")

import sqlalchemy as sa
import sqlalchemy.orm as sa_orm

from models import DbModel

print_current_memory_usage("After imports")
tracemalloc.start()
engine = sa.create_engine("postgresql+psycopg://user:password@localhost:5432/db")


storage = {}
with sa_orm.Session(engine) as session:
    print_current_memory_usage("Session connected")
    query_result = session.execute(sa.select(DbModel))
    for index, row in enumerate(query_result.scalars()):
        if index == 0:
            print_current_memory_usage("Result iteration start")
        storage[row.id] = row
    print_current_memory_usage("Result iteration end")

print_tracemalloc_top()
