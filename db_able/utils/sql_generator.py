"""
Utilities to generate SQL templates to simplify creating Stored Procedures for each mixin implementation.
:date_created: 2021-11-20
"""

import humps
from do_py import DataObject, R
from do_py.abc import ABCRestrictions
from db_able import Loadable, Creatable, Savable, Deletable


@ABCRestrictions.require('BASE_SQL', 'from_db_able')
class ABCSQL(DataObject):
    """
    Abstraction for generating MySQL Stored Procedures from DBAble implementations.
    """
    _is_abstract_ = True

    @classmethod
    def get_table_name(cls, cls_ref):
        """
        Decamelize the `cls_ref.__name__` to get a default table name.
        :type cls_ref: type
        :rtype: str
        """
        table_name = humps.decamelize(cls_ref.__name__)
        if table_name == cls_ref.__name__:
            table_name = cls_ref.__name__.lower()
        return table_name

    def as_sql(self):
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
    def from_db_able(cls, cls_ref):
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
    def from_db_able(cls, cls_ref):
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
    def from_db_able(cls, cls_ref):
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
    Note: Savable assumes the DBAble is Loadable also.
    """
    BASE_SQL = '''DELETE FROM `{db}`.`{table_name}` WHERE {where_clause};
    SELECT ROW_COUNT() AS `deleted`%s''' % ';'
    _restrictions = {
        'db': R.STR,
        'table_name': R.STR,
        'where_clause': R.STR,
        }

    @classmethod
    def from_db_able(cls, cls_ref):
        """
        :type cls_ref: Deletable
        :rtype: SaveProcedure
        """
        return cls({
            'db': cls_ref.db,
            'table_name': cls.get_table_name(cls_ref),
            'where_clause': ' AND '.join(
                '`{param}` = `_{param}`'.format(param=param)
                for param in cls_ref.delete_params
                )
            })


procedure_mapping = {
    'load': LoadProcedure,
    'create': CreateProcedure,
    'save': SaveProcedure,
    'delete': DeleteProcedure
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
        'method': R('create', 'load', 'save', 'delete'),
        'version': R.STR,
        'params': R.STR,
        'procedure': R.STR
        }

    @classmethod
    def from_db_able(cls, cls_ref, method):
        """
        Creates string representation of SQL file to create a Stored Procedure for given method.
        :type cls_ref: Creatable or Loadable or Savable or Deletable
        :type method: str
        :rtype: CoreStoredProcedure
        """
        params_attr = getattr(cls_ref, '%s_params' % method)
        sql_type_mapping = {
            str(R.INT): 'INT',
            str(R.NULL_INT): 'INT',
            str(R.STR): 'VARCHAR(255)',
            str(R.NULL_STR): 'VARCHAR(255)',
            str(R.DATETIME): 'TIMESTAMP',
            str(R.NULL_DATETIME): 'TIMESTAMP',
            str(R.FLOAT): 'FLOAT',
            str(R.NULL_FLOAT): 'FLOAT',
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
                                )
                            )
                        )
                    )
                for param in params_attr
                ),
            'procedure': procedure_mapping[method].from_db_able(cls_ref).as_sql()
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

