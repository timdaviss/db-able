"""
Paginated example.
:date_created: 2021-11-30
"""
from do_py import R

from db_able import Paginated


class C(Paginated):
    """ Simple Paginated example. """
    db = 'testing'
    _restrictions = {
        'id': R.INT,
        'x': R.INT,
        'y': R.INT
        }
    _extra_restrictions = {
        'limit': R.INT.with_default(10),
        'page': R.INT.with_default(1)
        }
    list_params = ['limit', 'page']
