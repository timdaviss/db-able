"""
:date_created: 2021-11-20
"""
import pytest
from pymysql.constants import FIELD_TYPE
from sqlalchemy import text

from db_able import client
from db_able.client import Data, Args, DBClient


class DummyObject(object):
    """ Dummy class definition for use with attribute descriptors. """
    data_types = {}
    data = Data()
    args = Args()


class TestData(object):
    """
    Test the custom attribute descriptor Data.
    """
    class_ref = Data

    @pytest.mark.parametrize('data, data_types, expected_output', [
        ([], {}, []),
        ([{'x': 1}], {'x': FIELD_TYPE.INT24}, [{'x': 1}]),
        ([{'y': None}], {'y': FIELD_TYPE.JSON}, [{'y': None}]),
        ([{'y': '{"x": 1}'}], {'y': FIELD_TYPE.JSON}, [{'y': {'x': 1}}]),
        pytest.param(['abc'], {}, [], marks=pytest.mark.xfail(raises=AttributeError)),
        ])
    def test_get_set(self, data, data_types, expected_output):
        """
        :type data: List[dict]
        :type data_types: dict
        :type expected_output: List[dict]
        """
        obj = DummyObject()
        obj.data_types = data_types
        obj.data = data
        assert obj.data == expected_output


class TestArgs(object):
    """
    Test the custom attribute descriptor Args.
    """
    class_ref = Args

    @pytest.mark.parametrize('args, expected_output', [
        ([('x', 1)], [('x', 1)]),
        ([('y', None)], [('y', None)]),
        ([('y', {'x': 1})], [('y', '{"x": 1}')]),
        ([('y', ['a', 'b'])], [('y', '["a", "b"]')]),
        ])
    def test_get_set(self, args, expected_output):
        """
        :type args: list of tuple
        :type expected_output: list of tuple
        """
        obj = DummyObject()
        obj.args = args
        assert obj.args == expected_output


# TODO: conn, session, __enter__, __exit__; kwarg `rollback` functionality
class TestDBClient(object):
    """
    Test the DB connection client context manager class, DBClient.
    """
    class_ref = DBClient

    @pytest.fixture
    def conn_str(self, request):
        """
        :type request: pytest.SubRequest
        """
        old_conn_str = client.CONN_STR
        client.CONN_STR = request.param
        yield
        client.CONN_STR = old_conn_str

    @pytest.mark.parametrize('conn_str', [
        'dummy_conn_str',
        pytest.param(None, marks=pytest.mark.xfail(raises=AssertionError, reason='CONN_STR must be set to connect.'))
        ], indirect=True)
    def test_init(self, conn_str):
        """
        :type conn_str: None
        """
        self.class_ref('db', 'sp', *[], **{})

    def test_engine_cached_classproperty(self):
        """
        Validate that `DBClient.engine` is only set once per worker.
        """
        inst1 = self.class_ref('db', 'sp', *[], **{})
        inst2 = self.class_ref('db', 'sp', *[], **{})
        assert inst1.engine == inst2.engine == self.class_ref.engine

    @pytest.mark.parametrize('args, expected_output', [
        ([], 'CALL `db`.`sp`();'),
        ([('x', 1)], 'CALL `db`.`sp`(:x);'),
        ([('x', 1), ('y', 2)], 'CALL `db`.`sp`(:x,:y);'),
        ])
    def test_sql_property(self, args, expected_output):
        """
        :type args: list of tuple
        :type expected_output: str
        """
        inst = self.class_ref('db', 'sp', *args)
        assert inst.sql.text == expected_output
