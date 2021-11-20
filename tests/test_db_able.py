"""
:date_created: 2021-10-30
"""
from datetime import datetime

from examples.a import A


def test_db_able():
    """
    This is an integration test. It covers end-to-end functionality of the db_able package.
    """
    # Create
    created = A.create(
        string='Hello world. 😇',
        json={'x': 1, 'y': 123},
        int=12,
        float=12.34,
        datetime=datetime.utcnow()
        )
    loaded = A.load(id=created.id)
    assert loaded == created
    # Update
    created.int = None
    created.float = None
    created.datetime = datetime(2021, 11, 18)
    assert created.save()
    assert loaded != created
    loaded = A.load(id=created.id)
    assert loaded == created
    # Delete
    created.delete()
    assert created != loaded
    loaded = A.load(id=loaded.id)
    assert not loaded
