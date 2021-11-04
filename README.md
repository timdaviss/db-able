# db-able
![release](https://img.shields.io/github/package-json/v/timdaviss/db-able?label=release&logo=release&style=flat-square)
![build](https://img.shields.io/github/workflow/status/timdaviss/db-able/test?style=flat-square)
![coverage](https://img.shields.io/codecov/c/github/timdaviss/db-able?style=flat-square)
![dependencies](https://img.shields.io/librariesio/release/pypi/db-able?style=flat-square)

Boiler plate for building new repos within do-py-together infrastructure.

## Usage
```python
from db_able import client


client.CONN_STR = 'mysql+pymysql://root:GAgh4B5ZF7hXgcbj@localhost?unix_socket=/tmp/mysql.sock'
```

### Testing & Code Quality
Code coverage reports for master, branches, and PRs 
are posted [here in CodeCov](https://codecov.io/gh/timdaviss/db-able).
