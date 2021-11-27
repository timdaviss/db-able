"""
Mixin to provide a paginated result set.
:date_created: 2021-11-25
"""
from do_py import DataObject, R
from do_py.abc import ABCRestrictions
from do_py.utils import classproperty

from db_able.base_model.database_abc import Database
from db_able.client import DBClient
from db_able.mgmt.const import PaginationType


class Pagination(DataObject):
    _restrictions = {
        'page': R.INT.with_default(1),
        'page_size': R.INT.with_default(10),
        'total': R.INT,
        # 'total_pages': R.INT
        }


class InfiniteScroll(DataObject):
    _restrictions = {
        'after': R.STR,
        'has_more': R.BOOL,
        # 'total': R.INT  # Anti-pattern?
        }


class PaginatedData(DataObject):
    """
    Paginated data structure.
    """
    _restrictions = {
        'data': R.LIST,  # Dynamic ManagedList of Listable DataObjects.
        'pagination': Pagination
        }


class InfiniteScrollData(DataObject):
    """"""
    _restrictions = {
        'data': R.LIST,
        'pagination': InfiniteScroll
        }


@ABCRestrictions.require('list_params', 'pagination_type')
class Listable(Database):
    """"""
    _is_abstract_ = True
    pagination_type = PaginationType.PAGINATION
    pagination_mapping = {
        PaginationType.PAGINATION: PaginatedData,
        PaginationType.INFINITE_SCROLL: InfiniteScrollData
        }

    @classproperty
    def pagination_data_cls_ref(cls):
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

    @classmethod
    def list(cls, **kwargs):
        """
        :param kwargs: refer to `cls.list_params`
        :rtype: PaginatedData or InfiniteScrollData
        """
        stored_procedure = '%s_list%s' % (cls.__name__, cls.list_params.version)
        validated_args = cls.kwargs_validator(*cls.list_params, **kwargs)
        if cls.pagination_type == PaginationType.PAGINATION:
            with DBClient(cls.db, stored_procedure, *validated_args) as conn:
                # TODO: limit handling
                for row in conn.data:
                    return cls(data=row)
        elif cls.pagination_type == PaginationType.INFINITE_SCROLL:
            with DBClient(cls.db, stored_procedure, *validated_args) as conn:
                # TODO: limit handling
                data = []
                for row in conn.data:
                    data.append(cls(data=row))
        else:
            # TODO: Better exception
            raise Exception('Invalid `pagination_type` "%s"' % cls.pagination_type)
        return cls.pagination_data_cls_ref({
            'data': data,
            'pagination': ''  # TODO
            })

    @classmethod
    def yield_all(cls, **kwargs):
        """
        Wrap `cls.list` to auto-paginate and provide a generator of all results.
        :param kwargs: refer to `cls.list_params`
        :rtype: collections.Iterator
        """
