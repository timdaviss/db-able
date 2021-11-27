"""
Constants for db_able.
:date_created: 2021-11-25
"""


class PaginationType(object):  # Constant):
    """"""
    PAGINATION = 'pagination'
    INFINITE_SCROLL = 'infinite_scroll'
    allowed = [PAGINATION, INFINITE_SCROLL]
