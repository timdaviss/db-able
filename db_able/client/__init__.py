"""
:date_created: 2021-10-23
"""

from builtins import object

from do_py.utils import cached_property
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

CONN_STR = 'mysql+pymysql://root:GAgh4B5ZF7hXgcbj@localhost?unix_socket=/tmp/mysql.sock'


class DBClient(object):
    """
    SQLAlchemy to MySQL via pymysql client implementation with context utility.
    Implementation is scoped to using stored procedures and provided arguments.
    """
    engine = create_engine(CONN_STR)
    data = None

    def __init__(self, database, stored_procedure, *args, **kwargs):
        """
        :type database: str
        :type stored_procedure: str
        :param args: Stored procedure's argument values.
        :param kwargs: Additional keyword arguments to adjust DB execution logic.
        :keyword rollback: bool; Rolls back changes on exception.
        """
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
        Note that calling this property opens a connection with DB.
        :rtype: sqlalchemy.engine.base.Connection
        """
        return self.engine.connect()

    @cached_property
    def session(self):
        """
        Connection-scoped Session.
        :rtype: sqlalchemy.orm.Session
        """
        return sessionmaker(bind=self.conn)()

    def __enter__(self):
        """
        Execute the constructed `self.sql` command in DB based on `__init__` params.
        :rtype: DBClient
        """
        output = self.session.execute(self.sql % self.args)
        self.data = [
            {
                key: value
                for key, value in zip(output.keys(), row)
                }
            for row in output.all()
            ]
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        :type exc_type: Exception or None
        :type exc_val:
        :type exc_tb:
        :rtype:
        """
        if exc_type is None or not self.kwargs.get('rollback', False):
            self.session.commit()
        self.session.__exit__(exc_type, exc_val, exc_tb)
        self.conn.__exit__(exc_type, exc_val, exc_tb)
