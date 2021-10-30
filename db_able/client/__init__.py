"""
:date_created: 2021-10-23
"""

from do_py.utils import cached_property


class DBClient(object):

    def __init__(self, database, stored_procedure, *args, **kwargs):
        """"""
        self.database = database
        self.stored_procedure = stored_procedure
        self.args = args
        self.kwargs = kwargs

    @cached_property
    def sql(self):
        """
        
        :rtype: str
        """
        return '`{database}`.`{stored_procedure}`({args});'.format(
            database=self.database,
            stored_procedure=self.stored_procedure,
            args=','.join(self.args)
            )

    def open_connection(self):
        """"""


    def __enter__(self):
        """"""
        # Open connection
        # Execute command

    def __exit__(self, exc_type, exc_val, exc_tb):
        """"""
