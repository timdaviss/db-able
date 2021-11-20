"""
:date_created: 2021-10-23
"""

import json

from do_py.utils import cached_property
from do_py.utils.properties import cached_classproperty
from pymysql.constants import FIELD_TYPE
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List

CONN_STR = None


class Data(object):
    """
    Managed attribute for DBClient to load JSON data for sqlalchemy.
    """

    def __get__(self, instance, owner):
        """
        :type instance: DBClient
        :type owner: type
        :rtype: list of tuple
        """
        # noinspection PyUnresolvedReferences
        return instance.__data

    def __set__(self, instance, data: List[dict]):
        """
        Validate that `value` is a list of 2-tuples and is dict-transformation friendly.
        `json.dumps` dict and list vals in tuple[1] of each element
        Caveat: Relies on `instance.data_types` to be populated beforehand.
        :type instance: DBClient
        :type data: list of dict
        """
        new_data = []
        for datum in data:
            new_datum = {}
            for key, value in datum.items():
                if instance.data_types[key] == FIELD_TYPE.JSON and value is not None:
                    new_datum[key] = json.loads(value)
                else:
                    new_datum[key] = value
            new_data.append(new_datum)
        instance.__data = new_data


class Args(object):
    """
    Managed attribute for DBClient to dump JSON data for sqlalchemy.
    """

    def __get__(self, instance, owner):
        """
        :type instance: DBClient
        :type owner: type
        :rtype: list of tuple
        """
        # noinspection PyUnresolvedReferences
        return instance.__args

    def __set__(self, instance, args: List[tuple]):
        """
        Validate that `value` is a list of 2-tuples and is dict-transformation friendly.
        `json.dumps` dict and list vals in tuple[1] of each element
        :type instance: DBClient
        :type args: list of tuple
        """
        dict(args)  # Attempting this throws a ValueError for malformed `value`.
        new_args = []
        for key, value in args:
            if isinstance(value, dict) or isinstance(value, list):
                new_args.append((key, json.dumps(value)))
            else:
                new_args.append((key, value))
        instance.__args = new_args


class DBClient(object):
    """
    SQLAlchemy to MySQL via pymysql client implementation with context utility.
    Implementation is scoped to using stored procedures and provided arguments.
    """
    data_types = None
    data = Data()
    args = Args()

    def __init__(self, database, stored_procedure, *args, **kwargs):
        """
        :type database: str
        :type stored_procedure: str
        :param args: *list of tuple; Stored procedure's keyword argument values.
        :param kwargs: Additional keyword arguments to adjust DB execution logic.
        :keyword rollback: bool; Rolls back changes on exception.
        """
        assert CONN_STR is not None, 'Initialize db_able by setting `db_able.client.CONN_STR`.'
        self.database = database
        self.stored_procedure = stored_procedure
        self.args = args
        self.kwargs = kwargs

    @cached_classproperty
    def engine(cls):
        """
        :rtype: sqlalchemy.engine.base.Engine or sqlalchemy.future.Engine
        """
        return create_engine(CONN_STR)

    @property
    def sql(self):
        """
        :rtype: sqlalchemy.sql.elements.TextClause
        """
        return text(
            'CALL `{database}`.`{stored_procedure}`({args});'.format(
                database=self.database,
                stored_procedure=self.stored_procedure,
                args=','.join(':%s' % arg[0] for arg in self.args)
                )
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
        output = self.session.execute(self.sql.bindparams(**dict(self.args)))
        # {column_name: pymysql column type}
        self.data_types = {descriptor[0]: descriptor[1] for descriptor in output.cursor.description}
        self.data = [dict(row) for row in output.all()]
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
