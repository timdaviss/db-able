"""
:date_created: 2021-10-30
"""
from datetime import datetime
from typing import Type, Union

import pytest

from examples.a import A
from examples.b import B
from examples.c import C


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


@pytest.mark.parametrize('cls_ref', [B, C])
def test_listable(cls_ref: Type[Union[B, C]]):
    """
    Integration test for `Scrollable` (`B`) and `Paginated` (`C`) implementations.
    """
    data = list(cls_ref.yield_all(limit=5))
    assert len(data) == 11  # 11 seed_data points in SQL setup. Ref: tests/sql/testing/seed_data/*.sql
