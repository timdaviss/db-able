"""
:date_created: 2021-11-04
"""


class Params(list):
    """
    Supports versioning for SPs by extending the params with a version kwarg

    Example:
        class A(Loadable):
            _restrictions = {
                'id': R.INT,
                'x': R.INT,
                }
            load_params = Params('id', version=2)
    """

    def __init__(self, *args, **kwargs):
        """
        :keyword version: Versioning for SP
        :type version: int
        """
        super(Params, self).__init__()
        self.extend(args)
        self._version = kwargs.get('version')

    @property
    def version(self):
        """
        :rtype: str
        """
        return '_v%s' % self._version if self._version is not None else ''
