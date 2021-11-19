"""
:date_created: 2021-11-18
"""

from do_py.abc import ABCRestrictions

from db_able.base_model.database_abc import Database
from db_able.client import DBClient


@ABCRestrictions.require('delete_params')
class Deletable(Database):
    """
    This is a mixin designed to delete a row in DB with a standard method action, `delete`.
    Supplants the "D" of CRUD.
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        Extend compilation checks to validate defined params.
        """
        super(Deletable, cls).__compile__()
        cls._validate_params('delete_params')

    def delete(self):
        """
        Delete `DataObject` row from DB.
        Expects to call the stored procedure: ‘%s_delete’ % cls.__name__, i.e. ‘MyDataObject_delete’

        Example:
            >>> from db_able import Deletable, Loadable, Params
            >>> from do_py import R
            >>>
            >>> class A(Loadable, Deletable):
            >>>     db = 'schema_name'
            >>>     _restrictions = {
            >>>         'id': R.INT,
            >>>         'x': R.INT.with_default(0),
            >>>         'y': R.INT.with_default(1)
            >>>         }
            >>>     load_params = Params('id')  # version=2 allows versioning of the SP, i.e. `A_load_v2`
            >>>     del_params = Params('id')
            >>>
            >>> a = A.load(id=2)
            >>> a.delete()
            >>> a = A.load(id=2)  # None

        :rtype: bool
        """
        stored_procedure = '%s_delete%s' % (self.__class__.__name__, self.delete_params.version)
        validated_args = self.kwargs_validator(*self.delete_params, **self)
        with DBClient(self.db, stored_procedure, *validated_args) as conn:
            assert conn.data, 'Expected a truthy response for `%s`.`%s`' % (self.db, stored_procedure)
            assert conn.data[0]['deleted'], 'No data deleted.'
            self(None, strict=False)  # Deletes data from memory on success
            return True
