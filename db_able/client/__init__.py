"""
:date_created: 2021-10-23
"""

from do_py import DataObject, R


class DBClient(DataObject):
    _restrictions = {
        'url': R.STR,
        'username': R.STR,
        'password': R.STR
        }

    def __enter__(self):
        """"""
        # Open connection
        # Execute command

    def __exit__(self, exc_type, exc_val, exc_tb):
        """"""
