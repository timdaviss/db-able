"""
:date_created: 2021-11-20
"""
import pytest

from db_able import Params


class TestParams(object):
    """
    Test Params list implementation for versioning metadata.
    """
    class_ref = Params

    @pytest.mark.parametrize('args, kwargs', [
        (['x', 'y'], {}),
        (['x', 'y'], {'version': 23})
        ])
    def test_init(self, args, kwargs):
        """
        :type args: list
        :type kwargs: dict
        """
        inst = self.class_ref(*args, **kwargs)
        assert inst == args

    @pytest.mark.parametrize('version, expected_output', [
        (None, ''),
        (2, '_v2'),
        (123, '_v123'),
        ])
    def test_version_property(self, version, expected_output):
        """
        :type version: int or None
        :type expected_output: str
        """
        inst = self.class_ref(version=version)
        assert expected_output == inst.version
