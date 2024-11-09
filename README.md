# Investigation - Memory Usage of SQL Alchemy Selects

This investigation was sparked by an unexpectedly high memory consumption after querying for 92.000 records.

In order to assess the memory behavior of queries for such a data volume this repository has been created.

## Setup

- install Docker (and docker compose)
- install Python
- install poetry
- install python packages: `poetry install --no-root`
- start database: `docker compose up -d`
- add data to database: `poetry run python setup_db.py`

## Observations

These observations are based on the scenarios below.

1. In asynchronous ORM mode SQL Alchemy loads all data into memory at once instead of going row by row.
   This does not affect the total memory consumption if all data is processed in memory but it spikes much faster and
   is likely a bug.
   This behavior can cause issues if actual streaming (processing a row and then not storing the data) is intended.

2. The memory footprint of Pydantic validations (the default) and without (using `model_construct`) is very noticeable.

3. The less intermediate libraries are in the way between the code and database the less memory is used.
   For the database this increases memory from `psycopg` to `SQLAlchemy Core` to `SQLAlchemy ORM`.
   For the data this increases from `python objects` (dictionaries and tuples) to `Pydantic models`.

### Overview

| Scenario | Result Iteration End | Total Allocated Size | Main Memory Sources |
|-|-|-|-|
| Synchronous Psycopg | 98.7 MiB | 19.6 MiB | psycopg2 (14.1 MiB), query results allocation (5.5 MiB) |
| Synchronous Psycopg with Pydantic without validation | 124.3 MiB | 34.7 MiB | psycopg2 (14.1 MiB), Pydantic models (20.6 MiB) |
| Synchronous SQLAlchemy Engine - Core | 145.8 MiB | 31.1 MiB | SQLAlchemy Core (17.3 MiB), connection pool (13.8 MiB) |
| Synchronous SQLAlchemy Session - ORM | 328.2 MiB | 106.5 MiB | ORM mappings (63.2 MiB), session management (43.3 MiB) |
| Asynchronous SQLAlchemy Engine - Core | 139.4 MiB | 31.1 MiB | SQLAlchemy Core (17.3 MiB), async engine (13.8 MiB) |
| Asynchronous SQLAlchemy Session - ORM | 316.8 MiB | 101.5 MiB | ORM mappings (58.2 MiB), async session (43.3 MiB) |
| Asynchronous SQLAlchemy Engine - Core - Pydantic | 197.3 MiB | 64.0 MiB | Pydantic models (34.5 MiB), async engine (29.5 MiB) |
| Asynchronous SQLAlchemy Engine - Core - Pydantic Validation | 194.5 MiB | 64.0 MiB | Pydantic validation (33.0 MiB), async engine (31.0 MiB) |
| Asynchronous SQLAlchemy Engine - Core - Pydantic No Validation | 171.6 MiB | 44.5 MiB | Pydantic models (27.0 MiB), async engine (17.5 MiB) |

## Scenarios

Various scenarios exist to test the memory behavior for different implementation to query for the data.

### Synchronous Psycopg

This approach uses the driver directly (that is indirectly used by SQL Alchemy).

```txt
$ poetry run python run_sync_psycopg.py
Start  - process memory: 14.5 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 31.5 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Result iteration start  - process memory: 45.1 Mib  - trace_malloc: current=0.1 MiB, peak=0.2 MiB
Result iteration end  - process memory: 98.7 Mib  - trace_malloc: current=19.6 MiB, peak=20.3 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/psycopg/cursor.py:234: 7.6 MiB
    return self._tx.load_row(pos, self._make_row)
#2: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/collections/__init__.py:449: 6.9 MiB
    result = tuple_new(cls, iterable)
#3: ./run_sync_psycopg.py:19: 5.0 MiB
    storage[row.id] = row
#4: <frozen importlib._bootstrap_external>:752: 0.0 MiB
#5: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/stringprep.py:24: 0.0 MiB
    b3_exceptions = {
#6: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/stringprep.py:262: 0.0 MiB
    c9_set = set([917505] + list(range(917536,917632)))
#7: ./.venv/lib/python3.12/site-packages/psycopg/_conninfo_utils.py:107: 0.0 MiB
    cd = ParamDef(
#8: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/encodings/idna.py:300: 0.0 MiB
    class StreamWriter(Codec,codecs.StreamWriter):
#9: <frozen abc>:123: 0.0 MiB
#10: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/stringprep.py:220: 0.0 MiB
    c22_specials = set([1757, 1807, 6158, 8204, 8205, 8232, 8233, 65279] + list(range(8288,8292)) + list(range(8298,8304)) + list(range(65529,65533)) + list(range(119155,119163)))
125 other: 0.0 MiB
Total allocated size: 19.6 MiB
```

