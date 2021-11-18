"""
:date_created: 2021-11-03
"""

from do_py import DataObject
from do_py.data_object import Restriction
from do_py.exceptions import RestrictionError, DataObjectError


class KwargsValidator(DataObject):
    """
    This mixin injects the `cls.kwargs_validator` utility classmethod into the scope of the inheriting class.
    The `cls.kwargs_validator` utility is designed to be implemented as a method for data validation prior to
    executing "expensive" logic, i.e. connecting to DB.
    The intent is to fail as early as possible -- if we can fail in Python before hitting the DB, that is good.
    """
    _is_abstract_ = True
    _extra_restrictions = frozenset({})

    @classmethod
    def __compile__(cls):
        """
        `cls._extra_restrictions` need to be transformed accordingly into Restrictions structure.
        """
        super(KwargsValidator, cls).__compile__()
        if isinstance(cls._extra_restrictions, dict):
            for k in cls._extra_restrictions:
                try:
                    cls._extra_restrictions[k] = Restriction.legacy(cls._extra_restrictions[k])
                except RestrictionError as re:
                    raise DataObjectError.from_restriction_error(k, cls, re)

    @classmethod
    def kwargs_validator(cls, *signature, **kwargs):
        """
        Kwargs validator. Use `cls._restrictions` to validate the given `kwargs` values and inject defaults.
        The design is to error out as soon as possible, especially before opening a DB connection.
        :param signature: tuple of argument values. Ordered by `%s_params` attribute
        :param kwargs: keyword arguments matching `signature` to be validated by `cls._restrictions`
        :return: list of validated kwargs
        :rtype: list of tuple
        """
        validated_vals = []
        for k in signature:
            try:
                if k in cls._restrictions:
                    validated_vals.append(
                        (k, cls._restrictions[k](kwargs.get(k, cls._restrictions[k].default)))
                        )
                elif k in cls._extra_restrictions:
                    validated_vals.append(
                        (k, cls._extra_restrictions[k](kwargs.get(k, cls._extra_restrictions[k].default)))
                        )
                else:
                    raise KeyError('Restrictions required for "%s" in %s.' % (k, cls.__name__))
            except RestrictionError as re:
                raise DataObjectError.from_restriction_error(k, cls, re)
        return validated_vals
