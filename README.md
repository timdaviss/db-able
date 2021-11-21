# db-able
![release](https://img.shields.io/github/package-json/v/timdaviss/db-able?label=release&logo=release&style=flat-square)
![build](https://img.shields.io/github/workflow/status/timdaviss/db-able/test?style=flat-square)
![coverage](https://img.shields.io/codecov/c/github/timdaviss/db-able?style=flat-square)
![dependencies](https://img.shields.io/librariesio/release/pypi/db-able?style=flat-square)

Framework to implement basic CRUD operations with DB for [DataObject](https://github.com/do-py-together/do-py).

## Quick start
Set up your connection string to your database.
```python
from db_able import client


client.CONN_STR = '{dialect}+{driver}://{username}:{password}@{host}:{port}/{database}?{query_args}'
```

Implement the mixins into your DataObject to inject CRUD methods.
```python
from do_py import R
from db_able import Creatable, Deletable, Loadable, Savable


class MyObject(Creatable, Deletable, Loadable, Savable):
    db = '{schema_name}'
    _restrictions = {
        'id': R.INT,
        'key': R.INT
        }
    load_params = ['id']
    create_params = ['key']
    delete_params = ['id']
    save_params = ['id', 'key']


my_obj = MyObject.create(key=555)
my_obj = MyObject.load(id=my_obj.id)
my_obj.key = 777
my_obj.save()
my_obj.delete()
```
Classmethods `create`, `load`, and methods `save` and `delete` are made available
to your DataObject class.

Use provided SQL Generating utils to expedite implementation.
```python
from db_able.utils.sql_generator import print_all_sps
from examples.a import A

print_all_sps(A)
```

### Testing & Code Quality
Code coverage reports for master, branches, and PRs 
are posted [here in CodeCov](https://codecov.io/gh/timdaviss/db-able).