### Synchronous SQLAlchemy Engine - Core

This approach uses the "low level" SQL Alchemy engine.
It uses the SQLAlchemy "core" approach (in contrast to the ORM approach).

```txt
$ poetry run python run_sync_sqlalchemy_engine.py
Start  - process memory: 14.3 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 60.4 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Engine connected  - process memory: 76.8 Mib  - trace_malloc: current=6.6 MiB, peak=6.7 MiB
Result iteration start  - process memory: 82.6 Mib  - trace_malloc: current=6.7 MiB, peak=6.8 MiB
Result iteration end  - process memory: 145.8 Mib  - trace_malloc: current=31.5 MiB, peak=31.5 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/psycopg/cursor.py:191: 13.7 MiB
    record = self._tx.load_row(self._pos, self._make_row)
#2: ./.venv/lib/python3.12/site-packages/sqlalchemy/engine/result.py:529: 6.1 MiB
    make_row(raw_row) if make_row else raw_row
#3: ./run_sync_sqlalchemy_engine.py:23: 5.0 MiB
    storage[row.id] = row
#4: <frozen importlib._bootstrap_external>:752: 1.9 MiB
#5: <frozen abc>:106: 0.8 MiB
#6: ./.venv/lib/python3.12/site-packages/psycopg/types/array.py:348: 0.2 MiB
    return type(f"{name.title()}{base.__name__}", (base,), attribs)
#7: <frozen abc>:107: 0.1 MiB
#8: ./.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:302: 0.1 MiB
    env.update(vars(mod))
#9: ./.venv/lib/python3.12/site-packages/sqlalchemy/event/attr.py:213: 0.1 MiB
    self._clslevel[target] = collections.deque()
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/sql/schema.py:2159: 0.0 MiB
    self.info = info
4125 other: 3.0 MiB
Total allocated size: 31.1 MiB
```

### Synchronous SQLAlchemy Session - ORM

This approach uses the SQL Alchemy session and the model.
It uses the SQLAlchemy "ORM" approach (in contrast to the core approach).

```txt
$ poetry run python run_sync_sqlalchemy_session.py
Start  - process memory: 14.5 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 59.5 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Session connected  - process memory: 68.7 Mib  - trace_malloc: current=6.4 MiB, peak=6.4 MiB
Result iteration start  - process memory: 328.4 Mib  - trace_malloc: current=115.4 MiB, peak=115.4 MiB
Result iteration end  - process memory: 328.2 Mib  - trace_malloc: current=106.8 MiB, peak=122.9 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:206: 20.6 MiB
    self.expired_attributes = set()
#2: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/instrumentation.py:509: 16.0 MiB
    state = self._state_constructor(instance, self)
#3: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:204: 13.7 MiB
    self.obj = weakref.ref(obj, self._cleanup)
#4: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/instrumentation.py:507: 9.2 MiB
    instance = self.class_.__new__(self.class_)
#5: ./.venv/lib/python3.12/site-packages/psycopg/cursor.py:225: 7.7 MiB
    records = self._tx.load_rows(self._pos, self.pgresult.ntuples, self._make_row)
#6: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:205: 6.1 MiB
    self.committed_state = {}
#7: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/loading.py:1116: 6.1 MiB
    dict_ = instance_dict(instance)
#8: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/loading.py:1080: 6.1 MiB
    identitykey = (
#9: ./run_sync_sqlalchemy_session.py:24: 5.0 MiB
    storage[row.id] = row
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/identity.py:211: 5.0 MiB
    self._dict[key] = state
4185 other: 10.9 MiB
Total allocated size: 106.5 MiB
```

