"""
:date_created: 2021-11-20
"""
import pytest
from do_py import R
from do_py.exceptions import DataObjectError

from db_able.base_model.kwargs_validator import KwargsValidator


class DummyKwargsValidator(KwargsValidator):
    """ Dummy implementation for UT """
    _restrictions = {
        'x': R.INT,
        }
    _extra_restrictions = {
        'y': R.INT.with_default(5)
        }


class TestKwargsValidator(object):
    """
    Test the KwargsValidator interface.
    """
    class_ref = DummyKwargsValidator

    @pytest.fixture
    def namespace(self, request):
        """
        :type request: pytest.SubRequest
        :rtype: dict
        """
        data = {
            '__module__': 'pytesting',
            '_restrictions': {'x': R.INT},
            }
        data.update(request.param)
        return data

    @pytest.mark.parametrize('namespace', [
        {},
        {'_extra_restrictions': {'y': R.INT}},
        pytest.param(
            {'_extra_restrictions': {'y': [str, 'a', 'b']}},
            marks=pytest.mark.xfail(raises=DataObjectError)
            ),
        ], indirect=True)
    def test_compile(self, namespace):
        """
        :type namespace: dict
        """
        _ = type('Implementation', (KwargsValidator,), namespace)

    @pytest.mark.parametrize('signature, kwargs, expected_output', [
        (['x'], {'x': 1}, [('x', 1)]),
        (['y'], {}, [('y', 5)]),
        pytest.param(['x'], {'x': 'abc'}, [], marks=pytest.mark.xfail(raises=DataObjectError)),
        pytest.param(['z'], {'x': 1, 'y': 1}, [], marks=pytest.mark.xfail(raises=KeyError)),
        ])
    def test_kwargs_validator(self, signature, kwargs, expected_output):
        """
        :type signature: list
        :type kwargs: dict
        :type expected_output: list of tuple
        """
        assert expected_output == self.class_ref.kwargs_validator(*signature, **kwargs)
