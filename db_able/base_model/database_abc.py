"""
:date_created: 2021-11-03
"""

from do_py.abc import ABCRestrictions

from db_able.base_model.kwargs_validator import KwargsValidator
from db_able.base_model.params import Params


@ABCRestrictions.require('db')
class Database(KwargsValidator):
    """
    Abstracted common required attributes and functionality for all DBAble mixins.
    """
    _is_abstract_ = True

    @classmethod
    def _validate_params(cls, params_attr_name):
        """
        1. Validate that `params_attr_name` is declared as an attribute of the class as a list or `Params`
        2. Transform the params into a `Params` instance.
        3. Validate that all declared parameters have a corresponding restriction
            in `cls._restrictions` or `cls._extra_restrictions`.
        :type params_attr_name: str
        """
        params = getattr(cls, params_attr_name)
        if not isinstance(params, Params):
            assert isinstance(params, list), '%s: Expected "%s" to be a list.' % (cls.__name__, params_attr_name)
            params = Params(*params)
            setattr(cls, params_attr_name, params)
        for k in params:
            assert k in cls._restrictions or k in cls._extra_restrictions, \
                '%s: Missing restrictions for "%s" in %s.' % (cls.__name__, k, params_attr_name)
