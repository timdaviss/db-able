"""
:date_created: 2021-10-23
"""

import json
import os

from do_py.utils import cached_property
from do_py.utils.properties import cached_classproperty
from pymysql.constants import FIELD_TYPE
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from typing import List

CONN_STR = os.getenv('DB_CONN_STR')


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

    @cached_property
    def output(self):
        """
        Note that calling this property executes the SQL and prepares for a single pass-through of resulting data.
        :rtype: sqlalchemy.engine.cursor.CursorResult
        """
        return self.session.execute(self.sql.bindparams(**dict(self.args)))

    def populate_data(self):
        """
        Use the current `self.output.cursor` position to populate `self.data` and `self.data_types`.
        """
        # {column_name: pymysql column type}
        self.data_types = {descriptor[0]: descriptor[1] for descriptor in self.output.cursor.description}
        data = []
        for row in self.output.cursor.fetchall():
            row_dict = {}
            for description, value in zip(self.output.cursor.description, row):
                row_dict[description[0]] = value
            data.append(row_dict)
        self.data = data

    def next_set(self):
        """
        Move cursor to next result set and populate `self.data` with data from next result set.
        :rtype: bool
        """
        next_set_bool = self.output.cursor.nextset() and self.output.cursor.description
        self.populate_data()
        return next_set_bool

    def __enter__(self):
        """
        Execute the constructed `self.sql` command in DB based on `__init__` params.
        :rtype: DBClient
        """
        self.populate_data()
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