### Asynchronous SQLAlchemy Engine - Core

This approach uses the "low level" SQL Alchemy engine in asynchronous mode.
It uses the SQLAlchemy "core" approach (in contrast to the ORM approach).

```txt
$ poetry run python run_async_sqlalchemy_engine.py
Start  - process memory: 19.9 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 61.8 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Engine connected  - process memory: 75.9 Mib  - trace_malloc: current=6.7 MiB, peak=6.7 MiB
Result iteration start  - process memory: 76.2 Mib  - trace_malloc: current=6.7 MiB, peak=6.8 MiB
Result iteration end  - process memory: 139.4 Mib  - trace_malloc: current=31.5 MiB, peak=31.6 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/psycopg/server_cursor.py:181: 13.7 MiB
    return self._tx.load_rows(0, res.ntuples, self._make_row)
#2: ./.venv/lib/python3.12/site-packages/sqlalchemy/engine/result.py:618: 6.1 MiB
    make_row(row) if make_row else row
#3: ./run_async_sqlalchemy_engine.py:31: 5.0 MiB
    storage[row.id] = row
#4: <frozen importlib._bootstrap_external>:752: 2.0 MiB
#5: <frozen abc>:106: 0.8 MiB
#6: ./.venv/lib/python3.12/site-packages/psycopg/types/array.py:348: 0.2 MiB
    return type(f"{name.title()}{base.__name__}", (base,), attribs)
#7: <frozen abc>:107: 0.1 MiB
#8: ./.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:302: 0.1 MiB
    env.update(vars(mod))
#9: ./.venv/lib/python3.12/site-packages/sqlalchemy/event/attr.py:213: 0.1 MiB
    self._clslevel[target] = collections.deque()
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/sql/schema.py:2159: 0.0 MiB
    self.info = info
4237 other: 3.0 MiB
Total allocated size: 31.1 MiB
```

### Synchronous SQLAlchemy Session - ORM

This approach uses the SQL Alchemy session and the model in asynchronous mode.
It uses the SQLAlchemy "ORM" approach (in contrast to the core approach).

```txt
 ✗ poetry run python run_async_sqlalchemy_session.py
Start  - process memory: 20.1 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 62.5 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Engine connected  - process memory: 71.8 Mib  - trace_malloc: current=6.4 MiB, peak=6.5 MiB
Result iteration start  - process memory: 323.6 Mib  - trace_malloc: current=115.5 MiB, peak=115.5 MiB
Result iteration end  - process memory: 316.8 Mib  - trace_malloc: current=106.9 MiB, peak=123.0 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:206: 20.6 MiB
    self.expired_attributes = set()
#2: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/instrumentation.py:509: 16.0 MiB
    state = self._state_constructor(instance, self)
#3: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:204: 13.7 MiB
    self.obj = weakref.ref(obj, self._cleanup)
#4: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/instrumentation.py:507: 9.2 MiB
    instance = self.class_.__new__(self.class_)
#5: ./.venv/lib/python3.12/site-packages/psycopg/server_cursor.py:181: 7.7 MiB
    return self._tx.load_rows(0, res.ntuples, self._make_row)
#6: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/state.py:205: 6.1 MiB
    self.committed_state = {}
#7: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/loading.py:1116: 6.1 MiB
    dict_ = instance_dict(instance)
#8: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/loading.py:1080: 6.1 MiB
    identitykey = (
#9: ./run_async_sqlalchemy_session.py:31: 5.0 MiB
    storage[row.id] = row
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/orm/loading.py:1082: 4.6 MiB
    primary_key_getter(row),
4291 other: 6.3 MiB
Total allocated size: 101.5 MiB
```

### Asynchronous SQLAlchemy Engine - Core - Pydantic

