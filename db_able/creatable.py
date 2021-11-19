"""
:date_created: 2021-11-04
"""
from do_py.abc import ABCRestrictions

from db_able.base_model.database_abc import Database
from db_able.client import DBClient


@ABCRestrictions.require('create_params')
class Creatable(Database):
    """
    This is a mixin designed to access DB with a standard classmethod action, `create`.
    Supplants the "C" of CRUD.
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        Extend compilation checks to validate defined params.
        """
        super(Creatable, cls).__compile__()
        cls._validate_params('create_params')

    @classmethod
    def create(cls, **kwargs):
        """
        Create `DataObject`. Use `cls.create_params` as kwargs reference.
        Expects to call the stored procedure: '%s_create' % cls.__name__, i.e. 'MyDataObject_create'
        Note: Standard Creatable implementation uses Loadable internally in the stored procedure.

        Example:
            >>> from db_able import Loadable, Creatable, Params
            >>> from do_py import R
            >>>
            >>> class A(Creatable, Loadable):
            >>>     db = 'schema_name'
            >>>     _restrictions = {
            >>>         'id': R.INT,
            >>>         'x': R.INT.with_default(0),
            >>>         'y': R.INT.with_default(1)
            >>>         }
            >>>     load_params = Params('id')  # version=2 allows versioning of the SP, i.e. `A_load_v2`
            >>>     create_params = Params('x', 'y')
            >>>
            >>> a = A.create(x=1, y=2)
            >>> loaded = A.load(id=a.id)
            >>> assert a == loaded

        :param kwargs: Refer to cls.create_params
        :rtype: cls or None
        """
        stored_procedure = '%s_create%s' % (cls.__name__, cls.create_params.version)
        validated_args = cls.kwargs_validator(*cls.create_params, **kwargs)
        with DBClient(cls.db, stored_procedure, *validated_args, rollback=True) as conn:
            for row in conn.data:  # Note: this is a weakness. Create should always return one and only one row.
                return cls(data=row)
