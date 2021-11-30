"""
Utilities to generate SQL templates to simplify creating Stored Procedures for each mixin implementation.
:date_created: 2021-11-20
"""
from typing import Type, Union

import humps
from do_py import DataObject, R
from do_py.abc import ABCRestrictions

from db_able import Creatable, Deletable, Loadable, Paginated, Savable, Scrollable


@ABCRestrictions.require('BASE_SQL', 'from_db_able')
class ABCSQL(DataObject):
    """
    Abstraction for generating MySQL Stored Procedures from DBAble implementations.
    """
    _is_abstract_ = True

    @classmethod
    def get_table_name(
            cls,
            cls_ref: Type[Union[Loadable, Creatable, Savable, Deletable, Paginated, Scrollable]]
            ) -> str:
        """
        Decamelize the `cls_ref.__name__` to get a default table name.
        """
        table_name = humps.decamelize(cls_ref.__name__)
        if table_name == cls_ref.__name__:
            table_name = cls_ref.__name__.lower()
        return table_name

    def as_sql(self) -> str:
        """
        :rtype: str
        """
        return self.BASE_SQL.format(**self)


class LoadProcedure(ABCSQL):
    """
    SQL generator helper for Loadable.
    """
    BASE_SQL = '''SELECT * FROM `{db}`.`{table_name}` WHERE {where_clause};'''
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'where_clause': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Loadable]):
        """
        :type cls_ref: type[Loadable]
        :rtype: LoadProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'where_clause': ' AND '.join('`{param}` = `_{param}`'.format(param=param) for param in cls_ref.load_params)
            })


class CreateProcedure(ABCSQL):
    """
    SQL generator helper for Creatable.
    Note: Creatable assumes the DBAble is Loadable also.
    """
    BASE_SQL = '''INSERT INTO `{db}`.`{table_name}` ({columns}) VALUES ({values_clause});
    CALL `{db}`.`{cls_name}_load{load_version}`(LAST_INSERT_ID())%s''' % ';'
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'columns': R.STR,
        'values_clause': R.STR,
        'cls_name': R.STR,
        'load_version': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Creatable]):
        """
        :type cls_ref: Creatable
        :rtype: CreateProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'columns': ', '.join('`%s`' % param for param in cls_ref.create_params),
            'values_clause': ', '.join('`_%s`' % param for param in cls_ref.create_params),
            'cls_name': cls_ref.__name__,
            'load_version': cls_ref.load_params.version
            })


class SaveProcedure(ABCSQL):
    """
    SQL generator helper for Savable.
    Note: Savable assumes the DBAble is Loadable also.
    """
    BASE_SQL = '''UPDATE `{db}`.`{table_name}` SET {set_clause} WHERE {where_clause};
    CALL `{db}`.`{cls_name}_load{load_version}`({load_params})%s''' % ';'
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'set_clause': R.STR,
        'where_clause': R.STR,
        'cls_name': R.STR,
        'load_version': R.STR,
        'load_params': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Savable]):
        """
        :type cls_ref: Savable
        :rtype: SaveProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'set_clause': ', '.join(
                '`{param}`=`_{param}`'.format(param=param)
                for param in [p for p in cls_ref.save_params if p not in cls_ref.load_params]
                ),
            'where_clause': ' AND '.join('`{param}` = `_{param}`'.format(param=param) for param in cls_ref.load_params),
            'cls_name': cls_ref.__name__,
            'load_version': cls_ref.load_params.version,
            'load_params': ', '.join('`_%s`' % param for param in cls_ref.load_params)
            })


class DeleteProcedure(ABCSQL):
    """
    SQL generator helper for Deletable.
    """
    BASE_SQL = '''DELETE FROM `{db}`.`{table_name}` WHERE {where_clause};
    SELECT ROW_COUNT() AS `deleted`%s''' % ';'
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'where_clause': R.STR,
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Deletable]):
        """
        :type cls_ref: Type[Deletable]
        :rtype: DeleteProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'where_clause': ' AND '.join(
                '`{param}` = `_{param}`'.format(param=param)
                for param in cls_ref.delete_params
                )
            })