This approach uses the "low level" SQL Alchemy engine in asynchronous mode.

This approach also uses Pydantic models and creates them via the model class constructor.

```txt
$ poetry run python run_async_sqlalchemy_engine_pydantic.py
Start  - process memory: 20.2 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 60.7 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Engine connected  - process memory: 77.4 Mib  - trace_malloc: current=6.7 MiB, peak=6.7 MiB
Result iteration start  - process memory: 77.6 Mib  - trace_malloc: current=6.7 MiB, peak=6.8 MiB
Result iteration end  - process memory: 197.3 Mib  - trace_malloc: current=64.4 MiB, peak=64.4 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/pydantic/main.py:212: 38.2 MiB
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
#2: ./run_async_sqlalchemy_engine_pydantic.py:31: 11.9 MiB
    storage[row.id] = DomainModel(id=row.id, num=row.num, data=row.data)
#3: ./.venv/lib/python3.12/site-packages/psycopg/server_cursor.py:181: 7.6 MiB
    return self._tx.load_rows(0, res.ntuples, self._make_row)
#4: <frozen importlib._bootstrap_external>:752: 2.0 MiB
#5: <frozen abc>:106: 0.8 MiB
#6: ./.venv/lib/python3.12/site-packages/psycopg/types/array.py:348: 0.2 MiB
    return type(f"{name.title()}{base.__name__}", (base,), attribs)
#7: <frozen abc>:107: 0.1 MiB
#8: ./.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:302: 0.1 MiB
    env.update(vars(mod))
#9: ./.venv/lib/python3.12/site-packages/sqlalchemy/event/attr.py:213: 0.1 MiB
    self._clslevel[target] = collections.deque()
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/sql/schema.py:2159: 0.0 MiB
    self.info = info
4242 other: 3.0 MiB
Total allocated size: 64.0 MiB
```

### Asynchronous SQLAlchemy Engine - Core - Pydantic - Validation

This approach uses the "low level" SQL Alchemy engine in asynchronous mode.

This approach also uses Pydantic models and creates them with validation from existing objects.

```txt
$ poetry run python run_async_sqlalchemy_engine_pydantic_validate.py
Start  - process memory: 20.4 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 62.1 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Engine connected  - process memory: 76.9 Mib  - trace_malloc: current=6.7 MiB, peak=6.7 MiB
Result iteration start  - process memory: 77.2 Mib  - trace_malloc: current=6.7 MiB, peak=6.8 MiB
Result iteration end  - process memory: 194.5 Mib  - trace_malloc: current=64.4 MiB, peak=64.4 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/pydantic/main.py:596: 45.0 MiB
    return cls.__pydantic_validator__.validate_python(
#2: ./.venv/lib/python3.12/site-packages/psycopg/server_cursor.py:181: 7.6 MiB
    return self._tx.load_rows(0, res.ntuples, self._make_row)
#3: ./run_async_sqlalchemy_engine_pydantic_validate.py:31: 5.0 MiB
    storage[row.id] = DomainModel.model_validate(row)
#4: <frozen importlib._bootstrap_external>:752: 2.0 MiB
#5: <frozen abc>:106: 0.8 MiB
#6: ./.venv/lib/python3.12/site-packages/psycopg/types/array.py:348: 0.2 MiB
    return type(f"{name.title()}{base.__name__}", (base,), attribs)
#7: <frozen abc>:107: 0.1 MiB
#8: ./.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:302: 0.1 MiB
    env.update(vars(mod))
#9: ./.venv/lib/python3.12/site-packages/sqlalchemy/event/attr.py:213: 0.1 MiB
    self._clslevel[target] = collections.deque()
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/util/_concurrency_py3k.py:80: 0.1 MiB
    greenlet.__init__(self, fn, driver)
4246 other: 3.1 MiB
Total allocated size: 64.0 MiB
```

### Asynchronous SQLAlchemy Engine - Core - Pydantic - Without Validation

This approach uses the "low level" SQL Alchemy engine in asynchronous mode.

This approach also uses Pydantic models and creates them without validation from existing objects.

