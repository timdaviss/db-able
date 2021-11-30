"""
Mixin to provide a paginated result set.
:date_created: 2021-11-25
"""
from typing import Generator, Type, Union

from do_py import DataObject, R
from do_py.abc import ABCRestrictionMeta, ABCRestrictions
from do_py.utils import classproperty

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


class InfiniteScroll(ABCPagination):
    """
    This design suffers from UX issues: Skipping through pages cannot be supported, only the next page is available.
    """
    _restrictions = {
        'after': R.STR,
        'has_more': R.BOOL,
        # 'total': R.INT  # Anti-pattern; InfiniteScroll is intended to be performant with large data sets.
        }
    cursor_key = 'after'


class PaginatedData(DataObject):
    """
    Paginated data structure.
    """
    _restrictions = {
        'data': R.LIST,  # Dynamic ManagedList of Listable DataObjects.
        'pagination': R()  # Pagination or InfiniteScroll DO; validated via `__init__`
        }

    # TODO: Perhaps unnecessary
    def __init__(self, data: Union[dict, None] = None, strict: bool = True):
        """
        Extend initialization to transform self.pagination into the correct DataObject type.
        """
        super(PaginatedData, self).__init__(data=data, strict=strict)
        if type(self.pagination) is dict:
            try:
                self.pagination = Pagination(self.pagination)
            except Exception:
                pass
            try:
                self.pagination = InfiniteScroll(self.pagination)
            except Exception:
                pass
            assert isinstance(self.pagination, ABCPagination)


@ABCRestrictions.require('list_params', 'pagination_type')
class Listable(Database):
    """
    This is a mixin designed to access DB with a standard classmethod action, `list`.
    Supplants bulk "R" of CRUD.
    There are two pagination methods:
        1. Pagination, with Offset/limit paging implemented
        2. Infinite Scroll, with "next page" design using an "after" cursor and "has_more" boolean.
    """
    _is_abstract_ = True
    pagination_type = PaginationType.PAGINATION
    pagination_mapping = {
        PaginationType.PAGINATION: Pagination,
        PaginationType.INFINITE_SCROLL: InfiniteScroll
        }

    @classproperty
    def pagination_data_cls_ref(cls) -> Type[Union[Pagination, InfiniteScroll]]:
        """
        :rtype: ABCRestrictionMeta
        """
        return cls.pagination_mapping[cls.pagination_type]

    @classmethod
    def __compile__(cls):
        """
        Extend compilation checks to validate defined params.
        """
        super(Listable, cls).__compile__()
        cls._validate_params('list_params')
        assert cls.pagination_type in PaginationType.allowed, 'Invalid pagination_type="%s".' % (cls.pagination_type,)
        assert cls.pagination_data_cls_ref, \
            'Failed to resolve to a Pagination class ref for pagination_type="%s".' % (cls.pagination_type,)

    @classmethod
    def list(cls, **kwargs: dict) -> PaginatedData:
        """
        :param kwargs: refer to `cls.list_params`
        :rtype: PaginatedData
        """
        stored_procedure = '%s_list%s' % (cls.__name__, cls.list_params.version)
        validated_args = cls.kwargs_validator(*cls.list_params, **kwargs)

        # Get limit + 1 for Infinite Scroll SP
        # limit = None
        # new_validated_args = []
        # for key, value in validated_args:
        #     if key == 'limit':
        #         new_arg = (key, value + 1)
        #     else:
        #         new_arg = (key, value)
        #     new_validated_args.append(new_arg)

        with DBClient(cls.db, stored_procedure, *validated_args) as conn:
            data = [cls(data=row) for row in conn.data]
            assert conn.next_set(), 'Expected 2 result sets from %s.%s' % (cls.db, stored_procedure)
            pagination = cls.pagination_data_cls_ref(data=conn.data[0])  # TODO: Weakness
        return PaginatedData({
            'data': data,
            'pagination': pagination
            })

    @classmethod
    def yield_all(cls, **kwargs: dict) -> Generator:
        """
        Wrap `cls.list` to auto-paginate and provide a generator of all results.
        :param kwargs: refer to `cls.list_params`
        :rtype: Generator
        """
        cursor_key = cls.pagination_data_cls_ref.cursor_key
        after = kwargs.pop(cursor_key, cls.pagination_data_cls_ref._restrictions[cursor_key].default)  # TODO: Do better
        has_more = True
        while has_more:
            kwargs[cursor_key] = after
            paginated_data = cls.list(**kwargs)
            for datum in paginated_data.data:
                yield datum
            has_more = paginated_data.pagination.has_more
            after = paginated_data.pagination.after
