"""
Scrollable example.
:date_created: 2021-11-30
"""
from do_py import R

from db_able import Scrollable


class B(Scrollable):
    """ Simple Scrollable implementation. """
    db = 'testing'
    _restrictions = {
        'id': R.INT,
        'x': R.INT,
        'y': R.INT
        }
    _extra_restrictions = {
        'limit': R.INT.with_default(10),
        'after': R.NULL_INT
        }
    list_params = ['limit', 'after']

    def to_after(self) -> int:
        """
        Convert `self` to cursor value.
        :rtype: int
        """
        return self.id
