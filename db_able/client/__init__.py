"""
:date_created: 2021-10-23
"""

from builtins import object

from do_py.utils import cached_property
from sqlalchemy import create_engine

CONN_STR = 'mysql+pymysql://root:GAgh4B5ZF7hXgcbj@localhost?unix_socket=/tmp/mysql.sock'


# TODO: kwargs['rollback'] <bool> on DB exception.
class DBClient(object):
    """
    SQLAlchemy to MySQL via pymysql client implementation with context utility.
    Implementation is scoped to using stored procedures and provided arguments.
    """
    engine = create_engine(CONN_STR)
    data = None

    def __init__(self, database, stored_procedure, *args, **kwargs):
        """"""
        self.database = database
        self.stored_procedure = stored_procedure
        self.args = args
        self.kwargs = kwargs

    @property
    def sql(self):
        """
        :rtype: str
        """
        return 'CALL `{database}`.`{stored_procedure}`({args});'.format(
            database=self.database,
            stored_procedure=self.stored_procedure,
            args=','.join('%s' for _ in self.args)
            )

    @cached_property
    def conn(self):
        """
        :rtype: sqlalchemy.engine.base.Connection
        """
        return self.engine.connect()

    def __enter__(self):
        """
        Execute the constructed `self.sql` command in DB based on `__init__` params.
        :rtype: DBClient
        """
        with self.conn as conn:
            output = conn.execute(self.sql, self.args)
            self.data = [
                {
                    key: value
                    for key, value in zip(output.keys(), row)
                    }
                for row in output.all()
                ]
            return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """"""
        if not self.conn.closed:
            self.conn.close()
