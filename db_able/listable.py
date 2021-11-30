"""
Mixins to provide a paginated result set.
:date_created: 2021-11-25
"""
from typing import Generator, Union

from do_py import DataObject, R
from do_py.abc import ABCRestrictions
from do_py.data_object.validator import Validator

from db_able.base_model.database_abc import Database
from db_able.client import DBClient
from db_able.mgmt.const import PaginationType


@ABCRestrictions.require('cursor_key')
class ABCPagination(DataObject):
    """
    Interface for nested pagination structures for use with PaginatedData.
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        Extend compile-time checks to validate `cls.cursor_key` value in `cls._restrictions`.
        """
        super(ABCPagination, cls).__compile__()
        assert cls.cursor_key in cls._restrictions, \
            '{cls_name}.cursor_key="{cursor_key}" must be in {cls_name}._restrictions.'.format(
                cls_name=cls.__name__,
                cursor_key=cls.cursor_key
                )
        assert 'has_more' in cls._restrictions or hasattr(cls, 'has_more'), \
            '"has_more" must be defined in {cls_name}\'s restrictions or as an attribute'.format(
                cls_name=cls.__name__
                )
        assert 'after' in cls._restrictions or hasattr(cls, 'after'), \
            '"after" must be defined in {cls_name}\'s restrictions or as an attribute'.format(
                cls_name=cls.__name__
                )


class Pagination(ABCPagination):
    """
    This design suffers from performance issues on large data sets: in MySQL, OFFSET walks through each row it skips.
    """
    _restrictions = {
        'page': R.INT.with_default(1),
        'page_size': R.INT.with_default(10),
        'total': R.INT,
        }
    cursor_key = 'page'

    @property
    def has_more(self) -> bool:
        """
        :rtype: bool
        """
        return self.page * self.page_size < self.total

    @property
    def after(self) -> int:
        """
        :rtype: int
        """
        return self.page + 1


class InfiniteScroll(ABCPagination, Validator):
    """
    This design suffers from UX issues: Skipping through pages cannot be supported, only the next page is available.
    """
    _restrictions = {
        'after': R(),  # Note: Does not handle encryption/decryption for external exposure.
        'has_more': R.BOOL,
        # 'total': R.INT  # Anti-pattern; InfiniteScroll is intended to be performant with large data sets.
        }
    cursor_key = 'after'

    def _validate(self):
        """
        Validate that `self.after` is populated if `self.has_more` is True.
        """
        if self.has_more:
            assert self.after is not None, 'Expected "after" to be populated when "has_more" is True.'


class PaginatedData(Validator):
    """
    Paginated data structure.
    """
    _restrictions = {
        'data': R.LIST,  # _Listable DataObjects.
        'pagination': R()  # Pagination or InfiniteScroll DO; validated via `_validate`
        }

    def _validate(self):
        """
        Validate `self.data` elements are `_Listable` implementation instances.
        Validate `self.pagination` is a `ABCPagination` implementation instance.
        """
        assert all(isinstance(datum, _Listable) for datum in self.data), \
            '`self.data` must be comprised of _Listable descendents.'
        assert isinstance(self.pagination, ABCPagination), \
            '`self.pagination` type "%s" must be a descendent of `ABCPagination`.' % type(self.pagination)


@ABCRestrictions.require('list_params', 'pagination_type', 'pagination_data_cls_ref')
class _Listable(Database):
    """
    This is an abstraction for `Paginated` and `Scrollable` mixins, designed to access DB with a
    standard classmethod action, `list`.
    Supplants bulk "R" of CRUD.
    There are two pagination designs:
        1. Pagination, with Offset/limit paging implemented
        2. Infinite Scroll, with "next page" design using an "after" cursor and "has_more" boolean.
    """
    _is_abstract_ = True

    @classmethod
    def __compile__(cls):
        """
        Extend compilation checks to validate defined params.
        """
        super(_Listable, cls).__compile__()
        cls._validate_params('list_params')
        assert cls.pagination_type in PaginationType.allowed, 'Invalid pagination_type="%s".' % (cls.pagination_type,)
        assert ABCPagination in cls.pagination_data_cls_ref.mro(), \
            'Invalid pagination_data_cls_ref="%s".' % (cls.pagination_data_cls_ref,)

    @classmethod
    def yield_all(cls, **kwargs) -> Generator:
        """
        Wrap `cls.list` to auto-paginate and provide a generator of all results.
        :param kwargs: refer to `cls.list_params`
        :rtype: Generator
        """
        cursor_key = cls.pagination_data_cls_ref.cursor_key
        after = kwargs.pop(cursor_key, cls.pagination_data_cls_ref._restrictions[cursor_key].default)
        has_more = True
        while has_more:
            kwargs[cursor_key] = after
            paginated_data = cls.list(**kwargs)
            for datum in paginated_data.data:
                yield datum
            has_more = paginated_data.pagination.has_more
            after = paginated_data.pagination.after


