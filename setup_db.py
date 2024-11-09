import psycopg

with psycopg.connect("postgres://user:password@localhost:5432/db") as conn:
    with conn.cursor() as cursor:
        cursor.execute("DROP TABLE IF EXISTS data")
        cursor.execute(
            """
            CREATE TABLE data (
                id serial PRIMARY KEY,
                num integer,
                data text
            )
            """
        )
        records = [(10, 20, "hello"), (40, None, "world")]

        with cursor.copy("COPY data (id, num, data) FROM STDIN") as copy:
            for index in range(100_000):
                copy.write_row((index, (index * 5) % 200, f"hello-{index}"))

    conn.commit()
print("DB setup complete")
