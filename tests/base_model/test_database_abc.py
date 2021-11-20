"""
:date_created: 2021-11-20
"""
import pytest
from do_py import R

from db_able import Params
from db_able.base_model.database_abc import Database


class DummyDatabase(Database):
    """ Dummy Database implementation """
    db = ''
    _restrictions = {
        'x': R.INT
        }
    dummy_params = ['x']
    invalid_params = 'abc'


class MyTestException(Exception):
    """ Custom exception for pytest. """


class TestDatabase(object):
    """
    Test Database abstract base class implementation.
    """
    class_ref = DummyDatabase

    @pytest.mark.parametrize('params_attr_name', [
        'dummy_params',
        pytest.param('invalid_params', marks=pytest.mark.xfail(raises=AssertionError)),
        pytest.param('invalid', marks=pytest.mark.xfail(raises=AttributeError))
        ])
    def test_validate_params(self, params_attr_name):
        """
        :type params_attr_name: str
        """
        self.class_ref._validate_params(params_attr_name)
        try:
            assert isinstance(getattr(self.class_ref, params_attr_name), Params)
        except AssertionError:
            raise MyTestException('pytest exception')
