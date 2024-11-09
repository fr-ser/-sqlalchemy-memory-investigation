import tracemalloc

from helpers import print_current_memory_usage, print_tracemalloc_top

print_current_memory_usage("Start")

import sqlalchemy as sa

from models import DbModel

print_current_memory_usage("After imports")
tracemalloc.start()
engine = sa.create_engine("postgresql+psycopg://user:password@localhost:5432/db")


storage = {}
with engine.connect() as conn:
    print_current_memory_usage("Engine connected")
    query_result = conn.execute(sa.select(DbModel))
    for index, row in enumerate(query_result):
        if index == 0:
            print_current_memory_usage("Result iteration start")
        storage[row.id] = row
    print_current_memory_usage("Result iteration end")


print_tracemalloc_top()
