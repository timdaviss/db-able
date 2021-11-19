"""
:date_created: 2021-11-03
"""
from do_py.abc import ABCRestrictions

from db_able.base_model.database_abc import Database
from db_able.client import DBClient


@ABCRestrictions.require('load_params')
class Loadable(Database):
    """
    This is a mixin designed to access DB with a standard classmethod action, `load`.
    Supplants the "R" of CRUD.
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        Extend compilation checks to validate defined params.
        """
        super(Loadable, cls).__compile__()
        cls._validate_params('load_params')

    @classmethod
    def load(cls, **kwargs):
        """
        Load `DataObject`. use `cls.load_params` as kwargs reference.
        Expects to call the stored procedure: '%s_load' % cls.__name__, i.e. 'MyDataObject_load'

        Example:
            >>> from db_able import Loadable, Params
            >>> from do_py import R
            >>>
            >>> class A(Loadable):
            >>>     db = 'schema_name'
            >>>     _restrictions = {
            >>>         'id': R.INT,
            >>>         'x': R.INT.with_default(0),
            >>>         'y': R.INT.with_default(1)
            >>>         }
            >>>     load_params = Params('id')  # version=2 allows versioning of the SP, i.e. `A_load_v2`
            >>>
            >>> a = A.load(id=2)

        :param kwargs:
        :rtype: cls or None
        """
        stored_procedure = '%s_load%s' % (cls.__name__, cls.load_params.version)
        validated_args = cls.kwargs_validator(*cls.load_params, **kwargs)
        with DBClient(cls.db, stored_procedure, *validated_args) as conn:
            for row in conn.data:  # Note: this is a weakness. Load should only return one row.
                return cls(data=row)