class Paginated(_Listable):
    """
    Mixin to support standard pagination design, with offset/limit paging implementation.
    """
    _is_abstract_ = True
    pagination_type = PaginationType.PAGINATION
    pagination_data_cls_ref = Pagination

    @classmethod
    def __compile__(cls):
        """
        Extend compile-time checks to validate implementation does not use both Scrollable and Paginated.
        """
        super(Paginated, cls).__compile__()
        assert Scrollable not in cls.mro(), '"Scrollable" and "Paginated" mixins are mutually exclusive.'

    @classmethod
    def list(cls, **kwargs) -> PaginatedData:
        """
        List multiple `DataObject` in `PaginatedData` structure. Use `cls.list_params` as kwargs reference.
        Expects to call the stored procedure: '%s_list' % cls.__name__, i.e. 'MyDataObject_list'

        Example:
            >>> from db_able import Paginated, Params
            >>> from do_py import R
            >>>
            >>> class A(Paginated):
            >>>     db = 'schema_name'
            >>>     _restrictions = {
            >>>         'id': R.INT,
            >>>         'x': R.INT.with_default(0),
            >>>         'y': R.INT.with_default(1)
            >>>         }
            >>>     _extra_restrictions = {
            >>>         'limit': R.INT.with_default(10),
            >>>         'page': R.INT.with_default(1)
            >>>         }
            >>>     list_params = Params('limit', 'page')  # version=2 allows versioning of the SP, i.e. `A_list_v2`
            >>>
            >>> a = A.list(limit=10)
            >>> list(A.yield_all(limit=10))
        :param kwargs: refer to `cls.list_params`
        :rtype: PaginatedData
        """
        stored_procedure = '%s_list%s' % (cls.__name__, cls.list_params.version)
        validated_args = cls.kwargs_validator(*cls.list_params, **kwargs)
        with DBClient(cls.db, stored_procedure, *validated_args) as conn:
            data = [cls(data=row) for row in conn.data]
            assert conn.next_set(), 'Expected 2 result sets from %s.%s' % (cls.db, stored_procedure)
            assert conn.data, 'No pagination data found in second result set from %s.%s' % (cls.db, stored_procedure)
            assert len(conn.data) == 1, \
                'Expected one row from pagination data result set from %s.%s' % (cls.db, stored_procedure)
            pagination = cls.pagination_data_cls_ref(data=conn.data[0])
        return PaginatedData({
            'data': data,
            'pagination': pagination
            })


@ABCRestrictions.require('to_after')
class Scrollable(_Listable):
    """
    Mixin to support Infinite Scroll pagination design.
    :attribute to_after: method to convert self into the appropriate cursor value for `list` stored procedure.
    """
    _is_abstract_ = True
    pagination_type = PaginationType.INFINITE_SCROLL
    pagination_data_cls_ref = InfiniteScroll

    @classmethod
    def __compile__(cls):
        """
        Extend compile-time checks to:
            1. Validate implementation does not use both Scrollable and Paginated.
            2. Validate limit restriction is defined.
            3. Validate limit is defined in `list_params`.
        """
        super(Scrollable, cls).__compile__()
        assert Paginated not in cls.mro(), '"Scrollable" and "Paginated" mixins are mutually exclusive.'
        assert 'limit' in cls._restrictions or 'limit' in cls._extra_restrictions, \
            '"limit" restriction required for %s.' % cls.__name__
        assert 'limit' in cls.list_params, '"limit" param required for %s.list_params' % cls.__name__

    @classmethod
    def list(cls, **kwargs) -> PaginatedData:
        """
        List multiple `DataObject` in `PaginatedData` structure. Use `cls.list_params` as kwargs reference.
        Expects to call the stored procedure: '%s_list' % cls.__name__, i.e. 'MyDataObject_list'

        Example:
            >>> from db_able import Scrollable, Params
            >>> from do_py import R
            >>>
            >>> class A(Scrollable):
            >>>     db = 'schema_name'
            >>>     _restrictions = {
            >>>         'id': R.INT,
            >>>         'x': R.INT.with_default(0),
            >>>         'y': R.INT.with_default(1)
            >>>         }
            >>>     _extra_restrictions = {
            >>>         'limit': R.INT.with_default(10),
            >>>         'after': R.NULL_STR
            >>>         }
            >>>     pagination_type = PaginationType.INFINITE_SCROLL
            >>>     list_params = Params('limit', 'after')  # version=2 allows versioning of the SP, i.e. `A_list_v2`
            >>>
            >>> a = A.list(limit=10)
            >>> list(A.yield_all(limit=10))
        :param kwargs: refer to `cls.list_params`
        :rtype: PaginatedData
        """
        stored_procedure = '%s_list%s' % (cls.__name__, cls.list_params.version)
        validated_args = cls.kwargs_validator(*cls.list_params, **kwargs)

        # Get limit + 1 to fetch one additional row for `has_more` business logic implementation.
        # Peeling out from validated_args is required to use restriction-defined default limit value.
        limit = None
        new_validated_args = []
        for key, value in validated_args:
            if key == 'limit':
                new_arg = (key, value + 1)
                limit = value
            else:
                new_arg = (key, value)
            new_validated_args.append(new_arg)

        with DBClient(cls.db, stored_procedure, *new_validated_args) as conn:
            pagination = {
                'has_more': len(conn.data) > limit,
                'after': None
                }
            data = []
            for row in conn.data:
                if len(data) < limit:
                    obj = cls(data=row)
                    data.append(obj)
                    pagination['after'] = obj.to_after()
                else:
                    break
        return PaginatedData({
            'data': data,
            'pagination': cls.pagination_data_cls_ref(pagination)
            })