```txt
$ poetry run python run_async_sqlalchemy_engine_pydantic_no_validation.py
Start  - process memory: 19.6 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 59.9 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Engine connected  - process memory: 75.5 Mib  - trace_malloc: current=6.7 MiB, peak=6.7 MiB
Result iteration start  - process memory: 75.7 Mib  - trace_malloc: current=6.7 MiB, peak=6.8 MiB
Result iteration end  - process memory: 171.6 Mib  - trace_malloc: current=44.5 MiB, peak=44.5 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/psycopg/server_cursor.py:181: 13.7 MiB
    return self._tx.load_rows(0, res.ntuples, self._make_row)
#2: ./.venv/lib/python3.12/site-packages/pydantic/main.py:266: 6.9 MiB
    m = cls.__new__(cls)
#3: ./.venv/lib/python3.12/site-packages/sqlalchemy/engine/result.py:618: 6.1 MiB
    make_row(row) if make_row else row
#4: ./.venv/lib/python3.12/site-packages/pydantic/main.py:267: 6.1 MiB
    fields_values: dict[str, Any] = {}
#5: ./run_async_sqlalchemy_engine_pydantic_construct.py:31: 5.0 MiB
    storage[row.id] = DomainModel.model_construct(row)
#6: <frozen importlib._bootstrap_external>:752: 2.0 MiB
#7: <frozen abc>:106: 0.8 MiB
#8: ./.venv/lib/python3.12/site-packages/psycopg/types/array.py:348: 0.2 MiB
    return type(f"{name.title()}{base.__name__}", (base,), attribs)
#9: <frozen abc>:107: 0.1 MiB
#10: ./.venv/lib/python3.12/site-packages/sqlalchemy/util/langhelpers.py:302: 0.1 MiB
    env.update(vars(mod))
4241 other: 3.1 MiB
Total allocated size: 44.1 MiB
```

### Synchronous Psycopg - Pydantic - Without Validation

This approach uses the driver directly (that is indirectly used by SQL Alchemy).

This approach also uses Pydantic models and creates them without validation from existing objects.

```txt
$ poetry run python run_sync_psycopg_pydantic_no_validation.py
Start  - process memory: 60.3 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
After imports  - process memory: 64.8 Mib  - trace_malloc: current=0.0 MiB, peak=0.0 MiB
Result iteration start  - process memory: 75.4 Mib  - trace_malloc: current=0.1 MiB, peak=0.2 MiB
Result iteration end  - process memory: 153.7 Mib  - trace_malloc: current=32.6 MiB, peak=32.6 MiB

Top 10 lines for memory allocation
#1: ./.venv/lib/python3.12/site-packages/psycopg/cursor.py:234: 7.6 MiB
    return self._tx.load_row(pos, self._make_row)
#2: ./.venv/lib/python3.12/site-packages/pydantic/main.py:266: 6.9 MiB
    m = cls.__new__(cls)
#3: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/collections/__init__.py:449: 6.9 MiB
    result = tuple_new(cls, iterable)
#4: ./.venv/lib/python3.12/site-packages/pydantic/main.py:267: 6.1 MiB
    fields_values: dict[str, Any] = {}
#5: ./run_sync_psycopg_pydantic_no_validation.py:20: 5.0 MiB
    storage[row.id] = DomainModel.model_construct(row)
#6: <frozen importlib._bootstrap_external>:752: 0.0 MiB
#7: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/stringprep.py:24: 0.0 MiB
    b3_exceptions = {
#8: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/stringprep.py:262: 0.0 MiB
    c9_set = set([917505] + list(range(917536,917632)))
#9: ./.venv/lib/python3.12/site-packages/psycopg/_conninfo_utils.py:107: 0.0 MiB
    cd = ParamDef(
#10: /Users/sergej_herbert/.asdf/installs/python/3.12.1/lib/python3.12/encodings/idna.py:300: 0.0 MiB
    class StreamWriter(Codec,codecs.StreamWriter):
125 other: 0.0 MiB
Total allocated size: 32.6 MiB
```