class PaginatedListProcedure(ABCSQL):
    """
    SQL generator helper for Paginated.
    """
    BASE_SQL = '''DECLARE `_offset` INT;
    DECLARE `_page_number` INT;
    SET `_page_number` = IFNULL(`_page`, 1);
    SET `_offset` = (`_page_number` - 1) * `_limit`;

    SELECT * FROM `{db}`.`{table_name}` {opt_where_clause} LIMIT `_limit` OFFSET `_offset`;
    SELECT `_page_number` as `page`, COUNT(*) as `total`, `_limit` as `page_size` FROM `{db}`.`{table_name}`;'''
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'opt_where_clause': R.STR.with_default('')
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Paginated]):
        """
        :type cls_ref: Paginated
        :rtype: PaginatedListProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'opt_where_clause': ' AND '.join(
                '`{param}` = `_{param}`'.format(param=param)
                for param in cls_ref.list_params
                if param not in ['limit', 'page']
                )
            })


class ScrollListProcedure(ABCSQL):
    """
    SQL generator helper for Scrollable.
    Caveats:
        * Where clause will need to be implemented manually for `after` param.
        * Order by clause will need to be implemented manually.
    """
    BASE_SQL = '''SELECT * FROM `{db}`.`{table_name}` WHERE {where_clause} LIMIT `_limit`;'''
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'where_clause': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Scrollable]):
        """
        :type cls_ref: Scrollable
        :rtype: PaginatedListProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'where_clause': ' AND '.join(
                '`{param}` = `_{param}`'.format(param=param)
                for param in cls_ref.list_params
                if param not in ['limit']
                )
            })


procedure_mapping = {
    'load': LoadProcedure,
    'create': CreateProcedure,
    'save': SaveProcedure,
    'delete': DeleteProcedure,
    'paginated': PaginatedListProcedure,
    'scrollable': ScrollListProcedure
    }


class CoreStoredProcedure(ABCSQL):
    """
    :restriction params: Should conform to ``` IN `_variable` TYPE ``` syntax.
    :restriction procedure: The contents of the SP's execution.
    """
    BASE_SQL = '''
USE `{db}`;
DROP PROCEDURE IF EXISTS `{db}`.`{cls_name}_{method}{version}`;

DELIMITER $$
CREATE
    DEFINER = `root`@`localhost` PROCEDURE `{db}`.`{cls_name}_{method}{version}`
(
{params}
)
BEGIN

    {procedure}

END;
$$
DELIMITER ;
'''
    _restrictions = {
        'db': R.STR,
        'cls_name': R.STR,
        'method': R('create', 'load', 'save', 'delete', 'list'),
        'version': R.STR,
        'params': R.STR,
        'procedure': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref: Type[Union[Loadable, Creatable, Savable, Deletable, Paginated, Scrollable]], method,
                     procedure_key=None):
        """
        Creates string representation of SQL file to create a Stored Procedure for given method.
        :type cls_ref: Creatable or Loadable or Savable or Deletable
        :type method: str
        :type procedure_key: str or None
        :rtype: CoreStoredProcedure
        """
        params_attr = getattr(cls_ref, '%s_params' % method)
        sql_type_mapping = {
            str(R.INT[0]): 'INT',
            str(R.NULL_INT[0]): 'INT',
            str(R.STR[0]): 'VARCHAR(255)',
            str(R.NULL_STR[0]): 'VARCHAR(255)',
            str(R.DATETIME[0]): 'TIMESTAMP',
            str(R.NULL_DATETIME[0]): 'TIMESTAMP',
            str(R.FLOAT[0]): 'FLOAT',
            str(R.NULL_FLOAT[0]): 'FLOAT',
            }
        return cls({
            'db': cls_ref.db,
            'cls_name': cls_ref.__name__,
            'method': method,
            'version': params_attr.version,
            'params': ',\n'.join(
                '    IN `_%s` %s' % (
                    param,
                    sql_type_mapping.get(
                        str(
                            cls_ref._restrictions.get(
                                param,
                                (cls_ref._extra_restrictions or {}).get(param)
                                )[0]
                            )
                        )
                    )
                for param in params_attr
                ),
            'procedure': procedure_mapping[procedure_key or method].from_db_able(cls_ref).as_sql()
            })


def print_all_sps(cls_ref):
    """
    :type cls_ref: Loadable or Creatable # or Savable or Deletable
    """
    if Loadable in cls_ref.mro():
        print(CoreStoredProcedure.from_db_able(cls_ref, 'load').as_sql())
    if Creatable in cls_ref.mro():
        print(CoreStoredProcedure.from_db_able(cls_ref, 'create').as_sql())
    if Savable in cls_ref.mro():
        print(CoreStoredProcedure.from_db_able(cls_ref, 'save').as_sql())
    if Deletable in cls_ref.mro():
        print(CoreStoredProcedure.from_db_able(cls_ref, 'delete').as_sql())
    if Paginated in cls_ref.mro():
        print(CoreStoredProcedure.from_db_able(cls_ref, 'list', procedure_key='paginated').as_sql())
    if Scrollable in cls_ref.mro():
        print(CoreStoredProcedure.from_db_able(cls_ref, 'list', procedure_key='scrollable').as_sql())
