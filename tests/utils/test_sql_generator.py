"""
:date_created: 2021-11-21
"""
import pytest
from do_py import R

from db_able.utils.sql_generator import ABCSQL


class DummyABCSQL(ABCSQL):
    """ Dummy implementation of ABCSQL. """
    BASE_SQL = '''SELECT * FROM `testing`.`{table_name}` WHERE {where_clause};'''
    _restrictions = {
        'table_name': R.STR,
        'where_clause': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref):
        """
        :type cls_ref: type
        :rtype: DummyABCSQL
        """
        return cls({
            'table_name': cls.get_table_name(cls_ref),
            'where_clause': '`hello`=`_world`'
            })


class TestABCSQL(object):
    class_ref = ABCSQL

    @pytest.fixture(params=['A'])
    def cls_ref(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: type
        """
        return type(request.param, (ABCSQL,), {
            '__module__': 'pytesting',
            '_restrictions': {
                'key1': R.INT,
                'key2': R.STR,
                'key3': R()
                },
            'BASE_SQL': '''SELECT * FROM `testing`.`a`;''',
            'from_db_able': lambda x: x
            })

    @pytest.mark.parametrize('cls_ref, expected_output', [
        ('A', 'a'),
        ('User', 'user'),
        ('CouchPotato', 'couch_potato')
        ], indirect=['cls_ref'])
    def test_get_table_name(self, cls_ref, expected_output):
        """
        :type cls_ref: type
        :type expected_output: str
        """
        assert self.class_ref.get_table_name(cls_ref) == expected_output

    def test_as_sql(self):
        """
        Basic coverage of `as_sql` method.
        """
        inst = DummyABCSQL({
            'table_name': 'couch_potato',
            'where_clause': '`hello`=`_world`'
            })
        assert inst.as_sql() == '''SELECT * FROM `testing`.`couch_potato` WHERE `hello`=`_world`;'''
