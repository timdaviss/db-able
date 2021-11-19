"""
Placeholder unit test.
:date_created: 2020-12-05
"""
from datetime import datetime

from do_py import R, DataObject

from db_able import Creatable, Loadable


class Json(DataObject):
    """ Nested Json object for A. """
    _restrictions = {
        'x': R.INT,
        'y': R.INT
        }


class A(Creatable, Loadable):
    """ Basic DBAble implementation for unit tests. """
    db = 'testing'
    _restrictions = {
        'id': R.INT,
        'string': R.NULL_STR,
        'json': R(Json, type(None)),
        'int': R.NULL_INT,
        'float': R.NULL_FLOAT,
        'datetime': R.NULL_DATETIME
        }
    load_params = ['id']
    create_params = ['string', 'json', 'int', 'float', 'datetime']


def test_a():
    """

    """
    created = A.create(
        string='Hello world. 😇',
        json={'x': 1, 'y': 123},
        int=12,
        float=12.34,
        datetime=datetime.utcnow()
        )
    loaded = A.load(id=created.id)
    assert loaded == created
    # TODO: U
    # TODO: D
