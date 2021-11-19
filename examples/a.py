from do_py import DataObject, R

from db_able import Creatable, Loadable, Savable, Deletable


class Json(DataObject):
    """ Nested Json object for A. """
    _restrictions = {
        'x': R.INT,
        'y': R.INT
        }


class A(Creatable, Loadable, Savable, Deletable):
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
    save_params = ['id', 'string', 'json', 'int', 'float', 'datetime']
    delete_params = ['id']
