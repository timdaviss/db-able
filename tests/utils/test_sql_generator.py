"""
:date_created: 2021-11-21
"""
import pytest
from do_py import R

from db_able import Loadable, Creatable, Savable, Deletable
from db_able.utils.sql_generator import ABCSQL, LoadProcedure, CreateProcedure, SaveProcedure, DeleteProcedure, \
    CoreStoredProcedure, procedure_mapping, print_all_sps
from examples.a import A


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


class TestLoadProcedure(object):
    class_ref = LoadProcedure

    @pytest.fixture(params=['A'])
    def cls_ref(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: type
        """
        return type(request.param, (Loadable,), {
            '__module__': 'pytesting',
            'db': 'testing',
            '_restrictions': {
                'x': R.INT,
                'y': R.INT
                },
            'load_params': ['x', 'y']
            })

    @pytest.fixture
    def expected_output(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: LoadProcedure
        """
        data = {
            'db': 'testing',
            'where_clause': '`x` = `_x` AND `y` = `_y`'
            }
        data.update(request.param)
        return self.class_ref(data)

    @pytest.mark.parametrize('cls_ref, expected_output', [
        ('A', {'table_name': 'a'}),
        ('User', {'table_name': 'user'}),
        ('CouchPotato', {'table_name': 'couch_potato'})
        ], indirect=True)
    def test_from_db_able(self, cls_ref, expected_output):
        """
        :type cls_ref: type[Loadable]
        :type expected_output: LoadProcedure
        """
        assert self.class_ref.from_db_able(cls_ref) == expected_output


class TestCreateProcedure(object):
    class_ref = CreateProcedure

    @pytest.fixture(params=['A'])
    def cls_ref(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: type
        """
        return type(request.param, (Loadable, Creatable), {
            '__module__': 'pytesting',
            'db': 'testing',
            '_restrictions': {
                'x': R.INT,
                'y': R.INT
                },
            'load_params': ['x', 'y'],
            'create_params': ['x', 'y']
            })

    @pytest.fixture
    def expected_output(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: CreateProcedure
        """
        data = {
            'db': 'testing',
            'columns': '`x`, `y`',
            'values_clause': '`_x`, `_y`',
            'load_version': ''
            }
        data.update(request.param)
        return self.class_ref(data)

    @pytest.mark.parametrize('cls_ref, expected_output', [
        ('A', {'table_name': 'a', 'cls_name': 'A'}),
        ('User', {'table_name': 'user', 'cls_name': 'User'}),
        ('CouchPotato', {'table_name': 'couch_potato', 'cls_name': 'CouchPotato'})
        ], indirect=True)
    def test_from_db_able(self, cls_ref, expected_output):
        """
        :type cls_ref: type[Creatable]
        :type expected_output: CreateProcedure
        """
        assert self.class_ref.from_db_able(cls_ref) == expected_output


class TestSaveProcedure(object):
    class_ref = SaveProcedure

    @pytest.fixture(params=['A'])
    def cls_ref(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: type
        """
        return type(request.param, (Loadable, Savable), {
            '__module__': 'pytesting',
            'db': 'testing',
            '_restrictions': {
                'x': R.INT,
                'y': R.INT,
                'z': R.INT
                },
            'load_params': ['x', 'y'],
            'save_params': ['x', 'y', 'z']
            })

    @pytest.fixture
    def expected_output(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: SaveProcedure
        """
        data = {
            'db': 'testing',
            'set_clause': '`z`=`_z`',
            'where_clause': '`x` = `_x` AND `y` = `_y`',
            'load_version': '',
            'load_params': '`_x`, `_y`'
            }
        data.update(request.param)
        return self.class_ref(data)

    @pytest.mark.parametrize('cls_ref, expected_output', [
        ('A', {'table_name': 'a', 'cls_name': 'A'}),
        ('User', {'table_name': 'user', 'cls_name': 'User'}),
        ('CouchPotato', {'table_name': 'couch_potato', 'cls_name': 'CouchPotato'})
        ], indirect=True)
    def test_from_db_able(self, cls_ref, expected_output):
        """
        :type cls_ref: type[Savable]
        :type expected_output: SaveProcedure
        """
        assert self.class_ref.from_db_able(cls_ref) == expected_output


class TestDeleteProcedure(object):
    class_ref = DeleteProcedure

    @pytest.fixture(params=['A'])
    def cls_ref(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: type
        """
        return type(request.param, (Deletable,), {
            '__module__': 'pytesting',
            'db': 'testing',
            '_restrictions': {
                'x': R.INT,
                'y': R.INT,
                'z': R.INT
                },
            'delete_params': ['x', 'y']
            })

    @pytest.fixture
    def expected_output(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: DeleteProcedure
        """
        data = {
            'db': 'testing',
            'where_clause': '`x` = `_x` AND `y` = `_y`'
            }
        data.update(request.param)
        return self.class_ref(data)

    @pytest.mark.parametrize('cls_ref, expected_output', [
        ('A', {'table_name': 'a'}),
        ('User', {'table_name': 'user'}),
        ('CouchPotato', {'table_name': 'couch_potato'})
        ], indirect=True)
    def test_from_db_able(self, cls_ref, expected_output):
        """
        :type cls_ref: type[Deletable]
        :type expected_output: DeleteProcedure
        """
        assert self.class_ref.from_db_able(cls_ref) == expected_output


class TestCoreStoredProcedure(object):
    class_ref = CoreStoredProcedure

    @pytest.fixture(params=['A'])
    def cls_ref(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: type
        """
        return type(request.param, (Creatable, Loadable, Savable, Deletable,), {
            '__module__': 'pytesting',
            'db': 'testing',
            '_restrictions': {
                'x': R.INT,
                'y': R.INT,
                'z': R.INT
                },
            'load_params': ['x', 'y'],
            'create_params': ['x', 'y', 'z'],
            'save_params': ['x', 'y', 'z'],
            'delete_params': ['x', 'y']
            })

    @pytest.fixture
    def expected_output(self, request, cls_ref, method, params):
        """
        :type request: pytest.SubRequest
        :type cls_ref: type[Loadable, Creatable, Savable, Deletable]
        :rtype: CoreStoredProcedure
        """
        data = {
            'db': 'testing',
            'method': method,
            'version': '',
            'params': params
            }
        data.update(request.param)
        data['procedure'] = procedure_mapping[data['method']].from_db_able(cls_ref).as_sql()
        return self.class_ref(data)

    @pytest.fixture(params=['create', 'load', 'save', 'delete'])
    def method(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: str
        """
        return request.param

    @pytest.fixture
    def params(self, cls_ref, method):
        """
        :type cls_ref: type
        :type method: str
        :rtype: str
        """
        params_attr = getattr(cls_ref, '%s_params' % method)
        return ',\n'.join('    IN `_%s` INT' % param for param in params_attr)

    @pytest.mark.parametrize('cls_ref, expected_output', [
        ('A', {'cls_name': 'A'}),
        ('User', {'cls_name': 'User'}),
        ('CouchPotato', {'cls_name': 'CouchPotato'})
        ], indirect=True)
    def test_from_db_able(self, cls_ref, method, expected_output):
        """
        :type cls_ref: type[Deletable]
        :type method: str
        :type expected_output: DeleteProcedure
        """
        assert self.class_ref.from_db_able(cls_ref, method) == expected_output


def test_print_all_sps():
    print_all_sps(A)
