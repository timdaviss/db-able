"""
:date_created: 2021-11-18
"""

from do_py.abc import ABCRestrictions

from db_able.base_model.database_abc import Database
from db_able.client import DBClient


@ABCRestrictions.require('save_params')
class Savable(Database):
    """
    This is a mixin designed to access DB with a standard method action, `save`.
    Supplants the "U" of CRUD.
    :requirement save_params: list or Params; usually load_params + create_params
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        Extend compilation checks to validate defined params.
        """
        super(Savable, cls).__compile__()
        cls._validate_params('save_params')

    def save(self):
        """
        Save `DataObject`. Uses data in instance to update DB. Refer to `self.save_params` to see
        what fields are update-able.
        Expects to call the stored procedure: '%s_save' % cls.__name__, i.e. 'MyDataObject_save'
        Note: Standard Savable implementation uses Loadable internally in the stored procedure.

        Example:
            >>> from db_able import Loadable, Creatable, Savable, Params
            >>> from do_py import R
            >>>
            >>> class A(Creatable, Loadable, Savable):
            >>>     db = 'schema_name'
            >>>     _restrictions = {
            >>>         'id': R.INT,
            >>>         'x': R.INT.with_default(0),
            >>>         'y': R.INT.with_default(1)
            >>>         }
            >>>     load_params = Params('id')  # version=2 allows versioning of the SP, i.e. `A_load_v2`
            >>>     create_params = Params('x', 'y')
            >>>     save_params = Params('id', 'x', 'y')
            >>>
            >>> a = A.create(x=1, y=2)
            >>> loaded = A.load(id=a.id)
            >>> assert a == loaded

        :rtype: bool
        """
        stored_procedure = '%s_save%s' % (self.__class__.__name__, self.save_params.version)
        validated_args = self.kwargs_validator(*self.save_params, **self)
        with DBClient(self.db, stored_procedure, *validated_args, rollback=True) as conn:
            assert conn.data, 'DB response required for `%s`.`%s`.' % (self.db, stored_procedure)
            for row in conn.data:  # Note: this is a weakness. Should always return one and only one row.
                self(data=row)
                return True
