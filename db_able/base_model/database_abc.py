"""
:date_created: 2021-11-03
"""

from do_py.abc import ABCRestrictions, SystemMessages
from do_py.utils import classproperty

from db_able import Params
from db_able.base_model.kwargs_validator import KwargsValidator


@ABCRestrictions.require('db', 'mixin_name', unique=['mixin_name'])
class Database(KwargsValidator):
    """
    Abstracted common required attributes and functionality for all DBAble mixins.
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        1. Validate that 'params_attr' is declared as an attribute of the class as a list or `Params`
        2. Transform the params into a `Params` instance.
        3. Validate that all declared parameters have a corresponding restriction
            in `cls._restrictions` or `cls._extra_restrictions`.
        """
        super(Database, cls).__compile__()
        assert hasattr(cls, cls.params_attr_name), \
            SystemMessages.required_argument % (cls.params_attr_name, cls.__name__)
        if not isinstance(cls.params, Params):
            assert isinstance(cls.params, list), '%s: Expected "%s" to be a list.' % (cls.__name__, cls.params)
            params = Params(*cls.params)
            setattr(cls, cls.params_attr_name, params)
        for k in cls.params:
            assert k in cls._restrictions or k in cls._extra_restrictions, \
                '%s: Missing restrictions for "%s" in %s.' % (cls.__name__, k, cls.params_attr_name)

    @classproperty
    def params_attr_name(cls):
        """
        :rtype: str
        """
        return '%s_params' % cls.mixin_name

    @classproperty
    def params(cls):
        """
        :rtype: Params
        """
        return getattr(cls, cls.params_attr_name)

    @classproperty
    def stored_procedure(cls):
        """
        :rtype: str
        """
        return '%s_%s%s' % (cls.__name__, cls.mixin_name, cls.params.version)
