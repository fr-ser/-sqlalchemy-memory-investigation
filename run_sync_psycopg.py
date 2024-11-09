from helpers import print_current_memory_usage, print_tracemalloc_top

print_current_memory_usage("Start")
import tracemalloc

import psycopg

print_current_memory_usage("After imports")
tracemalloc.start()

storage = {}
with psycopg.connect("postgres://user:password@localhost:5432/db") as conn:
    with conn.cursor(row_factory=psycopg.rows.namedtuple_row) as cursor:
        cursor.execute("SELECT * FROM data")

        for index, row in enumerate(cursor):
            if index == 0:
                print_current_memory_usage("Result iteration start")
            storage[row.id] = row
        print_current_memory_usage("Result iteration end")

print_tracemalloc_top()
