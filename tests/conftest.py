"""
:date_created: 2021-11-20
"""
import pytest

from db_able import client


@pytest.fixture(scope='session', autouse=True)
def set_conn_str():
    """
    Set the connection string for DBAble client for use in UTs.
    """
    client.CONN_STR = 'mysql+pymysql://root:root@localhost'
